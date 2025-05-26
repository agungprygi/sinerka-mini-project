from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectTaskInternal(models.Model):
    _name = 'project.task.internal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project Task Internal'
    _order = 'due_date desc'

    name = fields.Char(string='Task Name', required=True)
    project_id = fields.Many2one('project.internal', string='Project')
    assigned_to = fields.Many2one('hr.employee', string='Assignee')
    due_date = fields.Date(string='Due Date')
    state = fields.Selection([
        ('open', 'Open'),
        ('working', 'Working'),
        ('review', 'Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='open')
    description = fields.Html(string='Description')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='medium', string='Priority', tracking=True)

    @api.constrains('due_date', 'project_id')
    def _check_due_date(self):
        for rec in self:
            if rec.due_date and rec.project_id and rec.project_id.end_date:
                if rec.due_date > rec.project_id.end_date:
                    raise ValidationError(_("Due date cannot be after the project end date"))
    
    @api.constrains('assigned_to')
    def _check_assigned_to(self):
        for rec in self:
            if rec.assigned_to and rec.state not in ['done', 'cancelled']:
                active_tasks = self.env['project.task.internal'].search([
                    ('assigned_to', '=', rec.assigned_to.id),
                    ('state', 'not in', ['done', 'cancelled']),
                    ('id', '!=', rec.id),
                ])
                if len(active_tasks) >= 5:
                    raise ValidationError(_(f"Employee {rec.assigned_to.name} already has 5 active tasks. "
                        f"Cannot assign more tasks."))

    def action_start(self):
        self.write({'state': 'working'})

    def action_review(self):
        self.write({'state': 'review'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reopen(self):
        self.write({'state': 'open'})
    

    
        
    
    