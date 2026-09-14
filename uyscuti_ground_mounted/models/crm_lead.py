from odoo import models, fields, api, _

class SolarDiscom(models.Model):
    _inherit = 'solar.discom'

    # Master loss and charge parameters for Ground Mounted calculations
    wheeling_loss_pct = fields.Float(string='Wheeling Loss (%)', default=7.0)
    wheeling_rate = fields.Float(string='Wheeling Charge Rate (Rs./kWh)', default=0.21)
    trans_loss_pct = fields.Float(string='Transmission Loss (%)', default=3.5)
    scheduling_rate = fields.Float(string='Scheduling Charge (Rs.)', default=1000.0)
    trans_rate = fields.Float(string='Transmission Charge Rate (Rs./kWh)', default=0.15)
    sec_wheeling_loss_pct = fields.Float(string='Secondary Wheeling Loss (%)', default=0.0)
    sec_wheeling_rate = fields.Float(string='Secondary Wheeling Charge Rate (Rs./kWh)', default=0.0)
    banking_rate = fields.Float(string='Banking Charge Rate (Rs./kWh)', default=1.5)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    solar_lead_type = fields.Selection([
        ('commercial', 'Commercial / Industrial'),
        ('ground_mounted', 'Ground Mounted'),
    ], string='Solar Lead Type', default='ground_mounted', required=True)

    gm_proposal_ids = fields.One2many(
        'solar.gm.proposal', 'lead_id', string='Ground Mounted Proposals'
    )
    gm_proposal_count = fields.Integer(
        string='Proposals Count', compute='_compute_gm_proposal_count'
    )

    @api.depends('gm_proposal_ids')
    def _compute_gm_proposal_count(self):
        for lead in self:
            lead.gm_proposal_count = len(lead.gm_proposal_ids)

    def action_view_gm_proposals(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('uyscuti_ground_mounted.action_solar_gm_proposal')
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {
            'default_lead_id': self.id,
            'default_partner_id': self.partner_id.id or False,
            'default_customer_name': self.partner_id.name or self.contact_name or '',
            'default_customer_mobile': self.partner_id.phone or self.phone or '',
            'default_contract_demand': self.solar_kw_capacity or 0.0,
            'default_discom_drawl_id': self.discom_id.id or False,
        }
        return action
