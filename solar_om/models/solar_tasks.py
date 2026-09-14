# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

_logger = logging.getLogger(__name__)


def _send_solar_task_push(record, event_type, task_label, icon_prefix=""):
    """
    Helper to send push notifications safely via push.service.
    event_type: 'assigned' or 'completed'
    """
    try:
        if 'push.service' not in record.env:
            return

        push_service = record.env['push.service'].sudo()
        plant_name = record.plant_id.name if record.plant_id else 'Solar Plant'
        task_name = record.name or 'Task'
        current_user = record.env.user

        if event_type == 'assigned':
            # 1. Notify Assigned User
            if record.user_id:
                title = f"{icon_prefix}{task_label} Assigned: {task_name}"
                body = f"You have been assigned to {task_label.lower()} '{task_name}' at {plant_name}."
                push_service.send_to_user(
                    user_id=record.user_id.id,
                    title=title,
                    body=body,
                    data={
                        "model": record._name,
                        "res_id": str(record.id),
                        "type": "solar_task_assigned"
                    }
                )

            # 2. Notify Manager / Creator (if different from assigned user and current user)
            managers = set()
            if record.plant_id and record.plant_id.manager_id:
                managers.add(record.plant_id.manager_id)
            if record.create_uid:
                managers.add(record.create_uid)

            for manager in managers:
                if (not record.user_id or manager.id != record.user_id.id) and manager.id != current_user.id:
                    mgr_title = f"📌 {task_label} Assigned: {task_name}"
                    mgr_body = f"{task_label} '{task_name}' at {plant_name} assigned to {record.user_id.name if record.user_id else 'Unassigned'}."
                    push_service.send_to_user(
                        user_id=manager.id,
                        title=mgr_title,
                        body=mgr_body,
                        data={
                            "model": record._name,
                            "res_id": str(record.id),
                            "type": "solar_task_created"
                        }
                    )

        elif event_type == 'completed':
            # Notify Manager / Creator that task was completed
            managers = set()
            if record.plant_id and record.plant_id.manager_id:
                managers.add(record.plant_id.manager_id)
            if record.create_uid:
                managers.add(record.create_uid)

            completed_by = current_user.name
            for manager in managers:
                if manager.id != current_user.id:
                    mgr_title = f"✅ {task_label} Completed: {task_name}"
                    mgr_body = f"{task_label} '{task_name}' at {plant_name} was marked as completed by {completed_by}."
                    push_service.send_to_user(
                        user_id=manager.id,
                        title=mgr_title,
                        body=mgr_body,
                        data={
                            "model": record._name,
                            "res_id": str(record.id),
                            "type": "solar_task_completed"
                        }
                    )
    except Exception as e:
        _logger.warning("Failed to send push notification for %s (%s): %s", record._name, record.id, e)

class SolarTaskChecklistLine(models.Model):
    _name = 'solar.task.checklist.line'
    _description = 'Task Checklist Line'
    _order = 'id'

    name = fields.Char(string='Checklist Item Name', required=True)
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A')
    ], string='Status', default='na', required=True)
    remarks = fields.Char(string='Remarks')
    photo = fields.Binary(string='Photo', attachment=True)

    maintenance_id = fields.Many2one('solar.maintenance', string='Maintenance Task', ondelete='cascade')
    cleaning_id = fields.Many2one('solar.cleaning', string='Cleaning Task', ondelete='cascade')
    task_id = fields.Many2one('solar.task', string='General Task', ondelete='cascade')


