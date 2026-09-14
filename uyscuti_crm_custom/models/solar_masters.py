from odoo import models, fields

class SolarDiscom(models.Model):
    _name = 'solar.discom'
    _description = 'Solar Discom'
    
    name = fields.Char(string='Name', required=True)
    fee_ids = fields.One2many('solar.discom.fee', 'discom_id', string='Fee Rules')

class SolarDiscomFee(models.Model):
    _name = 'solar.discom.fee'
    _description = 'Solar Discom Fee Rule'

    discom_id = fields.Many2one('solar.discom', ondelete='cascade')
    sanction_phase = fields.Selection([('1ph', '1PH'), ('3ph', '3PH')], string='Sanction Load Phase', required=True)
    load_phase = fields.Selection([('1ph', '1PH'), ('3ph', '3PH')], string='Solar Load Phase', required=True)
    min_kw = fields.Float(string='Min KW', default=0.0)
    max_kw = fields.Float(string='Max KW', default=9999.0)
    fee = fields.Float(string='Discom Fee', required=True)

class SolarSystemStrengthConfig(models.Model):
    _name = 'solar.system.strength.config'
    _description = 'Solar System Strength Configuration'
    _order = 'min_kw'

    name = fields.Char(string='Description')
    min_kw = fields.Float(string='Min KW', required=True)
    max_kw = fields.Float(string='Max KW', required=True)
    fixed_fee = fields.Float(string='Fixed Fee')
    per_kw_fee = fields.Float(string='Per KW Fee')

class SolarTerraceType(models.Model):
    _name = 'solar.terrace.type'
    _description = 'Solar Terrace Type'
    
    name = fields.Char(string='Name', required=True)

class SolarModuleMake(models.Model):
    _name = 'solar.module.make'
    _description = 'Solar Module Make'
    
    name = fields.Char(string='Name', required=True)

class SolarModuleType(models.Model):
    _name = 'solar.module.type'
    _description = 'Solar Module Type'
    
    name = fields.Char(string='Name', required=True)

class SolarModuleWp(models.Model):
    _name = 'solar.module.wp'
    _description = 'Solar Module WP'
    
    name = fields.Char(string='Name', required=True)
