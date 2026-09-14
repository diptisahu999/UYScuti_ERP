# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError
from datetime import timedelta

class ProjectTask(models.Model):
    _inherit = "project.task"

    # Relabel '03_approved' state to 'Approval' so Users use it for task status updates
    state = fields.Selection(
        selection_add=[('03_approved', 'Approval')],
        ondelete={'03_approved': 'set default'}
    )

    # Define the new field
    x_days_left_display = fields.Char(
        string="Time Left (Excl. Sundays)",
        compute='_compute_days_left_display',
        store=False,  # This ensures it recalculates on every page load
    )

    @api.depends('date_deadline')
    def _compute_days_left_display(self):
        """
        Calculates the remaining workdays (excluding Sundays) 
        until the deadline.
        """
        today = fields.Date.today()
        
        for task in self:
            if not task.date_deadline:
                task.x_days_left_display = "No Deadline Set"
                continue

            deadline = task.date_deadline.date()
            
            if deadline < today:
                task.x_days_left_display = "Deadline Passed"
                continue

            # Loop from today until the deadline, counting non-Sundays
            days_left_count = 0
            current_date = today
            
            while current_date < deadline:
                # date.weekday() returns 0 for Monday and 6 for Sunday
                if current_date.weekday() != 6:  # 6 is Sunday
                    days_left_count += 1
                
                # Move to the next day
                current_date += timedelta(days=1)
            
            # Format the display string
            if days_left_count == 1:
                task.x_days_left_display = f"{days_left_count} day left"
            else:
                task.x_days_left_display = f"{days_left_count} days left"

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        """
        Override get_view to hide the 'Done' state from the selection list
        for users with 'User' access role (only Managers & Admins can see/set 'Done').
        """
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        user = self.env.user
        is_manager_or_admin = user.has_group('project_task_library.group_project_custom_manager') or user.has_group('project.group_project_manager')

        if 'state' in res.get('fields', {}) and not is_manager_or_admin:
            selection = res['fields']['state']['selection']
            # Filter out '1_done' from selection list for Users
            new_selection = [item for item in selection if item[0] != '1_done']
            res['fields']['state']['selection'] = new_selection

        return res

import logging

_logger = logging.getLogger(__name__)


