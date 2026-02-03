from odoo import models, fields

class HelpdeskTag(models.Model):
    _name = "helpdesk.tag"
    _description = "Helpdesk Ticket Tag"

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color Index", default=0)
