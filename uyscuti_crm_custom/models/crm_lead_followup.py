# models/crm_lead_followup.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

class CrmLeadPhoto(models.Model):
    _name = 'crm.lead.photo'
    _description = 'CRM Lead Photo'

    lead_id = fields.Many2one('crm.lead', ondelete='cascade')
    photo = fields.Image(string='Photo', required=True)
    name = fields.Char(string='Description')

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    followup_ids = fields.Many2many('crm.lead', 'crm_lead_dummy_followup_rel', 'lead_id', 'followup_id', string="Dummy Follow Ups")
    followup_progress = fields.Float(string="Dummy Progress")
    scheduled_date = fields.Date(string="Dummy Scheduled Date")
    state = fields.Selection([('draft', 'Pending'), ('done', 'Done')], string="Dummy Status")
    note = fields.Char(string="Dummy Note")
    tag_ids = fields.Many2many(string='Type of Lead', required=True)
    description = fields.Html(string='Lead Notes')
    opportunity_remark = fields.Html(string='Opportunity Remarks')
    reference_by = fields.Char(string='Reference By', required=True)
    contact_name = fields.Char(required=True)
    uyscuti_consumer_name = fields.Char(string='Consumer Name')
    uyscuti_consumer_id = fields.Char(string='Consumer Number')
    phone = fields.Char(required=True)
    state_id = fields.Many2one('res.country.state', required=True)
    city = fields.Char(required=True)

    # New solar-related fields
    solar_kw_capacity = fields.Float(string='PV Module - KW Capacity (DC)', digits=(10, 3))
    discom_id = fields.Many2one('solar.discom', string='Discom')
    sanction_load = fields.Char(string='Sanction Load')
    lat = fields.Float(string='Lat')
    long = fields.Float(string='Long')
    terrace_type_id = fields.Many2one('solar.terrace.type', string='Terrace Type')
    module_make_id = fields.Many2one('solar.module.make', string='Module Make')
    module_type_id = fields.Many2one('solar.module.type', string='Module Type')
    wp_id = fields.Many2one('solar.module.wp', string='WP')
    solar_pv_modules = fields.Char(string='No. of solar PV modules')
    existing_solar_plant = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Existing Solar Plant', default='no')
    existing_pv_cap = fields.Char(string='Existing PV Module Capacity (DC)')
    existing_inv_cap = fields.Char(string='Existing Inverter Capacity (AC)')
    light_bill_attachment = fields.Binary(string='Attachment (Light Bill)')
    light_bill_filename = fields.Char(string='Light Bill Filename')
    photo_ids = fields.One2many('crm.lead.photo', 'lead_id', string='Photos')
    reassign_user_id = fields.Many2one('res.users', string='Re-Assign to (Optional)')


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

    @api.onchange('partner_id')
    def _onchange_partner_id_consumer_sync(self):
        if self.partner_id:
            if not self.uyscuti_consumer_name:
                self.uyscuti_consumer_name = self.partner_id.uyscuti_consumer_name
            if not self.uyscuti_consumer_id:
                self.uyscuti_consumer_id = self.partner_id.uyscuti_consumer_id

    def _sync_consumer_to_partner(self, vals):
        """Helper to update partner if consumer details are changed in lead"""
        partner = self.partner_id
        if 'partner_id' in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
        
        if partner:
            partner_vals = {}
            if 'uyscuti_consumer_name' in vals:
                partner_vals['uyscuti_consumer_name'] = vals['uyscuti_consumer_name']
            if 'uyscuti_consumer_id' in vals:
                partner_vals['uyscuti_consumer_id'] = vals['uyscuti_consumer_id']
            
            if partner_vals:
                partner.sudo().write(partner_vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'phone' in vals:
                vals['phone'] = self._format_indian_number(vals['phone'])
            
            # Sync from partner if fields are empty
            if vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if not vals.get('uyscuti_consumer_name'):
                    vals['uyscuti_consumer_name'] = partner.uyscuti_consumer_name
                if not vals.get('uyscuti_consumer_id'):
                    vals['uyscuti_consumer_id'] = partner.uyscuti_consumer_id

        res = super(CrmLead, self).create(vals_list)
        for record, vals in zip(res, vals_list):
            # Sync TO partner if fields were provided in lead
            record._sync_consumer_to_partner(vals)
        return res

    def write(self, vals):
        if 'phone' in vals:
            vals['phone'] = self._format_indian_number(vals['phone'])
        
        # Sync from partner if fields are being set/changed and currently empty
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if not vals.get('uyscuti_consumer_name') and not self.uyscuti_consumer_name:
                 vals['uyscuti_consumer_name'] = partner.uyscuti_consumer_name
            if not vals.get('uyscuti_consumer_id') and not self.uyscuti_consumer_id:
                 vals['uyscuti_consumer_id'] = partner.uyscuti_consumer_id

        res = super(CrmLead, self).write(vals)
        
        # Sync TO partner
        for record in self:
            record._sync_consumer_to_partner(vals)
        return res

    def action_view_light_bill(self):
        """Open the light bill in a new tab for preview"""
        self.ensure_one()
        if not self.light_bill_attachment:
            return False
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/light_bill_attachment',
            'target': 'new',
        }