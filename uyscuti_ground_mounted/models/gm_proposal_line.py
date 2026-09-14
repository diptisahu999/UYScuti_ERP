from odoo import models, fields

class SolarGmProposalLine(models.Model):
    _name = 'solar.gm.proposal.line'
    _description = 'Ground Mounted Solar Proposal 25-Year Projection Line'
    _order = 'year asc'

    proposal_id = fields.Many2one('solar.gm.proposal', string='Proposal Ref', ondelete='cascade', index=True)
    year = fields.Integer(string='Year', required=True)
    received_units = fields.Float(string='Received Units (Generation - Losses)', digits=(16, 2))
    rate_kwh = fields.Float(string='Rate/kWh', digits=(10, 4))
    yearly_revenue = fields.Float(string='Yly. Revenue (Lakh)', digits=(12, 4))
    grid_expenses = fields.Float(string='Expense (Grid)', digits=(12, 4))
    om_expenses = fields.Float(string='O&M Exp (Lakh)', digits=(12, 4))
    land_lease = fields.Float(string='Land Lease (Lakh)', digits=(12, 4))
    emi = fields.Float(string='EMI (Lakh)', digits=(12, 4))
    net_income = fields.Float(string='Net Income (Lakh)', digits=(12, 4))
    gst_input_credit = fields.Float(string='GST Input Credit (Lakh)', digits=(12, 4))
    cumulative_income = fields.Float(string='Cumulative Income (Lakh)', digits=(12, 4))
