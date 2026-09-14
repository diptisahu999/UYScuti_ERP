from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import math
import logging

_logger = logging.getLogger(__name__)

def calculate_irr(cash_flows):
    """
    Calculate Internal Rate of Return (IRR) using Newton-Raphson method.
    cash_flows should be a list of numbers, starting with the initial investment (as a negative number).
    """
    if not cash_flows or all(x >= 0 for x in cash_flows) or all(x <= 0 for x in cash_flows):
        return 0.0
    
    # Try to find root
    r = 0.1 # initial guess
    for _ in range(100):
        npv = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cash_flows):
            npv += cf / ((1 + r) ** t)
            d_npv -= t * cf / ((1 + r) ** (t + 1))
        
        if abs(d_npv) < 1e-12:
            break
        r_new = r - npv / d_npv
        if abs(r_new - r) < 1e-6:
            return r_new * 100.0 # return percentage
        r = r_new
        if r < -0.99:
            r = -0.99
    return r * 100.0

class SolarFinancials(models.Model):
    _name = 'solar.financials'
    _description = 'Solar Financial Projection Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', default='/', readonly=True, copy=False)
    project_id = fields.Many2one('solar.project', string='Solar Project', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', string='Consumer Name', related='project_id.partner_id', store=True)
    project_type = fields.Selection(related='project_id.project_type', string='Project Type', store=True)
    
    # Sizing parameters
    kw_capacity = fields.Float(string='Capacity (kW)', related='project_id.kw_capacity', readonly=False, store=True)
    annual_yield_per_kw = fields.Float(string='Annual Yield (kWh/kW)', default=1700.0, required=True,
                                      help="Average generation in kWh per kW of installed capacity. E.g. 1700")
    
    # Financial parameters
    total_cost_lakh = fields.Float(string='Total Project Cost (Lakh Rs.)', default=10.0, required=True)
    equity_pct = fields.Float(string='Equity (%)', default=20.0, required=True)
    debt_pct = fields.Float(string='Debt (%)', default=80.0, required=True)
    
    equity_amount_lakh = fields.Float(string='Equity Amount (Lakh Rs.)', compute='_compute_debt_equity', store=True)
    debt_amount_lakh = fields.Float(string='Debt/Loan Amount (Lakh Rs.)', compute='_compute_debt_equity', store=True)
    
    # Loan parameters
    interest_rate_pct = fields.Float(string='Interest Rate (%)', default=9.5, required=True)
    tenure_years = fields.Integer(string='Loan Tenure (Years)', default=10, required=True)
    
    emi_amount_lakh = fields.Float(string='Monthly EMI (Lakh Rs.)', compute='_compute_loan_emi', store=True)
    yearly_emi_lakh = fields.Float(string='Yearly EMI (Lakh Rs.)', compute='_compute_loan_emi', store=True)
    total_interest_paid_lakh = fields.Float(string='Total Interest Paid (Lakh Rs.)', compute='_compute_loan_emi', store=True)
    total_repayment_lakh = fields.Float(string='Total Repayment (Lakh Rs.)', compute='_compute_loan_emi', store=True)

    # Subsidy parameters
    has_subsidy = fields.Boolean(string='Apply Subsidy', default=False)
    subsidy_amount_lakh = fields.Float(string='Subsidy Amount (Lakh Rs.)', default=0.0)

    # O&M details
    om_cost_yr1_lakh = fields.Float(string='O&M Cost Year 1 (Lakh Rs.)', default=0.25, required=True)
    om_escalation_pct = fields.Float(string='O&M Annual Escalation (%)', default=3.5, required=True)

    # Tariff and Generation parameters
    tariff_rate = fields.Float(string='Tariff Rate (Rs./kWh)', default=8.85, required=True)
    tariff_escalation_pct = fields.Float(string='Tariff Annual Escalation (%)', default=1.0, required=True)
    
    # Degradation rules
    degradation_yr2_pct = fields.Float(string='Year 2 Degradation (%)', default=2.5, required=True)
    degradation_subsequent_pct = fields.Float(string='Subsequent Year Degradation (%)', default=0.7, required=True)

    # Projection Output Lines
    cashflow_line_ids = fields.One2many('solar.financials.cashflow', 'financial_id', string='25-Year Cashflows', copy=False)

    # Summary metrics
    total_net_profit_lakh = fields.Float(string='Total 25-Year Net Profit (Lakh Rs.)', compute='_compute_metrics', store=True)
    roi_pct = fields.Float(string='ROI (%)', compute='_compute_metrics', store=True)
    irr_pct = fields.Float(string='IRR (%)', compute='_compute_metrics', store=True)

    @api.depends('total_cost_lakh', 'equity_pct', 'debt_pct')
    def _compute_debt_equity(self):
        for rec in self:
            rec.equity_amount_lakh = rec.total_cost_lakh * (rec.equity_pct / 100.0)
            rec.debt_amount_lakh = rec.total_cost_lakh * (rec.debt_pct / 100.0)

    @api.depends('debt_amount_lakh', 'interest_rate_pct', 'tenure_years')
    def _compute_loan_emi(self):
        for rec in self:
            if rec.debt_amount_lakh > 0 and rec.interest_rate_pct > 0 and rec.tenure_years > 0:
                p = rec.debt_amount_lakh
                r = (rec.interest_rate_pct / 12.0) / 100.0
                n = rec.tenure_years * 12
                try:
                    monthly_emi = p * (r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)
                    rec.emi_amount_lakh = monthly_emi
                    rec.yearly_emi_lakh = monthly_emi * 12.0
                    rec.total_repayment_lakh = rec.yearly_emi_lakh * rec.tenure_years
                    rec.total_interest_paid_lakh = rec.total_repayment_lakh - p
                except Exception:
                    rec.emi_amount_lakh = 0.0
                    rec.yearly_emi_lakh = 0.0
                    rec.total_repayment_lakh = 0.0
                    rec.total_interest_paid_lakh = 0.0
            else:
                rec.emi_amount_lakh = 0.0
                rec.yearly_emi_lakh = 0.0
                rec.total_repayment_lakh = 0.0
                rec.total_interest_paid_lakh = 0.0

    @api.depends('cashflow_line_ids.net_profit_lakh', 'equity_amount_lakh')
    def _compute_metrics(self):
        for rec in self:
            total_net_profit = sum(rec.cashflow_line_ids.mapped('net_profit_lakh'))
            rec.total_net_profit_lakh = total_net_profit
            
            if rec.equity_amount_lakh > 0:
                rec.roi_pct = (total_net_profit / rec.equity_amount_lakh) * 100.0
            else:
                rec.roi_pct = 0.0

            # Calculate IRR
            # Initial investment (outflow) at Year 0 is -equity_amount
            # Subsidy could reduce the initial investment or be added to Year 1 cash flow.
            # Let's model it: Year 0 outflow = - (equity_amount - subsidy_amount) if subsidy reduces initial investment,
            # or treat subsidy as received in Year 1. Let's subtract subsidy from Year 0 if has_subsidy.
            initial_outflow = -rec.equity_amount_lakh
            if rec.has_subsidy:
                initial_outflow += rec.subsidy_amount_lakh
                
            cash_flows = [initial_outflow]
            # Add cash flows for Year 1 to 25
            for line in sorted(rec.cashflow_line_ids, key=lambda l: l.year):
                cash_flows.append(line.net_profit_lakh)
            
            rec.irr_pct = calculate_irr(cash_flows)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.financials') or '/'
        records = super().create(vals_list)
        for rec in records:
            rec.action_recalculate_projections()
        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_fields = [
            'kw_capacity', 'annual_yield_per_kw', 'total_cost_lakh', 'equity_pct',
            'debt_pct', 'interest_rate_pct', 'tenure_years', 'has_subsidy', 'subsidy_amount_lakh',
            'om_cost_yr1_lakh', 'om_escalation_pct', 'tariff_rate', 'tariff_escalation_pct',
            'degradation_yr2_pct', 'degradation_subsequent_pct'
        ]
        if any(f in vals for f in trigger_fields):
            for rec in self:
                rec.action_recalculate_projections()
        return res

    def action_recalculate_projections(self):
        """Generates/Updates the 25-Year Projection lines for this financial model"""
        self.ensure_one()
        self.cashflow_line_ids.unlink()

        lines = []
        cumulative_income = 0.0

        # Calculations base
        base_generation = (self.kw_capacity / 1000.0) * 1700000.0 if self.kw_capacity else 0.0
        if not base_generation and self.kw_capacity:
            base_generation = self.kw_capacity * self.annual_yield_per_kw

        current_gen = base_generation
        current_om = self.om_cost_yr1_lakh
        current_tariff = self.tariff_rate

        for yr in range(1, 26):
            # 1. Degradation Logic
            if yr == 1:
                # Year 1: base generation
                pass
            elif yr == 2:
                # Year 2 degradation
                current_gen *= (1.0 - self.degradation_yr2_pct / 100.0)
            else:
                # Subsequent years degradation
                current_gen *= (1.0 - self.degradation_subsequent_pct / 100.0)

            # 2. Tariff Escalation (compounded yearly after Year 1)
            if yr > 1:
                current_tariff *= (1.0 + self.tariff_escalation_pct / 100.0)

            # 3. Revenue = (generation * tariff) / 100,000 to convert to Lakhs
            revenue_lakh = (current_gen * current_tariff) / 100000.0

            # 4. O&M Cost Escalation (escalated yearly starting from Year 2)
            if yr > 1:
                current_om *= (1.0 + self.om_escalation_pct / 100.0)

            # 5. Loan EMI (only paid during loan tenure)
            emi_lakh = self.yearly_emi_lakh if yr <= self.tenure_years else 0.0

            # 6. Expenses = O&M + EMI
            expenses_lakh = current_om + emi_lakh

            # 7. Net Profit = Revenue - Expenses
            net_profit_lakh = revenue_lakh - expenses_lakh
            cumulative_income += net_profit_lakh

            lines.append({
                'financial_id': self.id,
                'year': yr,
                'generation_units': current_gen,
                'tariff_rate': current_tariff,
                'revenue_lakh': revenue_lakh,
                'om_expenses_lakh': current_om,
                'emi_expenses_lakh': emi_lakh,
                'net_profit_lakh': net_profit_lakh,
                'cumulative_income_lakh': cumulative_income
            })

        self.env['solar.financials.cashflow'].create(lines)
        return True


class SolarFinancialsCashflow(models.Model):
    _name = 'solar.financials.cashflow'
    _description = 'Solar Financials 25-Year Cashflow Line'
    _order = 'year asc'

    financial_id = fields.Many2one('solar.financials', string='Financial Ref', ondelete='cascade', index=True)
    year = fields.Integer(string='Year', required=True)
    generation_units = fields.Float(string='Generation (kWh)', digits=(16, 2))
    tariff_rate = fields.Float(string='Tariff Rate (Rs./kWh)', digits=(10, 4))
    revenue_lakh = fields.Float(string='Yearly Revenue (Lakh Rs.)', digits=(12, 4))
    om_expenses_lakh = fields.Float(string='O&M Expenses (Lakh Rs.)', digits=(12, 4))
    emi_expenses_lakh = fields.Float(string='EMI Expenses (Lakh Rs.)', digits=(12, 4))
    net_profit_lakh = fields.Float(string='Net Profit/Cashflow (Lakh Rs.)', digits=(12, 4))
    cumulative_income_lakh = fields.Float(string='Cumulative Cashflow (Lakh Rs.)', digits=(12, 4))
