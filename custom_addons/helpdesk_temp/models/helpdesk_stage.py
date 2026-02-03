from odoo import models, fields

class HelpdeskStage(models.Model):
    _name = "helpdesk.stage"
    _description = "Helpdesk Stage"
    _order = "sequence, id"

    name = fields.Char(string="Stage Name", required=True)
    code = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('waiting', 'Waiting'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string="Stage Code", required=True, default='new')
    sequence = fields.Integer(string="Sequence", default=1)
    fold = fields.Boolean(string="Folded in Kanban", default=False)
