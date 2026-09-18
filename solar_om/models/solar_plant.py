# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SolarPlant(models.Model):
    _name = 'solar.plant'
    _description = 'Solar Plant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Plant Name', required=True, tracking=True)
    code = fields.Char(string='Plant Code', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    capacity = fields.Float(string='Capacity (kW)', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Client/Customer', required=True, tracking=True)
    
    # Address details
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='Zip/Postal Code')
    address = fields.Text(string='Full Address', compute='_compute_address', store=True)

    latitude = fields.Float(string='Latitude', digits=(9, 6), tracking=True)
    longitude = fields.Float(string='Longitude', digits=(9, 6), tracking=True)
    installation_date = fields.Date(string='Installation/Commission Date', required=True, tracking=True)
    warranty_expiry_date = fields.Date(string='Warranty Expiry Date', tracking=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft', required=True, tracking=True)

    manager_id = fields.Many2one('res.users', string='Manager', required=True, tracking=True)
    engineer_ids = fields.Many2many('res.users', 'solar_plant_engineer_rel', 'plant_id', 'user_id', string='Engineers', tracking=True)
    equipment_ids = fields.One2many('solar.equipment', 'plant_id', string='Related Equipment')
    price_per_unit = fields.Float(string='Price /Unit (Rs.)', default=0.0, tracking=True)
    discom_name = fields.Char(string='Discom Name', tracking=True)

    # Smart Button Counts
    maintenance_count = fields.Integer(string='Maintenance Count', compute='_compute_smart_button_counts')
    cleaning_count = fields.Integer(string='Cleaning Count', compute='_compute_smart_button_counts')
    breakdown_count = fields.Integer(string='Breakdown Count', compute='_compute_smart_button_counts')
    task_count = fields.Integer(string='Tasks Count', compute='_compute_smart_button_counts')
    generation_count = fields.Integer(string='Generation Logs Count', compute='_compute_smart_button_counts')
    sale_order_ids = fields.One2many('sale.order', 'solar_plant_id', string='Sales Orders')
    sale_order_count = fields.Integer(string='Sales Orders Count', compute='_compute_smart_button_counts')

    @api.depends('street', 'city', 'state_id', 'country_id', 'zip')
    def _compute_address(self):
        for record in self:
            parts = [record.street, record.city, record.state_id.name if record.state_id else '', record.zip, record.country_id.name if record.country_id else '']
            record.address = ", ".join([p for p in parts if p])

    def _compute_smart_button_counts(self):
        for record in self:
            record.maintenance_count = self.env['solar.maintenance'].search_count([('plant_id', '=', record.id)])
            record.cleaning_count = self.env['solar.cleaning'].search_count([('plant_id', '=', record.id)])
            record.breakdown_count = self.env['solar.breakdown'].search_count([('plant_id', '=', record.id)])
            record.task_count = self.env['solar.task'].search_count([('plant_id', '=', record.id)])
            record.generation_count = self.env['solar.daily.generation'].search_count([('plant_id', '=', record.id)])
            record.sale_order_count = self.env['sale.order'].search_count([('solar_plant_id', '=', record.id)]) if 'solar_plant_id' in self.env['sale.order']._fields else 0

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'name': _('Maintenance Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.maintenance',
            'view_mode': 'list,form',
            'domain': [('plant_id', '=', self.id)],
            'context': {'default_plant_id': self.id},
        }

    def action_view_cleaning(self):
        self.ensure_one()
        return {
            'name': _('Cleaning Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.cleaning',
            'view_mode': 'list,form',
            'domain': [('plant_id', '=', self.id)],
            'context': {'default_plant_id': self.id},
        }

    def action_view_breakdown(self):
        self.ensure_one()
        return {
            'name': _('Breakdown Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.breakdown',
            'view_mode': 'list,form',
            'domain': [('plant_id', '=', self.id)],
            'context': {'default_plant_id': self.id},
        }

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.task',
            'view_mode': 'list,form',
            'domain': [('plant_id', '=', self.id)],
            'context': {'default_plant_id': self.id},
        }

    def action_view_generation(self):
        self.ensure_one()
        return {
            'name': _('Daily Power Generation'),
            'type': 'ir.actions.act_window',
            'res_model': 'solar.daily.generation',
            'view_mode': 'list,form',
            'domain': [('plant_id', '=', self.id)],
            'context': {'default_plant_id': self.id},
        }

    def action_view_sales(self):
        self.ensure_one()
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('solar_plant_id', '=', self.id)],
            'context': {
                'default_solar_plant_id': self.id,
                'default_partner_id': self.customer_id.id if self.customer_id else False,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('solar.plant') or _('New')
        return super(SolarPlant, self).create(vals_list)

    @api.constrains('latitude', 'longitude')
    def _check_lat_long(self):
        for record in self:
            if record.latitude and not (-90.0 <= record.latitude <= 90.0):
                raise ValidationError(_('Latitude must be between -90 and 90.'))
            if record.longitude and not (-180.0 <= record.longitude <= 180.0):
                raise ValidationError(_('Longitude must be between -180 and 180.'))

    @api.model
    def get_dashboard_data(self):
        Plant = self.env['solar.plant']
        Maintenance = self.env['solar.maintenance']
        Breakdown = self.env['solar.breakdown']
        Cleaning = self.env['solar.cleaning']
        Task = self.env['solar.task']

        today = fields.Date.today()
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = fields.Datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        # KPIs
        total_plants = Plant.search_count([])
        active_plants = Plant.search_count([('status', '=', 'active')])

        today_maint = Maintenance.search_count([('date_due', '=', today)])
        today_cleaning = Cleaning.search_count([('create_date', '>=', today_start), ('create_date', '<=', today_end)])
        today_tasks = Task.search_count([('create_date', '>=', today_start), ('create_date', '<=', today_end)])
        todays_tasks_count = today_maint + today_cleaning + today_tasks

        pending_maint = Maintenance.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_breakdown = Breakdown.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_cleaning = Cleaning.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_tasks = Task.search_count([('state', 'in', ('draft', 'assigned', 'accepted', 'in_progress', 'waiting_approval'))])
        pending_tasks_count = pending_maint + pending_breakdown + pending_cleaning + pending_tasks

        comp_maint = Maintenance.search_count([('state', '=', 'completed')])
        comp_breakdown = Breakdown.search_count([('state', 'in', ('resolved', 'closed'))])
        comp_cleaning = Cleaning.search_count([('state', '=', 'completed')])
        comp_tasks = Task.search_count([('state', 'in', ('completed', 'closed'))])
        completed_tasks_count = comp_maint + comp_breakdown + comp_cleaning + comp_tasks

        breakdown_tickets = Breakdown.search_count([('state', 'in', ('draft', 'assigned', 'in_progress', 'resolved'))])
        cleaning_due = Cleaning.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])

        maint_engs = Maintenance.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        bd_engs = Breakdown.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        clean_engs = Cleaning.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        task_engs = Task.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        active_engineers = len(set(maint_engs + bd_engs + clean_engs + task_engs))

        # Chart 1: Cleaning Status
        cleaning_stats = {
            'completed': Cleaning.search_count([('state', '=', 'completed')]),
            'in_progress': Cleaning.search_count([('state', '=', 'in_progress')]),
            'assigned': Cleaning.search_count([('state', '=', 'assigned')]),
            'draft': Cleaning.search_count([('state', '=', 'draft')]),
        }

        # Chart 2: Task Completion (Est vs Act)
        done_maint = Maintenance.search([('state', '=', 'completed')], limit=10)
        task_completion = {
            'labels': done_maint.mapped('name'),
            'estimated': done_maint.mapped('estimated_hours'),
            'actual': done_maint.mapped('actual_hours'),
        }

        # Chart 3: Engineer Performance
        engineer_perf = {}
        for m in Maintenance.search([('state', '=', 'completed')]):
            if m.user_id:
                engineer_perf[m.user_id.name] = engineer_perf.get(m.user_id.name, 0) + 1
        for b in Breakdown.search([('state', 'in', ('resolved', 'closed'))]):
            if b.user_id:
                engineer_perf[b.user_id.name] = engineer_perf.get(b.user_id.name, 0) + 1
        for c in Cleaning.search([('state', '=', 'completed')]):
            if c.user_id:
                engineer_perf[c.user_id.name] = engineer_perf.get(c.user_id.name, 0) + 1
        for t in Task.search([('state', 'in', ('completed', 'closed'))]):
            if t.user_id:
                engineer_perf[t.user_id.name] = engineer_perf.get(t.user_id.name, 0) + 1

        engineer_performance = {
            'labels': list(engineer_perf.keys())[:10],
            'data': list(engineer_perf.values())[:10],
        }

        # Recent activities
        recent_activities = []
        m_records = Maintenance.search([], order='write_date desc', limit=3)
        b_records = Breakdown.search([], order='write_date desc', limit=3)
        c_records = Cleaning.search([], order='write_date desc', limit=3)
        t_records = Task.search([], order='write_date desc', limit=3)

        for m in m_records:
            recent_activities.append({
                'type': 'maintenance',
                'name': m.name,
                'desc': 'Maintenance status: %s' % m.state,
                'date': m.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for b in b_records:
            recent_activities.append({
                'type': 'breakdown',
                'name': b.name,
                'desc': 'Breakdown status: %s' % b.state,
                'date': b.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for c in c_records:
            recent_activities.append({
                'type': 'cleaning',
                'name': c.name,
                'desc': 'Cleaning status: %s' % c.state,
                'date': c.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for t in t_records:
            recent_activities.append({
                'type': 'task',
                'name': t.name,
                'desc': 'Task status: %s' % t.state,
                'date': t.write_date.strftime('%Y-%m-%d %H:%M'),
            })

        recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:6]

        return {
            'kpis': {
                'total_plants': total_plants,
                'active_plants': active_plants,
                'todays_tasks': todays_tasks_count,
                'pending_tasks': pending_tasks_count,
                'completed_tasks': completed_tasks_count,
                'breakdown_tickets': breakdown_tickets,
                'cleaning_due': cleaning_due,
                'active_engineers': active_engineers,
            },
            'cleaning_stats': cleaning_stats,
            'task_completion': task_completion,
            'engineer_performance': engineer_performance,
            'recent_activities': recent_activities,
        }



class SolarEquipmentCategory(models.Model):
    _name = 'solar.equipment.category'
    _description = 'Solar Equipment Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')


class SolarEquipment(models.Model):
    _name = 'solar.equipment'
    _description = 'Solar Equipment'
    _order = 'name'

    name = fields.Char(string='Equipment Name', required=True)
    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, ondelete='cascade')
    category_id = fields.Many2one('solar.equipment.category', string='Category', required=True)
    serial_number = fields.Char(string='Serial Number')
    installation_date = fields.Date(string='Installation Date')
    status = fields.Selection([
        ('operational', 'Operational'),
        ('faulty', 'Faulty'),
        ('maintenance', 'Under Maintenance'),
        ('decommissioned', 'Decommissioned')
    ], string='Status', default='operational', required=True)


class SolarMaintenanceType(models.Model):
    _name = 'solar.maintenance.type'
    _description = 'Solar Maintenance Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')


class SolarCleaningType(models.Model):
    _name = 'solar.cleaning.type'
    _description = 'Solar Cleaning Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')


class SolarChecklistTemplate(models.Model):
    _name = 'solar.checklist.template'
    _description = 'Solar Checklist Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('preventive', 'Preventive Maintenance'),
        ('breakdown', 'Breakdown Maintenance'),
        ('cleaning', 'Cleaning')
    ], string='Category', required=True, default='preventive')
    line_ids = fields.One2many('solar.checklist.template.line', 'template_id', string='Checklist Items')


class SolarChecklistTemplateLine(models.Model):
    _name = 'solar.checklist.template.line'
    _description = 'Solar Checklist Template Line'
    _order = 'sequence, id'

    template_id = fields.Many2one('solar.checklist.template', string='Template', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Checklist Item Name', required=True)


class SolarIssueType(models.Model):
    _name = 'solar.issue.type'
    _description = 'Solar Issue Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')


class SolarPriority(models.Model):
    _name = 'solar.priority'
    _description = 'Solar Priority'
    _order = 'sequence, id'

    name = fields.Char(string='Priority Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)


class SolarFailureReason(models.Model):
    _name = 'solar.failure.reason'
    _description = 'Solar Failure Reason'
    _order = 'name'

    name = fields.Char(string='Failure Reason', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')


class SolarTaskStage(models.Model):
    _name = 'solar.task.stage'
    _description = 'Solar Task Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('waiting_approval', 'Waiting Approval'),
        ('completed', 'Completed'),
        ('closed', 'Closed')
    ], string='State', required=True, default='draft')
