from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Solar Details
    solar_plant_id = fields.Many2one('solar.plant', string='Solar Plant')
    solar_kw_capacity = fields.Float(string='Solar Capacity (KW)', digits=(10, 3))
    solar_sanction_load = fields.Float(string='Sanction Load (KW)')
    solar_sanction_phase = fields.Selection([('1ph', '1PH'), ('3ph', '3PH')], string='Sanction Load Phase', default='1ph')
    solar_load_phase = fields.Selection([('1ph', '1PH'), ('3ph', '3PH')], string='Solar Load Phase', default='1ph')
    solar_discom_id = fields.Many2one('solar.discom', string='Discom')
    uyscuti_consumer_name = fields.Char(string='Consumer Name')
    uyscuti_consumer_id = fields.Char(string='Consumer Number')
    
    # Solar Prices
    system_price = fields.Float(string='System Price')
    discom_fees = fields.Float(string='Discom Fees', compute='_compute_solar_charges', store=True, readonly=False)
    mss_price = fields.Float(string='MSS Price')
    system_strength_charges = fields.Float(string='System Strength Charges', compute='_compute_solar_charges', store=True, readonly=False)
    legal_charges = fields.Float(string='Legal Charges')
    discount = fields.Float(string='Discount')

    @api.depends('solar_kw_capacity', 'solar_sanction_load', 'solar_sanction_phase', 'solar_load_phase', 'solar_discom_id')
    def _compute_solar_charges(self):
        for order in self:
            # 1. Calculate Discom Fees from Master
            # Uses Sanction Load (KW) to match against the fee rule ranges
            d_fees = 0.0
            if order.solar_discom_id and order.solar_sanction_load:
                domain = [
                    ('discom_id', '=', order.solar_discom_id.id),
                    ('sanction_phase', '=', order.solar_sanction_phase),
                    ('load_phase', '=', order.solar_load_phase),
                    ('min_kw', '<=', order.solar_sanction_load),
                    ('max_kw', '>=', order.solar_sanction_load),
                ]
                fee_rule = self.env['solar.discom.fee'].search(domain, limit=1)
                if fee_rule:
                    d_fees = fee_rule.fee
                else:
                    # Fallback: match only by phase, pick the highest min_kw rule
                    fallback_domain = [
                        ('discom_id', '=', order.solar_discom_id.id),
                        ('sanction_phase', '=', order.solar_sanction_phase),
                        ('load_phase', '=', order.solar_load_phase),
                    ]
                    fallback_rule = self.env['solar.discom.fee'].search(
                        fallback_domain, limit=1, order='min_kw desc'
                    )
                    if fallback_rule:
                        d_fees = fallback_rule.fee

            order.discom_fees = d_fees

            # 2. Calculate System Strength Charges from Master
            # Uses PV Capacity (KW) for system strength calculation
            s_charges = 0.0
            kw = order.solar_kw_capacity
            if kw:
                strength_rule = self.env['solar.system.strength.config'].search([
                    ('min_kw', '<=', kw),
                    ('max_kw', '>=', kw),
                ], limit=1, order='min_kw asc')

                if strength_rule:
                    s_charges = strength_rule.fixed_fee + (kw * strength_rule.per_kw_fee)

            order.system_strength_charges = s_charges

    @api.onchange('solar_kw_capacity', 'solar_sanction_load', 'solar_sanction_phase', 'solar_load_phase', 'solar_discom_id')
    def _onchange_solar_charges(self):
        """Update Discom Fee and System Strength Charges in real-time as user changes inputs."""
        self._compute_solar_charges()

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id_map_solar(self):
        """Map solar details from CRM Opportunity to Sale Order when opportunity is selected."""
        if self.opportunity_id:
            opp = self.opportunity_id
            self.solar_discom_id = opp.discom_id
            self.solar_kw_capacity = opp.solar_kw_capacity
            self.uyscuti_consumer_name = opp.uyscuti_consumer_name
            self.uyscuti_consumer_id = opp.uyscuti_consumer_id
            try:
                self.solar_sanction_load = float(opp.sanction_load) if opp.sanction_load else 0.0
            except (ValueError, TypeError):
                self.solar_sanction_load = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If opportunity_id is set at creation and kw not provided, fetch it
            if vals.get('opportunity_id') and not vals.get('solar_kw_capacity'):
                opp = self.env['crm.lead'].browse(vals['opportunity_id'])
                vals['solar_kw_capacity'] = opp.solar_kw_capacity
                if not vals.get('uyscuti_consumer_name'):
                    vals['uyscuti_consumer_name'] = opp.uyscuti_consumer_name
                if not vals.get('uyscuti_consumer_id'):
                    vals['uyscuti_consumer_id'] = opp.uyscuti_consumer_id
                if opp.discom_id and not vals.get('solar_discom_id'):
                    vals['solar_discom_id'] = opp.discom_id.id
        return super().create(vals_list)

    def action_confirm(self):
        for order in self:
            # Check if partner is a company and has no GST number (vat)
            if order.partner_id.company_type == 'company' and not order.partner_id.vat:
                raise ValidationError(_("Please add GST number for company contact: %s") % order.partner_id.name)
        
        return super(SaleOrder, self).action_confirm()

    @api.onchange('partner_id')
    def _onchange_partner_id_consumer_sync(self):
        """Fetch consumer details from partner if not set."""
        if self.partner_id:
            if not self.uyscuti_consumer_name:
                self.uyscuti_consumer_name = self.partner_id.uyscuti_consumer_name
            if not self.uyscuti_consumer_id:
                self.uyscuti_consumer_id = self.partner_id.uyscuti_consumer_id

        # Original shipping logic
        if self.partner_id and self.partner_shipping_id:
            valid_ids = (
                self.partner_id
                | self.partner_id.child_ids.filtered(
                    lambda c: c.type == 'delivery'
                )
            ).ids
            if self.partner_shipping_id.id not in valid_ids:
                self.partner_shipping_id = self.partner_id