class SolarMaintenance(models.Model):
    _name = 'solar.maintenance'
    _description = 'Preventive Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Maintenance Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, tracking=True)
    equipment_id = fields.Many2one('solar.equipment', string='Equipment', domain="[('plant_id', '=', plant_id)]", tracking=True)
    maintenance_type_id = fields.Many2one('solar.maintenance.type', string='Maintenance Type', tracking=True)
    checklist_template_id = fields.Many2one('solar.checklist.template', string='Checklist Template', domain="[('category', '=', 'preventive')]", tracking=True)
    checklist_line_ids = fields.One2many('solar.task.checklist.line', 'maintenance_id', string='Checklist Lines')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True)
    
    date_due = fields.Date(string='Due Date', required=True, default=lambda self: fields.Date.today() + timedelta(days=7), tracking=True)
    user_id = fields.Many2one('res.users', string='Assigned Engineer', tracking=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)
    actual_hours = fields.Float(string='Actual Hours', compute='_compute_actual_hours', store=True, tracking=True)
    remarks = fields.Text(string='Remarks')
    signature = fields.Binary(string='Digital Signature', attachment=True)
    date_completed = fields.Datetime(string='Completion Date', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # Time tracking helper fields
    time_start = fields.Datetime(string='Start Time')
    time_pause = fields.Datetime(string='Pause Time')
    time_spend = fields.Float(string='Time Spent (Hours)', default=0.0)
    is_paused = fields.Boolean(string='Is Paused', default=False)

    @api.depends('time_spend')
    def _compute_actual_hours(self):
        for record in self:
            record.actual_hours = record.time_spend

    @api.onchange('checklist_template_id')
    def _onchange_checklist_template(self):
        if self.checklist_template_id:
            lines = []
            for item in self.checklist_template_id.line_ids:
                lines.append((0, 0, {
                    'name': item.name,
                    'status': 'na',
                }))
            self.checklist_line_ids = [(5, 0, 0)] + lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.maintenance') or _('New')
        records = super(SolarMaintenance, self).create(vals_list)
        for record in records:
            if record.user_id:
                _send_solar_task_push(record, 'assigned', 'Maintenance Task', '🔧 ')
        return records

    def write(self, vals):
        old_users = {r.id: r.user_id.id for r in self} if 'user_id' in vals else {}
        old_states = {r.id: r.state for r in self} if 'state' in vals else {}
        res = super(SolarMaintenance, self).write(vals)
        if 'user_id' in vals:
            for r in self:
                if r.user_id and r.user_id.id != old_users.get(r.id):
                    _send_solar_task_push(r, 'assigned', 'Maintenance Task', '🔧 ')
        if 'state' in vals and vals.get('state') == 'completed':
            for r in self:
                if old_states.get(r.id) != 'completed':
                    _send_solar_task_push(r, 'completed', 'Maintenance Task', '✅ ')
        return res

    def action_start(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'time_start': fields.Datetime.now(),
            'is_paused': False
        })

    def action_pause(self):
        self.ensure_one()
        if self.state == 'in_progress' and not self.is_paused:
            now = fields.Datetime.now()
            duration = 0.0
            if self.time_start:
                diff = now - self.time_start
                duration = diff.total_seconds() / 3600.0
            self.write({
                'time_pause': now,
                'is_paused': True,
                'time_spend': self.time_spend + duration
            })

    def action_resume(self):
        self.ensure_one()
        if self.state == 'in_progress' and self.is_paused:
            self.write({
                'time_start': fields.Datetime.now(),
                'is_paused': False
            })

    def action_complete(self):
        self.ensure_one()
        duration = 0.0
        now = fields.Datetime.now()
        if self.state == 'in_progress' and not self.is_paused and self.time_start:
            diff = now - self.time_start
            duration = diff.total_seconds() / 3600.0
        
        self.write({
            'state': 'completed',
            'time_spend': self.time_spend + duration,
            'is_paused': False,
            'date_completed': now
        })


