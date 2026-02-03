from odoo import models, fields, api

class HelpdeskTeam(models.Model):
    _name = "helpdesk.team"
    _description = "Helpdesk Team"

    name = fields.Char(string="Team Name", required=True, tracking=True)
    user_ids = fields.Many2many('res.users', string="Members")

    # Computed Fields
    ticket_count = fields.Integer(
        string="Tickets",
        compute='_compute_ticket_count'
    )
    open_ticket_count = fields.Integer(
        string="Open Tickets",
        compute='_compute_open_ticket_count'
    )

    @api.depends('user_ids')
    def _compute_ticket_count(self):
        """Total tickets assigned to this team"""
        for team in self:
            team.ticket_count = self.env['helpdesk.ticket'].search_count([('team_id', '=', team.id)])

    @api.depends('user_ids')
    def _compute_open_ticket_count(self):
        """Tickets in progress / waiting / new for this team"""
        for team in self:
            team.open_ticket_count = self.env['helpdesk.ticket'].search_count([
                ('team_id', '=', team.id),
                ('stage_code', 'in', ['new', 'in_progress', 'waiting'])
            ])