def _send_project_task_push(task, event_type, new_users=None):
    try:
        if 'push.service' not in task.env:
            return

        push_service = task.env['push.service'].sudo()
        project_name = task.project_id.name if task.project_id else 'General Project'
        task_name = task.name or 'Task'
        current_user = task.env.user

        # Identify managers: project manager and creator
        managers = set()
        if task.project_id and task.project_id.user_id:
            managers.add(task.project_id.user_id)
        if task.create_uid:
            managers.add(task.create_uid)

        if event_type == 'assigned':
            target_users = new_users if new_users is not None else task.user_ids
            # 1. Notify Assigned Users
            for user in target_users:
                title = f"📋 Project Task Assigned: {task_name}"
                body = f"You have been assigned to task '{task_name}' in project '{project_name}'."
                push_service.send_to_user(
                    user_id=user.id,
                    title=title,
                    body=body,
                    data={
                        "model": "project.task",
                        "res_id": str(task.id),
                        "project_id": str(task.project_id.id or ""),
                        "type": "project_task_assigned"
                    }
                )

            # 2. Notify Manager / Creator (if not current user)
            assigned_names = ", ".join(target_users.mapped('name')) if target_users else "Unassigned"
            for manager in managers:
                if manager.id != current_user.id and manager.id not in target_users.ids:
                    mgr_title = f"📌 Project Task Assigned: {task_name}"
                    mgr_body = f"Task '{task_name}' in project '{project_name}' assigned to {assigned_names}."
                    push_service.send_to_user(
                        user_id=manager.id,
                        title=mgr_title,
                        body=mgr_body,
                        data={
                            "model": "project.task",
                            "res_id": str(task.id),
                            "project_id": str(task.project_id.id or ""),
                            "type": "project_task_created"
                        }
                    )

        elif event_type == 'completed':
            for manager in managers:
                if manager.id != current_user.id:
                    mgr_title = f"✅ Project Task Completed: {task_name}"
                    mgr_body = f"Task '{task_name}' in project '{project_name}' was completed by {current_user.name}."
                    push_service.send_to_user(
                        user_id=manager.id,
                        title=mgr_title,
                        body=mgr_body,
                        data={
                            "model": "project.task",
                            "res_id": str(task.id),
                            "project_id": str(task.project_id.id or ""),
                            "type": "project_task_completed"
                        }
                    )

        elif event_type == 'approval':
            for manager in managers:
                if manager.id != current_user.id:
                    mgr_title = f"⏳ Task Submitted for Approval: {task_name}"
                    mgr_body = f"Task '{task_name}' in project '{project_name}' is waiting for your approval (submitted by {current_user.name})."
                    push_service.send_to_user(
                        user_id=manager.id,
                        title=mgr_title,
                        body=mgr_body,
                        data={
                            "model": "project.task",
                            "res_id": str(task.id),
                            "project_id": str(task.project_id.id or ""),
                            "type": "project_task_approval"
                        }
                    )
    except Exception as e:
        _logger.warning("Failed to send push notification for project.task (%s): %s", task.id, e)


    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        is_manager_or_admin = user.has_group('project_task_library.group_project_custom_manager') or user.has_group('project.group_project_manager')
        if not is_manager_or_admin:
            raise UserError("Access Denied: Users with 'User' access role cannot create tasks. Only Project Managers or Administrators can create tasks.")
        tasks = super().create(vals_list)
        for task in tasks:
            if task.user_ids:
                _send_project_task_push(task, 'assigned')
        return tasks

    def write(self, vals):
        user = self.env.user
        is_manager_or_admin = user.has_group('project_task_library.group_project_custom_manager') or user.has_group('project.group_project_manager')
        if not is_manager_or_admin:
            # Users with 'User' role cannot mark a task as '1_done' (Done)
            if 'state' in vals and vals['state'] == '1_done':
                raise UserError(
                    "Access Denied: As a Project User, you can set task status up to 'Approval'.\n\n"
                    "Only Project Managers or Administrators have permission to mark a task as 'Done'."
                )

            # Users with 'User' role are only allowed to update task status/state or chatter
            allowed_fields = {'state', 'stage_id', 'kanban_state', 'x_state', 'message_follower_ids', 'message_ids', 'activity_ids'}
            modified_fields = set(vals.keys())
            disallowed = modified_fields - allowed_fields
            if disallowed:
                raise UserError(
                    f"Access Denied: Users with 'User' access role can only update task status/state.\n\n"
                    f"You do not have permission to modify task details ({', '.join(disallowed)})."
                )

        old_assignments = {t.id: set(t.user_ids.ids) for t in self} if 'user_ids' in vals else {}
        old_states = {t.id: t.state for t in self} if 'state' in vals else {}

        res = super(ProjectTask, self).write(vals)

        if 'user_ids' in vals:
            for task in self:
                new_users = task.user_ids.filtered(lambda u: u.id not in old_assignments.get(task.id, set()))
                if new_users:
                    _send_project_task_push(task, 'assigned', new_users=new_users)

        if 'state' in vals:
            for task in self:
                prev_state = old_states.get(task.id)
                if vals.get('state') == '1_done' and prev_state != '1_done':
                    _send_project_task_push(task, 'completed')
                elif vals.get('state') == '03_approved' and prev_state != '03_approved':
                    _send_project_task_push(task, 'approval')

        return res

    def unlink(self):
        user = self.env.user
        is_manager_or_admin = user.has_group('project_task_library.group_project_custom_manager') or user.has_group('project.group_project_manager')
        if not is_manager_or_admin:
            raise UserError("Access Denied: Users with 'User' access role cannot delete tasks. Only Project Managers or Administrators can delete tasks.")
        return super(ProjectTask, self).unlink()

