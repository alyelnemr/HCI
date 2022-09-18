
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict
import re

INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    treating_physician_ids = fields.Many2many('medical.physician',string='Treating Physicians',related='patient_id.treating_physician_ids', required=False)

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute('select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal), sum(line.quantity) * max(line.price_unit) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.sorting_rank, categ.name order by categ.sorting_rank' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group

    @api.model
    def _search_default_journal(self, journal_types):
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            if self._context.get('active_model') == 'sale.order':
                sale_order = self.env['sale.order'].browse(self._context.get('active_id'))
                if sale_order.patient_id and sale_order.patient_id.is_insurance:
                    domain_insurance = [('company_id', '=', company_id), ('type', 'in', journal_types), ('is_insurance_journal', '=', True)]
                    journal = self.env['account.journal'].search(domain_insurance, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        if not self.date or not self.journal_id:
            return "WHERE FALSE", {}
        where_string = "WHERE journal_id = %(journal_id)s AND name != '/'"
        param = {'journal_id': self.journal_id.id}

        if not relaxed:
            domain = [('journal_id', '=', self.journal_id.id), ('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', '', False))]
            if self.journal_id.refund_sequence:
                refund_types = ('out_refund', 'in_refund')
                domain += [('move_type', 'in' if self.move_type in refund_types else 'not in', refund_types)]
            reference_move_name = self.search(domain + [('date', '<=', self.date)], order='date desc', limit=1).name
            if not reference_move_name:
                reference_move_name = self.search(domain, order='date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_move_name)
            if sequence_number_reset == 'year':
                where_string += " AND date_trunc('year', date::timestamp without time zone) = date_trunc('year', %(date)s) "
                param['date'] = self.date
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
            elif sequence_number_reset == 'month':
                where_string += " AND date_trunc('month', date::timestamp without time zone) = date_trunc('month', %(date)s) "
                param['date'] = self.date
            else:
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

            if param.get('anti_regex') and not self.journal_id.sequence_override_regex:
                where_string += " AND sequence_prefix !~ %(anti_regex)s "

        if self.journal_id.refund_sequence:
            if self.move_type in ('out_refund', 'in_refund'):
                where_string += " AND move_type IN ('out_refund', 'in_refund') "
            else:
                where_string += " AND move_type NOT IN ('out_refund', 'in_refund') "

        return where_string, param

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        def journal_key(move):
            return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

        def date_key(move):
            return (move.date.year, move.date.month)

        grouped = defaultdict(  # key: journal_id, move_type
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    'records': self.env['account.move'],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
        highest_name = self[0]._get_last_sequence(lock=False) if self else False

        # Group the moves by journal and month
        for move in self:
            if not highest_name and move == self[0] and not move.posted_before and move.date:
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            elif (move.name and move.name != '/') or move.state != 'posted':
                try:
                    if not move.posted_before:
                        move._constrains_date_sequence()
                    # Has already a name or is not posted, we don't add to a batch
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group['records']:
                # Compute all the values needed to sequence this whole group
                move._set_next_sequence()
                group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
                group['reset'] = move._deduce_sequence_number_reset(move.name)
            group['records'] += move

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for journal_group in grouped.values():
            journal_group_changed = True
            for date_group in journal_group.values():
                if (
                    journal_group_changed
                    or final_batches[-1]['format'] != date_group['format']
                    or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                ):
                    final_batches += [date_group]
                    journal_group_changed = False
                elif date_group['reset'] == 'never':
                    final_batches[-1]['records'] += date_group['records']
                elif (
                    date_group['reset'] == 'year'
                    and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                ):
                    final_batches[-1]['records'] += date_group['records']
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for move in batch['records']:
                move.name = batch['format'].format(**batch['format_values'])
                batch['format_values']['seq'] += 1
            batch['records']._compute_split_sequence()

        self.filtered(lambda m: not m.name).name = '/'

    def action_post(self):
        self._post(soft=False)
        return False

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            future_moves.auto_post = True
            for move in future_moves:
                msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
        if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_("You don't have the access rights to post an invoice."))
        for move in to_post:
            if move.partner_bank_id and not move.partner_bank_id.active:
                raise UserError(_("The recipient bank account link to this invoice is archived.\nSo you cannot confirm the invoice."))
            if move.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
            if not move.line_ids.filtered(lambda line: not line.display_type):
                raise UserError(_('You need to add a line before posting.'))
            if move.auto_post and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s", date_msg))

            if not move.partner_id:
                if move.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif move.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
                raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if not move.invoice_date:
                if move.is_sale_document(include_receipts=True):
                    move.invoice_date = fields.Date.context_today(self)
                    move.with_context(check_move_validity=False)._onchange_invoice_date()
                elif move.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

            # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tax_tag_ids):
                move.date = move._get_accounting_date(move.invoice_date or move.date, True)
                move.with_context(check_move_validity=False)._onchange_currency()


        for move in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = move.is_invoice() and move.line_ids.filtered(lambda aml: aml.partner_id != move.commercial_partner_id and not aml.display_type)
            if wrong_lines:
                wrong_lines.partner_id = move.commercial_partner_id.id

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.mapped('line_ids').create_analytic_lines()
        to_post.write({
            'state': 'posted',
            'posted_before': True,
        })

        for move in to_post:
            move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

            # Compute 'ref' for 'out_invoice'.
            if move._auto_compute_invoice_reference():
                to_write = {
                    'payment_reference': move._get_invoice_computed_reference(),
                    'line_ids': []
                }
                for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                    to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
                move.write(to_write)

        for move in to_post:
            if move.is_sale_document() \
                    and move.journal_id.sale_activity_type_id \
                    and (move.journal_id.sale_activity_user_id or move.invoice_user_id).id not in (self.env.ref('base.user_root').id, False):
                move.activity_schedule(
                    date_deadline=min((date for date in move.line_ids.mapped('date_maturity') if date), default=move.date),
                    activity_type_id=move.journal_id.sale_activity_type_id.id,
                    summary=move.journal_id.sale_activity_note,
                    user_id=move.journal_id.sale_activity_user_id.id or move.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for move in to_post:
            if move.is_sale_document():
                customer_count[move.partner_id] += 1
            elif move.is_purchase_document():
                supplier_count[move.partner_id] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices in amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        ).action_invoice_paid()

        # Force balance check since nothing prevents another module to create an incorrect entry.
        # This is performed at the very end to avoid flushing fields before the whole processing.
        to_post._check_balanced()
        return to_post