class SolarBreakdown(models.Model):
    _name = 'solar.breakdown'
    _description = 'Breakdown Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Ticket Number', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, tracking=True)
    equipment_id = fields.Many2one('solar.equipment', string='Equipment', domain="[('plant_id', '=', plant_id)]", tracking=True)
    issue_type_id = fields.Many2one('solar.issue.type', string='Issue Category', tracking=True)
    description = fields.Text(string='Issue Description')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True)

    user_id = fields.Many2one('res.users', string='Assigned Engineer', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    resolution = fields.Text(string='Resolution Remarks')
    downtime = fields.Float(string='Downtime (Hours)', tracking=True)
    failure_reason_id = fields.Many2one('solar.failure.reason', string='Root Cause / Failure Reason', tracking=True)
    corrective_action = fields.Text(string='Corrective Action')
    sla_deadline = fields.Datetime(string='SLA Deadline', required=True, default=lambda self: fields.Datetime.now() + timedelta(hours=24), tracking=True)
    escalated_to_id = fields.Many2one('res.users', string='Escalated To', tracking=True)

    # Time tracking helper fields
    time_start = fields.Datetime(string='Start Time')
    time_pause = fields.Datetime(string='Pause Time')
    time_spend = fields.Float(string='Total Work Hours', default=0.0)
    is_paused = fields.Boolean(string='Is Paused', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.breakdown') or _('New')
        records = super(SolarBreakdown, self).create(vals_list)
        for record in records:
            if record.user_id:
                _send_solar_task_push(record, 'assigned', 'Breakdown Ticket', '⚡ ')
        return records

    def write(self, vals):
        old_users = {r.id: r.user_id.id for r in self} if 'user_id' in vals else {}
        old_states = {r.id: r.state for r in self} if 'state' in vals else {}
        res = super(SolarBreakdown, self).write(vals)
        if 'user_id' in vals:
            for r in self:
                if r.user_id and r.user_id.id != old_users.get(r.id):
                    _send_solar_task_push(r, 'assigned', 'Breakdown Ticket', '⚡ ')
        if 'state' in vals and vals.get('state') in ('resolved', 'closed'):
            for r in self:
                if old_states.get(r.id) not in ('resolved', 'closed'):
                    _send_solar_task_push(r, 'completed', 'Breakdown Ticket', '✅ ')
        return res

    def action_start(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'time_start': fields.Datetime.now(),
            'is_paused': False
        })

    def action_pause(self):
        self.ensure_one()
        if self.state == 'in_progress' and not self.is_paused:
            now = fields.Datetime.now()
            duration = 0.0
            if self.time_start:
                diff = now - self.time_start
                duration = diff.total_seconds() / 3600.0
            self.write({
                'time_pause': now,
                'is_paused': True,
                'time_spend': self.time_spend + duration
            })

    def action_resume(self):
        self.ensure_one()
        if self.state == 'in_progress' and self.is_paused:
            self.write({
                'time_start': fields.Datetime.now(),
                'is_paused': False
            })

    def action_resolve(self):
        self.ensure_one()
        duration = 0.0
        now = fields.Datetime.now()
        if self.state == 'in_progress' and not self.is_paused and self.time_start:
            diff = now - self.time_start
            duration = diff.total_seconds() / 3600.0
        
        self.write({
            'state': 'resolved',
            'time_spend': self.time_spend + duration,
            'is_paused': False
        })

    def action_close(self):
        self.ensure_one()
        if not self.env.user.has_group('solar_om.group_solar_om_manager') and not self.env.user.has_group('solar_om.group_solar_om_admin'):
            raise ValidationError(_("Only O&M Managers or Admins can close breakdown tickets."))
        self.write({'state': 'closed'})


class SolarCleaning(models.Model):
    _name = 'solar.cleaning'
    _description = 'Cleaning Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Cleaning Ref', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, tracking=True)
    cleaning_type_id = fields.Many2one('solar.cleaning.type', string='Cleaning Type', tracking=True)
    frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('manual', 'Manual')
    ], string='Frequency', default='weekly', required=True, tracking=True)
    
    user_id = fields.Many2one('res.users', string='Assigned Engineer', tracking=True)
    checklist_template_id = fields.Many2one('solar.checklist.template', string='Checklist Template', domain="[('category', '=', 'cleaning')]", tracking=True)
    checklist_line_ids = fields.One2many('solar.task.checklist.line', 'cleaning_id', string='Checklist Lines')
    water_consumption = fields.Float(string='Water Consumption (Liters)', tracking=True)
    remarks = fields.Text(string='Remarks')
    
    before_image = fields.Binary(string='Before Image', attachment=True)
    after_image = fields.Binary(string='After Image', attachment=True)
    completion_time = fields.Datetime(string='Completion Time', tracking=True)
    latitude = fields.Float(string='Geo Latitude', digits=(9, 6), tracking=True)
    longitude = fields.Float(string='Geo Longitude', digits=(9, 6), tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # Time tracking helper fields
    time_start = fields.Datetime(string='Start Time')
    time_pause = fields.Datetime(string='Pause Time')
    time_spend = fields.Float(string='Total Cleaning Hours', default=0.0)
    is_paused = fields.Boolean(string='Is Paused', default=False)

    @api.onchange('checklist_template_id')
    def _onchange_checklist_template(self):
        if self.checklist_template_id:
            lines = []
            for item in self.checklist_template_id.line_ids:
                lines.append((0, 0, {
                    'name': item.name,
                    'status': 'na',
                }))
            self.checklist_line_ids = [(5, 0, 0)] + lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.cleaning') or _('New')
        records = super(SolarCleaning, self).create(vals_list)
        for record in records:
            if record.user_id:
                _send_solar_task_push(record, 'assigned', 'Cleaning Task', '🧹 ')
        return records

    def write(self, vals):
        old_users = {r.id: r.user_id.id for r in self} if 'user_id' in vals else {}
        old_states = {r.id: r.state for r in self} if 'state' in vals else {}
        res = super(SolarCleaning, self).write(vals)
        if 'user_id' in vals:
            for r in self:
                if r.user_id and r.user_id.id != old_users.get(r.id):
                    _send_solar_task_push(r, 'assigned', 'Cleaning Task', '🧹 ')
        if 'state' in vals and vals.get('state') == 'completed':
            for r in self:
                if old_states.get(r.id) != 'completed':
                    _send_solar_task_push(r, 'completed', 'Cleaning Task', '✅ ')
        return res

    def action_start(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'time_start': fields.Datetime.now(),
            'is_paused': False
        })

    def action_pause(self):
        self.ensure_one()
        if self.state == 'in_progress' and not self.is_paused:
            now = fields.Datetime.now()
            duration = 0.0
            if self.time_start:
                diff = now - self.time_start
                duration = diff.total_seconds() / 3600.0
            self.write({
                'time_pause': now,
                'is_paused': True,
                'time_spend': self.time_spend + duration
            })

    def action_resume(self):
        self.ensure_one()
        if self.state == 'in_progress' and self.is_paused:
            self.write({
                'time_start': fields.Datetime.now(),
                'is_paused': False
            })

    def action_complete(self):
        self.ensure_one()
        duration = 0.0
        now = fields.Datetime.now()
        if self.state == 'in_progress' and not self.is_paused and self.time_start:
            diff = now - self.time_start
            duration = diff.total_seconds() / 3600.0
        
        self.write({
            'state': 'completed',
            'time_spend': self.time_spend + duration,
            'is_paused': False,
            'completion_time': now,
            # coordinates should be captured in mobile screen/controller
        })


