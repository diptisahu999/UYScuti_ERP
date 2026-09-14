from odoo import models, fields, api

class AccountAccount(models.Model):
    _inherit = 'account.account'

    opening_debit = fields.Float()
    opening_credit = fields.Float()

    def write(self, vals):
        res = super().write(vals)

        opening_account = self.env['account.account'].search(
            [('name', '=', 'Opening Balance Equity')], limit=1
        )

        journal = self.env['account.journal'].search(
            [('type', '=', 'general')], limit=1
        )

        for record in self:
            debit = vals.get('opening_debit', 0.0)
            credit = vals.get('opening_credit', 0.0)

            if debit or credit:
                move = self.env['account.move'].create({
                    'date': '2026-03-31',
                    'journal_id': journal.id,
                    'line_ids': [
                        (0, 0, {
                            'account_id': record.id,
                            'debit': debit,
                            'credit': credit,
                        }),
                        (0, 0, {
                            'account_id': opening_account.id,
                            'debit': credit,
                            'credit': debit,
                        }),
                    ]
                })
                move.action_post()

        return res