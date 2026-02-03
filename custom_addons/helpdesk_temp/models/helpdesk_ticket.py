from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "stage_id, priority desc, id"

    # --- Basic Fields ---
    name = fields.Char(string="Title", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    requester_id = fields.Many2one('res.partner', string="Requester", tracking=True)
    assigned_id = fields.Many2one('res.users', string="Assigned To", tracking=True)
    team_id = fields.Many2one('helpdesk.team', string="Team", tracking=True)
    category_id = fields.Many2one('helpdesk.category', string="Category")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], default='1', string="Priority", tracking=True)

    stage_id = fields.Many2one(
        'helpdesk.stage', 
        string="Stage", 
        tracking=True,
        default=lambda self: self._default_stage_id(),
        group_expand='_read_group_stage_ids'
    )
    stage_code = fields.Selection(related='stage_id.code', string="Stage Code", store=True)

    tag_ids = fields.Many2many('helpdesk.tag', string="Tags")
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked')
    ], default='normal', string="Kanban State")

    # --- SLA / Resolution ---
    # Deadline field removed as requested
    closed_date = fields.Datetime(string="Closed Date", readonly=True)
    response_due_date = fields.Datetime(string="Response Due Date")
    resolution_due_date = fields.Datetime(string="Resolution Due Date")
    resolution_notes = fields.Text(string="Resolution Notes")

    # --- Related ---
    team_member_ids = fields.Many2many(
        related='team_id.user_ids',
        string="Team Members",
        readonly=True
    )

    # --- Default Methods ---
    @api.model
    def _default_stage_id(self):
        """Get default stage (New)"""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'new')], limit=1)
        return stage.id if stage else False

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Show all stages in kanban view, even if no tickets"""
        return self.env['helpdesk.stage'].search([], order=order)

    # --- Automatic closed date handling ---
    @api.model
    def create(self, vals):
        """Set initial stage to New if not provided"""
        if 'stage_id' not in vals:
            new_stage = self.env['helpdesk.stage'].search([('code', '=', 'new')], limit=1)
            if new_stage:
                vals['stage_id'] = new_stage.id
        return super().create(vals)

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Automatically set closed_date when moving to closed stage"""
        for ticket in self:
            if ticket.stage_id.code == 'closed' and not ticket.closed_date:
                ticket.closed_date = fields.Datetime.now()
            elif ticket.stage_id.code != 'closed' and ticket.closed_date:
                ticket.closed_date = False

    def write(self, vals):
        """Handle closed_date when stage changes via write"""
        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.code == 'closed':
                # Set closed_date for tickets that don't have it
                tickets_to_close = self.filtered(lambda t: not t.closed_date)
                if tickets_to_close:
                    vals['closed_date'] = fields.Datetime.now()
            else:
                # Clear closed_date when moving away from closed stage
                tickets_to_reopen = self.filtered(lambda t: t.closed_date)
                if tickets_to_reopen:
                    vals['closed_date'] = False
        return super().write(vals)

    # --- Action Methods ---
    def action_accept(self):
        """Move ticket to In Progress."""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'in_progress')], limit=1)
        if stage:
            self.write({'stage_id': stage.id})
            self.message_post(body=_("Ticket accepted and moved to In Progress."))

    def action_set_waiting(self):
        """Move ticket to Waiting."""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'waiting')], limit=1)
        if stage:
            self.write({'stage_id': stage.id})
            self.message_post(body=_("Ticket set to Pending state."))

    def action_resolve(self):
        """Move ticket to Resolved."""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'resolved')], limit=1)
        if stage:
            self.write({
                'stage_id': stage.id,
                'closed_date': fields.Datetime.now() if not self.closed_date else self.closed_date
            })
            self.message_post(body=_("Ticket marked as Resolved."))

    def action_close(self):
        """Move ticket to Closed."""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'closed')], limit=1)
        if stage:
            self.write({
                'stage_id': stage.id,
                'closed_date': fields.Datetime.now()
            })
            self.message_post(body=_("Ticket Closed."))

    def action_reopen(self):
        """Reopen a closed or resolved ticket."""
        stage = self.env['helpdesk.stage'].search([('code', '=', 'in_progress')], limit=1)
        if stage:
            self.write({
                'stage_id': stage.id,
                'closed_date': False
            })
            self.message_post(body=_("Ticket Reopened."))
