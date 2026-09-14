from odoo import models, fields, api
from odoo.exceptions import UserError


class OpeningBalanceWizard(models.TransientModel):
    _name = 'opening.balance.wizard'
    _description = 'Opening Balance Wizard'

    date = fields.Date(required=True, default=fields.Date.today)
    amount = fields.Float(required=True)

    partner_id = fields.Many2one('res.partner')
    account_id = fields.Many2one('account.account')

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([
            ('type', '=', 'general')
        ], limit=1)

        if not journal:
            raise UserError("No Miscellaneous Journal found. Please create one.")

        return journal
    

    def action_create_entry(self):
        journal = self._get_default_journal()

        if not self.amount:
            raise UserError("Amount is required")

        account = self.account_id

        # 🔥 RULE 1: Partner → FORCE receivable/payable
        if self.partner_id:
            if self.partner_id.customer_rank > 0:
                account = self.partner_id.property_account_receivable_id
            elif self.partner_id.supplier_rank > 0:
                account = self.partner_id.property_account_payable_id
            else:
                raise UserError("Selected partner is neither Customer nor Vendor.")

            # 🚫 Prevent wrong manual account
            if self.account_id and self.account_id != account:
                raise UserError(
                    "Do not select Account when Partner is set.\n"
                    "System will automatically use Receivable/Payable."
                )

        # 🔥 RULE 2: No Partner → Account required
        if not self.partner_id:
            if not account:
                raise UserError("Account is required when no partner is selected.")

            # 🚫 Prevent using receivable/payable without partner
            if account.account_type in ['asset_receivable', 'liability_payable']:
                raise UserError(
                    "Receivable/Payable account requires a Partner."
                )

        # 🔥 STEP: Equity account
        equity_account = self.env['account.account'].search([
            ('account_type', '=', 'equity')
        ], limit=1)

        if not equity_account:
            equity_account = self.env['account.account'].create({
                'name': 'Opening Balance Equity',
                'account_type': 'equity',
                'code': '999999',
            })

        # 🔥 STEP: Debit / Credit logic
        if self.partner_id:
            # Customer → Debit
            if self.partner_id.customer_rank > 0:
                debit = self.amount
                credit = 0.0
            else:
                # Vendor → Credit
                debit = 0.0
                credit = self.amount
        else:
            # Company own account (Bank/Cash/etc.)
            debit = self.amount if self.amount > 0 else 0.0
            credit = -self.amount if self.amount < 0 else 0.0

        move_lines = [
            (0, 0, {
                'account_id': account.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'debit': debit,
                'credit': credit,
                'name': 'Opening Balance',
            }),
            (0, 0, {
                'account_id': equity_account.id,
                'debit': credit,
                'credit': debit,
                'name': 'Opening Balance Equity',
            })
        ]

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'date': self.date,
            'journal_id': journal.id,
            'line_ids': move_lines,
            'ref': 'Opening Balance',
        })

        move.action_post()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
        }
    


    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.account_id = False