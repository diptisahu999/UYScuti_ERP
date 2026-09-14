from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gm_proposal_id = fields.Many2one(
        'solar.gm.proposal', 
        string='GM Customer Proposal', 
        compute='_compute_gm_proposal_id',
        store=True,
        readonly=False
    )
    is_ground_mounted = fields.Boolean(
        string='Is Ground Mounted', 
        compute='_compute_is_ground_mounted', 
        store=True
    )



    # Related proposal fields for embedded UI display
    gm_proposal_capacity_mw = fields.Float(
        related='gm_proposal_id.capacity_mw', 
        string='Plant Capacity (MW)', 
        readonly=True
    )
    gm_proposal_total_cost = fields.Float(
        related='gm_proposal_id.total_cost_lakh', 
        string='Total Cost (Lakh)', 
        readonly=True
    )
    gm_proposal_yearly_emi = fields.Float(
        related='gm_proposal_id.yearly_emi_lakh', 
        string='Yearly EMI (Lakh)', 
        readonly=True
    )
    gm_proposal_net_losses = fields.Float(
        related='gm_proposal_id.net_losses_pct', 
        string='Net Losses (%)', 
        readonly=True
    )
    gm_proposal_line_ids = fields.One2many(
        related='gm_proposal_id.projection_line_ids', 
        string='25-Year Projections', 
        readonly=True
    )

    @api.depends('opportunity_id.solar_lead_type')
    def _compute_is_ground_mounted(self):
        for order in self:
            order.is_ground_mounted = order.opportunity_id and order.opportunity_id.solar_lead_type in ('ground_mounted', 'commercial')

    @api.depends('opportunity_id', 'is_ground_mounted')
    def _compute_gm_proposal_id(self):
        for order in self:
            if order.is_ground_mounted and order.opportunity_id:
                proposals = order.opportunity_id.gm_proposal_ids
                if proposals:
                    order.gm_proposal_id = proposals[0].id
                else:
                    order.gm_proposal_id = False
            else:
                order.gm_proposal_id = False

    # Sync capacity & discom from linked GM Proposal to standard solar fields
    @api.depends('gm_proposal_id')
    def _compute_solar_project_sync(self):
        for order in self:
            if order.gm_proposal_id:
                order.solar_kw_capacity = order.gm_proposal_id.capacity_mw * 1000.0
                order.solar_discom_id = order.gm_proposal_id.discom_injection_id.id

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.is_ground_mounted and order.solar_project_id:
                p_type = 'commercial' if order.opportunity_id.solar_lead_type == 'commercial' else 'ground_mounted'
                order.solar_project_id.write({
                    'project_type': p_type,
                    'state': 'loa',
                })
        return res

    def action_view_solar_project(self):
        self.ensure_one()
        if self.solar_project_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Solar Project'),
                'res_model': 'solar.project',
                'view_mode': 'form',
                'res_id': self.solar_project_id.id,
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window_close'
        }
