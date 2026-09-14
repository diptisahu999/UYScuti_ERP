from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _format_indian_number(self, value):
        if not value:
            return value
        cleaned = "".join(filter(str.isdigit, str(value)))
        if len(cleaned) == 10:
            return f"+91{cleaned}"
        if len(cleaned) == 11 and cleaned.startswith('0'):
            return f"+91{cleaned[1:]}"
        if len(cleaned) == 12 and cleaned.startswith('91') and not str(value).startswith('+'):
            return f"+{cleaned}"
        return value

    @api.onchange('phone')
    def _on_change_phone(self):
        if self.phone:
            self.phone = self._format_indian_number(self.phone)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'phone' in vals:
                vals['phone'] = self._format_indian_number(vals['phone'])
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        if 'phone' in vals:
            vals['phone'] = self._format_indian_number(vals['phone'])
        return super(ResPartner, self).write(vals)
