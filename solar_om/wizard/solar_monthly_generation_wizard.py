# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
import calendar

class SolarMonthlyGenerationWizard(models.TransientModel):
    _name = 'solar.monthly.generation.wizard'
    _description = 'Monthly Generation Report Wizard'

    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True)
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string='Month', required=True, default=lambda self: str(date.today().month))
    
    year = fields.Selection([
        (str(y), str(y)) for y in range(date.today().year - 5, date.today().year + 5)
    ], string='Year', required=True, default=lambda self: str(date.today().year))

    def action_print_pdf(self):
        self.ensure_one()
        data = {
            'plant_id': self.plant_id.id,
            'month': int(self.month),
            'year': int(self.year),
        }
        return self.env.ref('solar_om.action_report_solar_monthly_generation').report_action(self, data=data)


class ReportSolarMonthlyGeneration(models.AbstractModel):
    _name = 'report.solar_om.report_solar_monthly_generation_template'
    _description = 'Monthly Generation Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        plant_id = data.get('plant_id')
        month = data.get('month')
        year = data.get('year')

        plant = self.env['solar.plant'].browse(plant_id)
        
        # Calculate start and end date of target month
        last_day = calendar.monthrange(year, month)[1]
        date_from = date(year, month, 1)
        date_to = date(year, month, last_day)

        records = self.env['solar.daily.generation'].search([
            ('plant_id', '=', plant_id),
            ('date', '>=', date_from),
            ('date', '<=', date_to)
        ], order='date asc')

        total_energy = sum(records.mapped('energy_kwh'))
        total_revenue = sum(records.mapped('revenue'))

        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        return {
            'doc_ids': docids,
            'doc_model': 'solar.monthly.generation.wizard',
            'plant': plant,
            'month_name': month_names.get(month),
            'year': year,
            'records': records,
            'total_energy': total_energy,
            'total_revenue': total_revenue,
        }
