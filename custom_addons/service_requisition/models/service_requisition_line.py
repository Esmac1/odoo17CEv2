from odoo import models, fields, api

class ServiceRequisitionLine(models.Model):
    _name = 'service.requisition.line'
    _description = 'Service Requisition Line'
    
    requisition_id = fields.Many2one('service.requisition', string='Requisition', ondelete='cascade')
    description = fields.Char(string='Item Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_cost = fields.Float(string='Unit Cost', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 related='requisition_id.currency_id', readonly=True)
    
    @api.depends('quantity', 'unit_cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_cost
