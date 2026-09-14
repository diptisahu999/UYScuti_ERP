from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class TestSolarFinancials(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSolarFinancials, cls).setUpClass()

        # Create a partner for the consumer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Solar Consumer',
            'email': 'consumer@test.com',
            'phone': '1234567890'
        })

        # Create a solar project
        cls.project = cls.env['solar.project'].create({
            'partner_id': cls.partner.id,
            'kw_capacity': 100.0,
            'project_type': 'commercial'
        })

    def test_financial_projections(self):
        """Test calculation of EMI, Projections, IRR and ROI"""
        financials = self.env['solar.financials'].create({
            'project_id': self.project.id,
            'annual_yield_per_kw': 1700.0,
            'total_cost_lakh': 40.0,
            'equity_pct': 20.0,
            'debt_pct': 80.0,
            'interest_rate_pct': 9.5,
            'tenure_years': 10,
            'om_cost_yr1_lakh': 1.0,
            'om_escalation_pct': 3.5,
            'tariff_rate': 8.85,
            'tariff_escalation_pct': 1.0,
            'degradation_yr2_pct': 2.5,
            'degradation_subsequent_pct': 0.7,
            'has_subsidy': False
        })

        self.assertAlmostEqual(financials.equity_amount_lakh, 8.0)
        self.assertAlmostEqual(financials.debt_amount_lakh, 32.0)
        self.assertTrue(financials.emi_amount_lakh > 0)
        self.assertAlmostEqual(financials.yearly_emi_lakh, financials.emi_amount_lakh * 12.0)

        financials.action_recalculate_projections()
        self.assertEqual(len(financials.cashflow_line_ids), 25)

        y1_line = financials.cashflow_line_ids.filtered(lambda l: l.year == 1)
        self.assertAlmostEqual(y1_line.generation_units, 170000.0)
        self.assertAlmostEqual(y1_line.tariff_rate, 8.85)
        self.assertAlmostEqual(y1_line.revenue_lakh, 15.045)
        self.assertAlmostEqual(y1_line.om_expenses_lakh, 1.0)
        self.assertAlmostEqual(y1_line.emi_expenses_lakh, financials.yearly_emi_lakh, places=4)

        y2_line = financials.cashflow_line_ids.filtered(lambda l: l.year == 2)
        self.assertAlmostEqual(y2_line.generation_units, 170000.0 * 0.975)
        
        y3_line = financials.cashflow_line_ids.filtered(lambda l: l.year == 3)
        self.assertAlmostEqual(y3_line.generation_units, 170000.0 * 0.975 * 0.993)

        self.assertTrue(financials.total_net_profit_lakh > 0)
        self.assertTrue(financials.roi_pct > 0)
        self.assertTrue(financials.irr_pct > 0)
