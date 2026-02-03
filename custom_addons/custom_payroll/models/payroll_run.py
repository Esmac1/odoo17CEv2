# models/payroll_run.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class PayrollRun(models.Model):
    _name = 'payroll.run'
    _description = 'Payroll Run'
    _order = 'date_from desc, name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    date_from = fields.Date(string='Period Start', required=True)
    date_to = fields.Date(string='Period End', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    journal_id = fields.Many2one(
        'custom_accounting.journal',
        string='Payroll Journal',
        required=True,
        domain="[('company_id', '=', company_id)]",
    )

    line_ids = fields.One2many(
        'payroll.line',
        'run_id',
        string='Payroll Lines'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    move_id = fields.Many2one('custom_accounting.move', string='Accounting Entry', readonly=True)

    total_gross = fields.Monetary(
        compute='_compute_totals', string='Total Gross', store=True
    )
    total_net = fields.Monetary(
        compute='_compute_totals', string='Total Net Pay', store=True
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id', readonly=True
    )

    @api.depends('line_ids.gross_amount', 'line_ids.net_amount')
    def _compute_totals(self):
        for run in self:
            run.total_gross = sum(line.gross_amount for line in run.line_ids)
            run.total_net = sum(line.net_amount for line in run.line_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('payroll.run') or 'New'
        return super().create(vals)

    def action_confirm(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError(_("Cannot confirm payroll with no lines!"))
        self.state = 'confirmed'

    def action_post_accounting(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed payroll can be posted."))
        if self.move_id:
            raise UserError(_("Payroll already posted to accounting."))

        move_lines = []
        for rule_line in self.line_ids.mapped('rule_line_ids'):
            account = rule_line.account_id
            if not account:
                raise UserError(_("Rule %s has no accounting account defined.") % rule_line.name)

            amount = rule_line.amount
            if rule_line.rule_type in ('allowance', 'basic'):
                # Debit: Expense
                move_lines.append((0, 0, {
                    'account_id': account.id,
                    'debit': amount,
                    'credit': 0.0,
                    'name': f"{rule_line.name} - {rule_line.payroll_line_id.employee_id.name}",
                }))
            else:  # deduction
                # Credit: Liability (PAYE, Pension, etc.)
                move_lines.append((0, 0, {
                    'account_id': account.id,
                    'debit': 0.0,
                    'credit': amount,
                    'name': f"{rule_line.name} - {rule_line.payroll_line_id.employee_id.name}",
                }))

        # Net Salary Payable - use your existing 2101 account
        net_total = self.total_net
        net_account = self.env['account.account'].search([('code', '=', '2101')], limit=1)
        if not net_account:
            raise UserError(_("Account with code 2101 (Salary Payable) not found."))

        move_lines.append((0, 0, {
            'account_id': net_account.id,
            'debit': 0.0,
            'credit': net_total,
            'name': "Net Salary Payable",
        }))

        move = self.env['custom_accounting.move'].create({
            'journal_id': self.journal_id.id,
            'date': self.date_to,
            'ref': self.name,
            'line_ids': move_lines,
        })
        move.action_post()

        self.move_id = move.id
        self.state = 'posted'
        self.message_post(body=_("Payroll posted to accounting: %s") % move.name)

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset_draft(self):
        self.state = 'draft'

    def action_generate_lines(self):
        self.ensure_one()
        wizard = self.env['generate.payroll.wizard'].create({
            'run_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Payroll Lines',
            'res_model': 'generate.payroll.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }
