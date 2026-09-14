# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import datetime

class SolarOMDashboardController(http.Controller):

    @http.route('/solar_om/dashboard_data', type='json', auth='user')
    def get_dashboard_data(self):
        # Base models envs
        Plant = request.env['solar.plant']
        Maintenance = request.env['solar.maintenance']
        Breakdown = request.env['solar.breakdown']
        Cleaning = request.env['solar.cleaning']
        Task = request.env['solar.task']
        User = request.env['res.users']

        today = fields.Date.today()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)

        # 1. KPI Calculation
        total_plants = Plant.search_count([])
        active_plants = Plant.search_count([('status', '=', 'active')])

        # Today's tasks (due today or scheduled/completed today)
        today_maint = Maintenance.search_count([('date_due', '=', today)])
        today_cleaning = Cleaning.search_count([('create_date', '>=', today_start), ('create_date', '<=', today_end)])
        today_tasks = Task.search_count([('create_date', '>=', today_start), ('create_date', '<=', today_end)])
        todays_tasks_count = today_maint + today_cleaning + today_tasks

        # Pending Tasks (all task models not completed/closed/cancelled)
        pending_maint = Maintenance.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_breakdown = Breakdown.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_cleaning = Cleaning.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])
        pending_tasks = Task.search_count([('state', 'in', ('draft', 'assigned', 'accepted', 'in_progress', 'waiting_approval'))])
        pending_tasks_count = pending_maint + pending_breakdown + pending_cleaning + pending_tasks

        # Completed Tasks
        comp_maint = Maintenance.search_count([('state', '=', 'completed')])
        comp_breakdown = Breakdown.search_count([('state', 'in', ('resolved', 'closed'))])
        comp_cleaning = Cleaning.search_count([('state', '=', 'completed')])
        comp_tasks = Task.search_count([('state', 'in', ('completed', 'closed'))])
        completed_tasks_count = comp_maint + comp_breakdown + comp_cleaning + comp_tasks

        # Active Breakdown tickets
        breakdown_tickets = Breakdown.search_count([('state', 'in', ('draft', 'assigned', 'in_progress', 'resolved'))])

        # Cleaning Due
        cleaning_due = Cleaning.search_count([('state', 'in', ('draft', 'assigned', 'in_progress'))])

        # Active Engineers (engineers assigned to in_progress tasks)
        maint_engs = Maintenance.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        bd_engs = Breakdown.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        clean_engs = Cleaning.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        task_engs = Task.search([('state', '=', 'in_progress')]).mapped('user_id.id')
        active_engineers = len(set(maint_engs + bd_engs + clean_engs + task_engs))

        # 2. Charts Data
        # Cleaning Status Breakdown
        cleaning_stats = {
            'completed': Cleaning.search_count([('state', '=', 'completed')]),
            'in_progress': Cleaning.search_count([('state', '=', 'in_progress')]),
            'assigned': Cleaning.search_count([('state', '=', 'assigned')]),
            'draft': Cleaning.search_count([('state', '=', 'draft')]),
        }

        # Task completion (Estimated vs Actual Hours)
        done_maint = Maintenance.search([('state', '=', 'completed')], limit=10)
        task_completion = {
            'labels': done_maint.mapped('name'),
            'estimated': done_maint.mapped('estimated_hours'),
            'actual': done_maint.mapped('actual_hours'),
        }

        # Engineer Performance (number of completed/closed tasks)
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

        # Recent activities (last 5 O&M events)
        recent_activities = []
        # fetch latest records
        m_records = Maintenance.search([], order='write_date desc', limit=3)
        b_records = Breakdown.search([], order='write_date desc', limit=3)
        c_records = Cleaning.search([], order='write_date desc', limit=3)
        t_records = Task.search([], order='write_date desc', limit=3)

        for m in m_records:
            recent_activities.append({
                'type': 'maintenance',
                'name': m.name,
                'desc': 'Maintenance task updated to %s' % m.state,
                'date': m.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for b in b_records:
            recent_activities.append({
                'type': 'breakdown',
                'name': b.name,
                'desc': 'Breakdown ticket updated to %s' % b.state,
                'date': b.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for c in c_records:
            recent_activities.append({
                'type': 'cleaning',
                'name': c.name,
                'desc': 'Cleaning task updated to %s' % c.state,
                'date': c.write_date.strftime('%Y-%m-%d %H:%M'),
            })
        for t in t_records:
            recent_activities.append({
                'type': 'task',
                'name': t.name,
                'desc': 'General task updated to %s' % t.state,
                'date': t.write_date.strftime('%Y-%m-%d %H:%M'),
            })

        # Sort activities by date
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