class SolarTask(models.Model):
    _name = 'solar.task'
    _description = 'General Solar Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Task Number', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Assigned Engineer', tracking=True)
    checklist_template_id = fields.Many2one('solar.checklist.template', string='Checklist Template', tracking=True)
    checklist_line_ids = fields.One2many('solar.task.checklist.line', 'task_id', string='Checklist Lines')
    remarks = fields.Text(string='Remarks')
    signature = fields.Binary(string='Digital Signature', attachment=True)
    latitude = fields.Float(string='Geo Latitude', digits=(9, 6), tracking=True)
    longitude = fields.Float(string='Geo Longitude', digits=(9, 6), tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('waiting_approval', 'Waiting Approval'),
        ('completed', 'Completed'),
        ('closed', 'Closed')
    ], string='Status', default='draft', required=True, tracking=True)

    # Time tracking helper fields
    time_start = fields.Datetime(string='Start Time')
    time_pause = fields.Datetime(string='Pause Time')
    time_spend = fields.Float(string='Time Spent (Hours)', default=0.0)
    is_paused = fields.Boolean(string='Is Paused', default=False)

    @api.onchange('checklist_template_id')
    def _onchange_checklist_template(self):
        if self.checklist_template_id:
            lines = []
            for item in self.checklist_template_id.line_ids:
                lines.append((0, 0, {
                    'name': item.name,
                    'status': 'na',
                }))
            self.checklist_line_ids = [(5, 0, 0)] + lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.task') or _('New')
        records = super(SolarTask, self).create(vals_list)
        for record in records:
            if record.user_id:
                _send_solar_task_push(record, 'assigned', 'Solar Task', '☀️ ')
        return records

    def write(self, vals):
        old_users = {r.id: r.user_id.id for r in self} if 'user_id' in vals else {}
        old_states = {r.id: r.state for r in self} if 'state' in vals else {}
        res = super(SolarTask, self).write(vals)
        if 'user_id' in vals:
            for r in self:
                if r.user_id and r.user_id.id != old_users.get(r.id):
                    _send_solar_task_push(r, 'assigned', 'Solar Task', '☀️ ')
        if 'state' in vals and vals.get('state') in ('waiting_approval', 'completed', 'closed'):
            for r in self:
                if old_states.get(r.id) not in ('waiting_approval', 'completed', 'closed'):
                    _send_solar_task_push(r, 'completed', 'Solar Task', '✅ ')
        return res

    def action_assign(self):
        self.ensure_one()
        if not self.user_id:
            raise ValidationError(_("Please assign an engineer first."))
        self.write({'state': 'assigned'})

    def action_accept(self):
        self.ensure_one()
        self.write({'state': 'accepted'})

    def action_start(self):
        self.ensure_one()
        if self.state in ('accepted', 'assigned'):
            self.write({
                'state': 'in_progress',
                'time_start': fields.Datetime.now(),
                'is_paused': False
            })

    def action_pause(self):
        self.ensure_one()
        if self.state == 'in_progress' and not self.is_paused:
            now = fields.Datetime.now()
            duration = 0.0
            if self.time_start:
                diff = now - self.time_start
                duration = diff.total_seconds() / 3600.0
            self.write({
                'time_pause': now,
                'is_paused': True,
                'time_spend': self.time_spend + duration
            })

    def action_resume(self):
        self.ensure_one()
        if self.state == 'in_progress' and self.is_paused:
            self.write({
                'time_start': fields.Datetime.now(),
                'is_paused': False
            })

    def action_complete(self):
        self.ensure_one()
        duration = 0.0
        now = fields.Datetime.now()
        if self.state == 'in_progress' and not self.is_paused and self.time_start:
            diff = now - self.time_start
            duration = diff.total_seconds() / 3600.0
        
        self.write({
            'state': 'waiting_approval',
            'time_spend': self.time_spend + duration,
            'is_paused': False
        })

    def action_approve(self):
        self.ensure_one()
        if not self.env.user.has_group('solar_om.group_solar_om_manager') and not self.env.user.has_group('solar_om.group_solar_om_admin'):
            raise ValidationError(_("Only O&M Managers or Admins can approve and close tasks."))
        self.write({'state': 'completed'})

    def action_close(self):
        self.ensure_one()
        if not self.env.user.has_group('solar_om.group_solar_om_manager') and not self.env.user.has_group('solar_om.group_solar_om_admin'):
            raise ValidationError(_("Only O&M Managers or Admins can approve and close tasks."))
        self.write({'state': 'closed'})
