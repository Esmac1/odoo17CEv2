from odoo import models, fields, api

class ServiceRequisitionRejectWizard(models.TransientModel):
    _name = 'service.requisition.reject.wizard'
    _description = 'Service Requisition Rejection Wizard'
    
    requisition_id = fields.Many2one('service.requisition', string='Requisition', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    
    def action_reject(self):
        self.requisition_id.action_reject_confirm(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}
