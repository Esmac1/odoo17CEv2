from odoo import models, fields

class HelpdeskCategory(models.Model):
    _name = "helpdesk.category"
    _description = "Helpdesk Ticket Category"

    name = fields.Char(string="Category Name", required=True)
    team_id = fields.Many2one('helpdesk.team', string="Assigned Team")
    active = fields.Boolean(string="Active", default=True)
