from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class ServiceRequisition(models.Model):
    _name = 'service.requisition'
    _description = 'Service Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, default='New', readonly=True)
    date_request = fields.Date(string='Request Date', default=fields.Date.today, required=True, tracking=True)
    requester_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user, required=True, tracking=True)
    
    # Requester Information
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    contact_phone = fields.Char(string='Phone', tracking=True)
    contact_email = fields.Char(string='Email', related='requester_id.email', readonly=True)
    
    # Service Details
    service_type = fields.Selection([
        ('it_support', 'IT Support'),
        ('maintenance', 'Maintenance'),
        ('consulting', 'Consulting'),
        ('training', 'Training'),
        ('other', 'Other')
    ], string='Service Type', required=True, tracking=True)
    
    description = fields.Text(string='Service Description', required=True, tracking=True)
    purpose = fields.Text(string='Purpose/Justification', required=True, tracking=True)
    deadline_date = fields.Date(string='Desired Completion Date', required=True, tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority Level', default='medium', required=True, tracking=True)
    
    # Vendor Information
    preferred_vendor = fields.Char(string='Preferred Vendor', tracking=True)
    vendor_contact = fields.Char(string='Vendor Contact Info', tracking=True)
    
    # Approval Section
    approver_id = fields.Many2one('res.users', string='Approver', required=True, tracking=True)
    approval_date = fields.Date(string='Approval Date', readonly=True, tracking=True)
    
    # Financial Information
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 default=lambda self: self.env.company.currency_id)
    total_estimated_cost = fields.Monetary(string='Total Estimated Cost', 
                                          compute='_compute_total_cost', store=True, tracking=True)
    
    # Lines
    line_ids = fields.One2many('service.requisition.line', 'requisition_id', string='Service Items')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    
    # Additional fields for better tracking
    rejection_reason = fields.Text(string='Rejection Reason')
    is_confidential = fields.Boolean(string='Confidential', default=False)
    
    # Computed fields
    @api.depends('line_ids.subtotal')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_estimated_cost = sum(line.subtotal for line in rec.line_ids)
    
    @api.onchange('requester_id')
    def _onchange_requester_id(self):
        if self.requester_id:
            # Set department from employee record
            employee = self.env['hr.employee'].search([('user_id', '=', self.requester_id.id)], limit=1)
            if employee:
                self.department_id = employee.department_id
                self.contact_phone = employee.work_phone or employee.mobile_phone
                
            # Set default approver as requester's manager
            if employee and employee.parent_id and employee.parent_id.user_id:
                self.approver_id = employee.parent_id.user_id
    
    # Action Methods
    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add at least one service item before submitting.")
            rec.state = 'submitted'
            # Create activity for approver
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                note=f'Service Requisition {rec.name} needs your approval',
                user_id=rec.approver_id.id,
                summary=f'Approve Service Requisition - {rec.name}'
            )
            rec.message_post(body="Requisition submitted for approval.")
    
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.approval_date = date.today()
            # Unlink activities
            rec.activity_ids.unlink()
            rec.message_post(body="Requisition approved.")
    
    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rejection Reason',
            'res_model': 'service.requisition.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_requisition_id': self.id}
        }
    
    def action_reject_confirm(self, reason):
        for rec in self:
            rec.state = 'rejected'
            rec.approval_date = date.today()
            rec.rejection_reason = reason
            # Unlink activities
            rec.activity_ids.unlink()
            rec.message_post(body=f"Requisition rejected. Reason: {reason}")
    
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.rejection_reason = False
    
    def action_send_message(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Message',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'service.requisition',
                'default_res_id': self.id,
                'default_composition_mode': 'comment',
            }
        }
    
    def action_log_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Schedule Activity',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'service.requisition',
                'default_res_id': self.id,
            }
        }
    
    def action_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachments',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', 'service.requisition'), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id}
        }
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('service.requisition') or 'New'
        return super(ServiceRequisition, self).create(vals)
