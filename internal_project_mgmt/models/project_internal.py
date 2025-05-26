from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class ProjectInternal(models.Model):
    _name = 'project.internal'
    _description = 'Project Internal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    manager_id = fields.Many2one('hr.employee', string='Manager', required=True)
    department_id = fields.Many2one(
        'hr.department', 
        related='manager_id.department_id',
        string='Department',
        store=True,
        required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft')

    #field task
    task_ids = fields.One2many('project.task.internal', 'project_id', string='Tasks')
    task_count = fields.Integer(string='Task Count', compute='_compute_task_count')
    progress = fields.Float(string='Progress', compute='_compute_progress', store=True)

    @api.depends('task_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    @api.depends('task_ids')
    def _compute_progress(self):
        for rec in self:
            if rec.task_ids:
                done_tasks = rec.task_ids.filtered(lambda t: t.state == 'done')
                rec.progress = (len(done_tasks) / len(rec.task_ids)) * 100
            else:
                rec.progress = 0.0
        
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.end_date <= rec.start_date:
                    raise ValidationError("End date must be greater than start date")

    @api.constrains('state','manager_id')
    def _check_active_project(self):
        for rec in self:
            active_projects = self.env['project.internal'].search([
                ('manager_id', '=', rec.manager_id.id),
                ('state', '=', 'in_progress'),
                ('id', '!=', rec.id)
            ])
            if active_projects:
                raise ValidationError(_(
                    f"Manager {rec.manager_id.name} is already managing another project. "
                    "Please complete or cancel the other project before starting a new one."
                ))

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_view_tasks(self):
        self.ensure_one()
        action = self.env.ref('internal_project_mgmt.action_internal_project_task_mgmt').read()[0]
        action['context'] = {
            'default_project_id': self.id
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action
    
    def _send_overdue_task_notification(self):
        overdue_projects = self.env['project.internal'].search([
            ('end_date', '<', date.today()),
            ('state', 'in', ['in_progress', 'draft'])])

        for project in overdue_projects:
            incomplete_tasks = project.task_ids.filtered(lambda t: t.state not in ['done', 'cancelled'])
            if incomplete_tasks and project.manager_id.work_email:
                template = self.env.ref('internal_project_mgmt.email_template_overdue_task', raise_if_not_found=False)
                context = {
                    'manager': project.manager_id,
                    'manager_name': project.manager_id.name,
                    'project_name': project.name,
                    'project_end_date': project.end_date,
                    'project_current_status': project.state,
                    'email': project.manager_id.work_email,
                }
                if template:
                    template.with_context(context).send_mail(project.id, force_send=True)
        
        