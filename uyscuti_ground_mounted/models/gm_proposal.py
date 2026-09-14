from odoo import models, fields, api, _
from odoo.exceptions import UserError
import math

class SolarGmProposal(models.Model):
    _name = 'solar.gm.proposal'
    _description = 'Ground Mounted Solar Customer Proposal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Proposal Reference', default='/', readonly=True, copy=False)
    lead_id = fields.Many2one('crm.lead', string='Lead / Opportunity', ondelete='set null')
    partner_id = fields.Many2one('res.partner', string='Customer')
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_mobile = fields.Char(string='Customer Mobile', required=True)
    remark = fields.Text(string='Remark')

    # Left Column Inputs
    consumer_type = fields.Selection([
        ('lt', 'LT (Low Tension)'),
        ('ht', 'HT (High Tension)'),
        ('ehv', 'EHV (Extra High Voltage)'),
    ], string='Type of Consumer', default='ht')
    power_boundary = fields.Selection([
        ('clear', 'Clear'),
        ('multiple', 'Multiple'),
    ], string='Power Boundary', default='clear')
    duty_status = fields.Selection([
        ('exemption', 'Exempted'),
        ('taxable', 'Taxable'),
    ], string='Electricity Duty Status', default='exemption')
    contract_demand = fields.Float(string='Total Contract Demand (kW)', default=100.0)
    existing_solar_capacity = fields.Float(string='Existing Solar Capacity (kW)', default=0.0)
    monthly_usage = fields.Float(string='Monthly Usage (Units)', default=10000.0)
    monthly_bill = fields.Float(string='Monthly Bill (INR)', default=88500.0)
    project_type = fields.Selection([
        ('cpp', 'CPP (Captive Power Plant)'),
        ('drebp', 'DREBP'),
        ('third_party', 'Third Party'),
    ], string='Type of Project', default='cpp')
    discom_drawl_id = fields.Many2one('solar.discom', string='Drawl Point Discom')
    discom_injection_id = fields.Many2one('solar.discom', string='Injection Point Discom')

    # Left Column Outputs
    monthly_req_units_daytime = fields.Float(
        string='Monthly Req. Units (Day Time)', compute='_compute_monthly_req_units_daytime', store=True
    )
    losses_compensation_pct = fields.Float(
        string='Total Losses Compensation (%)', compute='_compute_losses_compensation_pct', store=True
    )
    req_units_from_solar = fields.Float(
        string='Total Req. Units From Solar', compute='_compute_req_units_from_solar', store=True
    )
    suggested_capacity_dc = fields.Float(
        string='Suggested Plant Capacity (DC) kW', compute='_compute_suggested_capacity_dc', store=True
    )
    actual_capacity_dc = fields.Float(
        string='Actual Plant Capacity (DC) kW', compute='_compute_actual_capacity_dc', store=True
    )

    # Right Column Solar Plant Capacity & Charges (MW)
    capacity_mw = fields.Float(string='Solar Plant Capacity (DC) in MW', default=1.0)
    daily_gen_point = fields.Float(string='Daily Gen Point (kWh)', compute='_compute_charges_and_losses', store=True)
    
    # Losses %
    wheeling_loss_pct = fields.Float(string='Wheeling Loss (%)', default=7.0)
    trans_loss_pct = fields.Float(string='Transmission Loss (%)', default=3.5)
    sec_wheeling_loss_pct = fields.Float(string='Secondary Wheeling Loss (%)', default=0.0)

    # Charges Rates (Rs/kWh)
    wheeling_charge_rate = fields.Float(string='Wheeling Charge Rate (Rs./kWh)', default=0.21)
    scheduling_charge_rate = fields.Float(string='Scheduling Charge (Rs.)', default=1000.0)
    trans_charge_rate = fields.Float(string='Transmission Charge Rate (Rs./kWh)', default=0.15)
    sec_wheeling_charge_rate = fields.Float(string='Secondary Wheeling Charge Rate (Rs./kWh)', default=0.0)
    banking_charge_rate = fields.Float(string='Banking Charge Rate (Rs./kWh)', default=1.5)

    # Losses / Charges Daily kWh and Rs.
    wheeling_loss_units = fields.Float(string='Wheeling Loss (kWh)', compute='_compute_charges_and_losses', store=True)
    wheeling_charge_units = fields.Float(string='Wheeling Charges (kWh)', compute='_compute_charges_and_losses', store=True)
    wheeling_charge_rs = fields.Float(string='Wheeling Charges (Rs.)', compute='_compute_charges_and_losses', store=True)
    
    trans_loss_units = fields.Float(string='Transmission Losses (kWh)', compute='_compute_charges_and_losses', store=True)
    scheduling_charge_rs = fields.Float(string='Scheduling Charges (Rs.)', compute='_compute_charges_and_losses', store=True)
    
    trans_charge_units = fields.Float(string='Transmission Charges (kWh)', compute='_compute_charges_and_losses', store=True)
    trans_charge_rs = fields.Float(string='Transmission Charges (Rs.)', compute='_compute_charges_and_losses', store=True)

    sec_wheeling_loss_units = fields.Float(string='Secondary Wheeling Losses (kWh)', compute='_compute_charges_and_losses', store=True)
    sec_wheeling_charge_units = fields.Float(string='Secondary Wheeling Charges (kWh)', compute='_compute_charges_and_losses', store=True)
    sec_wheeling_charge_rs = fields.Float(string='Secondary Wheeling Charges (Rs.)', compute='_compute_charges_and_losses', store=True)

    banking_charge_units = fields.Float(string='Banking Charges (kWh)', compute='_compute_banking_units', store=True)
    banking_charge_rs = fields.Float(string='Banking Charges (Rs.)', compute='_compute_charges_and_losses', store=True)

    net_losses_pct = fields.Float(string='Net Losses (%)', compute='_compute_charges_and_losses', store=True)
    total_grid_charges_rs = fields.Float(string='Total Daily Charges (Rs.)', compute='_compute_charges_and_losses', store=True)

    # Middle Table: Fixed Charges & Unit Costs
    fixed_charge_1 = fields.Float(string='Fixed Charges 1st 500 kVA', default=0.0)
    fixed_charge_2 = fields.Float(string='Fixed Charges 2nd 500 kVA', default=0.0)
    fixed_charge_3 = fields.Float(string='Fixed Charges Above 1000 kVA', default=0.0)
    fixed_charge_total = fields.Float(string='Total Fixed Charges', compute='_compute_fixed_charges', store=True)

    per_unit_cost_incl_fc = fields.Float(string='Per Unit Cost (incl. Fix Charge)', compute='_compute_unit_costs', store=True)
    per_unit_cost_excl_fc = fields.Float(string='Per Unit Cost (excl. Fix Charge)', compute='_compute_unit_costs', store=True)
    per_unit_cost_wheeling = fields.Float(string='Per Unit Cost of Wheeling', compute='_compute_unit_costs', store=True)
    income_solar_gen = fields.Float(string='Income From Solar Plant Generation', compute='_compute_unit_costs', store=True)

    # Bottom Left Table: Capital Cost & Project Parameters
    annual_power_gen_mwh = fields.Float(string='Power Generation (MWH)', compute='_compute_power_generation', store=True)
    degradation_yr1 = fields.Float(string='Degradation for 1st Year (%)', default=1.0)
    degradation_after_yr2 = fields.Float(string='Degradation after 2nd Year (%)', default=0.5)
    cumulative_losses_pct = fields.Float(string='Cumulative Losses (%)', compute='_compute_cumulative_losses', store=True)
    land_req_acre_per_mw = fields.Float(string='Land Requirement (Acre/MW)', default=4.0)
    ss_distance_km = fields.Float(string='Distance from 66 kV SS (KM)', default=1.0)
    electricity_income_rate = fields.Float(string='Electricity Income Rate (Rs./Unit)', default=8.85)

    # Capital Cost parameters (Yellow Inputs)
    capital_cost_per_mw = fields.Float(string='Capital Cost per MW (incl. GST) (Rs. in Lakh)', default=400.0)
    land_cost_per_acre = fields.Float(string='Land Cost per Acre (Rs. in Lakh)', default=5.0)
    transmission_line_cost_per_km = fields.Float(string='Transmission Line Cost (Rs. in Lakh)', default=15.0)
    other_dev_cost_per_mw = fields.Float(string='Other Development Cost per MW (Rs. in Lakh)', default=20.0)

    # Cost Outputs (Rs in Lakh)
    solar_plant_cost_lakh = fields.Float(string='Solar PV Power Plant Cost (Rs. in Lakh)', compute='_compute_project_costs', store=True)
    total_land_cost_lakh = fields.Float(string='Total Land Cost (Rs. in Lakh)', compute='_compute_project_costs', store=True)
    total_line_cost_lakh = fields.Float(string='Total Line Cost (Rs. in Lakh)', compute='_compute_project_costs', store=True)
    other_misc_expenses_lakh = fields.Float(string='Other Misc. Expenses (Rs. in Lakh)', compute='_compute_project_costs', store=True)
    total_cost_lakh = fields.Float(string='Total Cost (Rs. in Lakh)', compute='_compute_project_costs', store=True)

    # Bottom Right Table: Maintenance & Financing / Loan
    om_cost_per_mw = fields.Float(string='Operation & Maintenance Cost per MW (Rs. in Lakh)', default=2.5)
    om_cost_yr1 = fields.Float(string='O&M Cost (Rs. in Lakh)', compute='_compute_om_cost_yr1', store=True)
    om_increment_pct = fields.Float(string='O&M Cost Increment (%)', default=5.0)
    om_increment_interval = fields.Integer(string='O&M Cost Increment Interval (Year)', default=1)
    
    land_lease_cost_yr1 = fields.Float(string='Land Lease Cost (Rs. in Lakh)', default=0.0)
    land_lease_increment_pct = fields.Float(string='Land Lease Increment (%)', default=5.0)
    land_lease_increment_interval = fields.Integer(string='Land Lease Increment Interval (Year)', default=1)
    
    total_maintenance_cost_lakh = fields.Float(string='Total Maintenance Cost (Rs. in Lakh)', compute='_compute_total_maintenance', store=True)

    # Debt / Equity Parameters
    debt_amount_lakh = fields.Float(string='Debt Amount @ 80% (Rs. in Lakh)', compute='_compute_debt_equity', store=True)
    equity_amount_lakh = fields.Float(string='Equity Amount @ 20% (Rs. in Lakh)', compute='_compute_debt_equity', store=True)
    yearly_emi_lakh = fields.Float(string='Yearly EMI Amount (Rs. in Lakh)', compute='_compute_loan_emi', store=True)
    principal_lakh = fields.Float(string='Principal (Rs. in Lakh)', compute='_compute_debt_equity', store=True)
    interest_rate_pct = fields.Float(string='Rate of Interest (%)', default=9.5)
    tenure_years = fields.Integer(string='Tenure in Years (Year)', default=10)
    emi_amount_lakh = fields.Float(string='EMI Amount (Rs. in Lakh)', compute='_compute_loan_emi', store=True)
    total_repayment_lakh = fields.Float(string='Total Repayment (Rs. in Lakh)', compute='_compute_loan_emi', store=True)
    total_interest_paid_lakh = fields.Float(string='Total Interest Paid (Rs. in Lakh)', compute='_compute_loan_emi', store=True)

    # 25-Year Projection lines
    projection_line_ids = fields.One2many(
        'solar.gm.proposal.line', 'proposal_id', string='25-Year Projections', copy=False
    )

    # --- Computes ---
    @api.depends('monthly_usage')
    def _compute_monthly_req_units_daytime(self):
        for rec in self:
            rec.monthly_req_units_daytime = rec.monthly_usage * 0.65

    @api.depends('wheeling_loss_pct', 'trans_loss_pct', 'sec_wheeling_loss_pct')
    def _compute_losses_compensation_pct(self):
        for rec in self:
            # Combined multiplicative losses factor
            w = rec.wheeling_loss_pct / 100.0
            t = rec.trans_loss_pct / 100.0
            s = rec.sec_wheeling_loss_pct / 100.0
            total_loss_pct = (1.0 - (1.0 - w) * (1.0 - t) * (1.0 - s)) * 100.0
            rec.losses_compensation_pct = total_loss_pct

    @api.depends('monthly_req_units_daytime', 'monthly_usage', 'losses_compensation_pct')
    def _compute_req_units_from_solar(self):
        for rec in self:
            night_usage = rec.monthly_usage - rec.monthly_req_units_daytime
            banking_units = night_usage * 0.30
            base_req = rec.monthly_req_units_daytime + banking_units
            rec.req_units_from_solar = base_req * (1.0 + rec.losses_compensation_pct / 100.0)

    @api.depends('req_units_from_solar')
    def _compute_suggested_capacity_dc(self):
        for rec in self:
            rec.suggested_capacity_dc = rec.req_units_from_solar / 30.0 / 4.0

    @api.depends('capacity_mw')
    def _compute_actual_capacity_dc(self):
        for rec in self:
            rec.actual_capacity_dc = rec.capacity_mw * 1000.0

    @api.depends('monthly_usage', 'monthly_req_units_daytime')
    def _compute_banking_units(self):
        for rec in self:
            night_usage = rec.monthly_usage - rec.monthly_req_units_daytime
            rec.banking_charge_units = night_usage * 0.30

    @api.depends('capacity_mw', 'wheeling_loss_pct', 'wheeling_charge_rate', 'trans_loss_pct', 
                 'scheduling_charge_rate', 'trans_charge_rate', 'sec_wheeling_loss_pct', 
                 'sec_wheeling_charge_rate', 'banking_charge_rate', 'banking_charge_units')
    def _compute_charges_and_losses(self):
        for rec in self:
            # Daily Gen Point (kWh) = MW * 1000 * 4
            gen = rec.capacity_mw * 1000.0 * 4.0
            rec.daily_gen_point = gen

            # 1. Wheeling
            wl = gen * (rec.wheeling_loss_pct / 100.0)
            rec.wheeling_loss_units = wl
            w_chg_units = gen - wl
            rec.wheeling_charge_units = w_chg_units
            rec.wheeling_charge_rs = w_chg_units * rec.wheeling_charge_rate

            # 2. GETCO Transmission Loss & Scheduling
            tl = w_chg_units * (rec.trans_loss_pct / 100.0)
            rec.trans_loss_units = tl
            
            # Scheduling charges = (Capacity MW * 1000 / 1.3 / 1000) * Scheduling Charge Rate
            sched_val = (rec.capacity_mw * 1000.0 / 1.3 / 1000.0) * rec.scheduling_charge_rate
            rec.scheduling_charge_rs = sched_val

            # Transmission Charges
            t_chg_units = w_chg_units - tl
            rec.trans_charge_units = t_chg_units
            rec.trans_charge_rs = t_chg_units * rec.trans_charge_rate

            # 3. Secondary Wheeling
            swl = t_chg_units * (rec.sec_wheeling_loss_pct / 100.0)
            rec.sec_wheeling_loss_units = swl
            sw_chg_units = t_chg_units - swl
            rec.sec_wheeling_charge_units = sw_chg_units
            rec.sec_wheeling_charge_rs = sw_chg_units * rec.sec_wheeling_charge_rate

            # 4. Banking Charges (Rs) = Units * Rate * 0.3
            rec.banking_charge_rs = rec.banking_charge_units * rec.banking_charge_rate * 0.3

            # Net Losses %
            final_units = sw_chg_units  # final deliverable after all steps
            if gen > 0:
                rec.net_losses_pct = (1.0 - (final_units / gen)) * 100.0
            else:
                rec.net_losses_pct = 0.0

            # Total Daily Charges (Rs)
            rec.total_grid_charges_rs = (
                rec.wheeling_charge_rs + rec.scheduling_charge_rs + 
                rec.trans_charge_rs + rec.sec_wheeling_charge_rs + rec.banking_charge_rs
            )

    @api.depends('fixed_charge_1', 'fixed_charge_2', 'fixed_charge_3')
    def _compute_fixed_charges(self):
        for rec in self:
            rec.fixed_charge_total = rec.fixed_charge_1 + rec.fixed_charge_2 + rec.fixed_charge_3

    @api.depends('monthly_bill', 'monthly_usage', 'total_grid_charges_rs', 'fixed_charge_total', 'electricity_income_rate')
    def _compute_unit_costs(self):
        for rec in self:
            # Per unit cost including Fixed Charge
            if rec.monthly_usage > 0:
                rec.per_unit_cost_incl_fc = rec.monthly_bill / rec.monthly_usage
                rec.per_unit_cost_excl_fc = (rec.monthly_bill - rec.fixed_charge_total) / rec.monthly_usage
                rec.per_unit_cost_wheeling = (rec.total_grid_charges_rs * 30.0) / rec.monthly_usage
            else:
                rec.per_unit_cost_incl_fc = 0.0
                rec.per_unit_cost_excl_fc = 0.0
                rec.per_unit_cost_wheeling = 0.0
            rec.income_solar_gen = rec.electricity_income_rate

    @api.depends('capacity_mw')
    def _compute_power_generation(self):
        for rec in self:
            # Annual generation in MWH
            rec.annual_power_gen_mwh = rec.capacity_mw * 1000.0 * 4.0 * 365.0 / 1000.0

    @api.depends('net_losses_pct')
    def _compute_cumulative_losses(self):
        for rec in self:
            rec.cumulative_losses_pct = rec.net_losses_pct

    @api.depends('capacity_mw', 'capital_cost_per_mw', 'land_req_acre_per_mw', 'land_cost_per_acre', 
                 'ss_distance_km', 'transmission_line_cost_per_km', 'other_dev_cost_per_mw')
    def _compute_project_costs(self):
        for rec in self:
            plant_cost = rec.capacity_mw * rec.capital_cost_per_mw
            land_cost = rec.capacity_mw * rec.land_req_acre_per_mw * rec.land_cost_per_acre
            line_cost = rec.ss_distance_km * rec.transmission_line_cost_per_km
            misc_cost = rec.capacity_mw * rec.other_dev_cost_per_mw
            
            rec.solar_plant_cost_lakh = plant_cost
            rec.total_land_cost_lakh = land_cost
            rec.total_line_cost_lakh = line_cost
            rec.other_misc_expenses_lakh = misc_cost
            rec.total_cost_lakh = plant_cost + land_cost + line_cost + misc_cost

    @api.depends('capacity_mw', 'om_cost_per_mw')
    def _compute_om_cost_yr1(self):
        for rec in self:
            rec.om_cost_yr1 = rec.capacity_mw * rec.om_cost_per_mw

    @api.depends('om_cost_yr1', 'land_lease_cost_yr1')
    def _compute_total_maintenance(self):
        for rec in self:
            rec.total_maintenance_cost_lakh = rec.om_cost_yr1 + rec.land_lease_cost_yr1

    @api.depends('total_cost_lakh')
    def _compute_debt_equity(self):
        for rec in self:
            rec.debt_amount_lakh = rec.total_cost_lakh * 0.80
            rec.equity_amount_lakh = rec.total_cost_lakh * 0.20
            rec.principal_lakh = rec.debt_amount_lakh

    @api.depends('debt_amount_lakh', 'interest_rate_pct', 'tenure_years')
    def _compute_loan_emi(self):
        for rec in self:
            if rec.debt_amount_lakh > 0 and rec.interest_rate_pct > 0 and rec.tenure_years > 0:
                # Monthly PMT Formula: P * r * (1+r)^n / ((1+r)^n - 1)
                p = rec.debt_amount_lakh
                r = (rec.interest_rate_pct / 12.0) / 100.0
                n = rec.tenure_years * 12
                
                try:
                    monthly_emi = p * (r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)
                    rec.emi_amount_lakh = monthly_emi
                    rec.yearly_emi_lakh = monthly_emi * 12.0
                    rec.total_repayment_lakh = rec.yearly_emi_lakh * rec.tenure_years
                    rec.total_interest_paid_lakh = rec.total_repayment_lakh - rec.debt_amount_lakh
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

    # DISCOM Sync logic (defaults on DISCOM change)
    @api.onchange('discom_injection_id')
    def _onchange_discom_injection_id(self):
        if self.discom_injection_id:
            self.wheeling_loss_pct = self.discom_injection_id.wheeling_loss_pct
            self.wheeling_charge_rate = self.discom_injection_id.wheeling_rate
            self.trans_loss_pct = self.discom_injection_id.trans_loss_pct
            self.scheduling_charge_rate = self.discom_injection_id.scheduling_rate
            self.trans_charge_rate = self.discom_injection_id.trans_rate
            self.sec_wheeling_loss_pct = self.discom_injection_id.sec_wheeling_loss_pct
            self.sec_wheeling_charge_rate = self.discom_injection_id.sec_wheeling_rate
            self.banking_charge_rate = self.discom_injection_id.banking_rate

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.gm.proposal') or '/'
        records = super().create(vals_list)
        for rec in records:
            rec.action_recalculate_projections()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Recalculate projections on major calculation parameter change
        trigger_fields = [
            'capacity_mw', 'degradation_yr1', 'degradation_after_yr2', 'electricity_income_rate',
            'total_cost_lakh', 'yearly_emi_lakh', 'tenure_years', 'om_cost_yr1', 'om_increment_pct',
            'om_increment_interval', 'land_lease_cost_yr1', 'land_lease_increment_pct', 
            'land_lease_increment_interval', 'total_grid_charges_rs'
        ]
        if any(f in vals for f in trigger_fields):
            for rec in self:
                rec.action_recalculate_projections()
        return res

    def action_recalculate_projections(self):
        """Generates/Updates the 25-Year Projection lines for this proposal"""
        self.ensure_one()
        # Clean existing lines
        self.projection_line_ids.unlink()

        lines = []
        cumulative_income = 0.0

        # Calculations
        base_income_rate = self.electricity_income_rate
        # Year 1 degradation applies to capacity
        annual_gen_base = self.capacity_mw * 1000.0 * 4.0 * 365.0  # units (kWh) per year base

        for yr in range(1, 26):
            # 1. Received Units
            if yr == 1:
                received_units = annual_gen_base * (1.0 - self.degradation_yr1 / 100.0)
            else:
                prev_units = lines[-1]['received_units']
                received_units = prev_units * (1.0 - self.degradation_after_yr2 / 100.0)

            # 2. Rate per kWh (+1% yearly escalation)
            rate_kwh = base_income_rate * math.pow(1.01, yr - 1)

            # 3. Yly Revenue
            revenue = (received_units * rate_kwh) / 100000.0  # Convert Rs. to Lakh

            # 4. Grid Overhead Expenses (Wheeling escalates by 5% yearly, others constant)
            # Wheeling charge daily rate to yearly:
            daily_wheeling = self.wheeling_charge_rs
            yearly_wheeling = daily_wheeling * 365.0 * math.pow(1.05, yr - 1)
            
            # Other grid charges (Scheduling, Transmission, Sec Wheeling, Banking)
            daily_other_charges = (
                self.scheduling_charge_rs + self.trans_charge_rs + 
                self.sec_wheeling_charge_rs + self.banking_charge_rs
            )
            yearly_other = daily_other_charges * 365.0

            grid_expenses_lakh = (yearly_wheeling + yearly_other) / 100000.0

            # 5. O&M Cost (escalating at set intervals)
            om_escalations = math.floor((yr - 1) / self.om_increment_interval)
            om_exp = self.om_cost_yr1 * math.pow(1.0 + self.om_increment_pct / 100.0, om_escalations)

            # 6. Land Lease Cost (escalating at set intervals)
            lease_escalations = math.floor((yr - 1) / self.land_lease_increment_interval)
            land_lease = self.land_lease_cost_yr1 * math.pow(1.0 + self.land_lease_increment_pct / 100.0, lease_escalations)

            # 7. EMI (only during loan tenure)
            emi = self.yearly_emi_lakh if yr <= self.tenure_years else 0.0

            # 8. Net Income
            net_income = revenue - grid_expenses_lakh - om_exp - land_lease - emi

            # 9. GST Input Credit (Reverse GST component benefit simulation)
            # GST Component from Wheeling (18%) and other services (13.8% or standard GST)
            gst_component1 = (yearly_wheeling - (yearly_wheeling / 1.18)) / 100000.0
            gst_benefit = gst_component1

            # 10. Cumulative
            cumulative_income += (net_income + gst_benefit)

            lines.append({
                'proposal_id': self.id,
                'year': yr,
                'received_units': received_units,
                'rate_kwh': rate_kwh,
                'yearly_revenue': revenue,
                'grid_expenses': grid_expenses_lakh,
                'om_expenses': om_exp,
                'land_lease': land_lease,
                'emi': emi,
                'net_income': net_income,
                'gst_input_credit': gst_benefit,
                'cumulative_income': cumulative_income
            })

        # Batch create lines
        self.env['solar.gm.proposal.line'].create(lines)
        return True
