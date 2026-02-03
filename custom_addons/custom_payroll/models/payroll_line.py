# models/payroll_line.py
from odoo import models, fields, api

class PayrollLine(models.Model):
    _name = 'payroll.line'
    _description = 'Payroll Line'
    _order = 'employee_id'

    run_id = fields.Many2one('payroll.run', required=True, ondelete='cascade')
    employee_profile_id = fields.Many2one(
        'payroll.employee.profile',
        string='Employee Profile',
        required=True
    )
    employee_id = fields.Many2one(
        related='employee_profile_id.employee_id',
        string='Employee',
        store=True,
        readonly=True
    )
    basic_salary = fields.Monetary(
        related='employee_profile_id.basic_salary',
        readonly=True
    )
    structure_id = fields.Many2one(
        related='employee_profile_id.structure_id',
        readonly=True
    )

    gross_amount = fields.Monetary(
        compute='_compute_amounts', store=True, string='Gross Pay'
    )
    total_deductions = fields.Monetary(
        compute='_compute_amounts', store=True
    )
    net_amount = fields.Monetary(
        compute='_compute_amounts', store=True, string='Net Pay'
    )
    currency_id = fields.Many2one(related='run_id.currency_id')

    # ← THIS FIELD WAS MISSING — NOW ADDED
    rule_line_ids = fields.One2many(
        'payroll.rule.line',
        'payroll_line_id',
        string='Rule Lines'
    )

    @api.depends('employee_profile_id.gross_salary', 'employee_profile_id.total_deductions', 'employee_profile_id.net_salary')
    def _compute_amounts(self):
        for line in self:
            if not line.employee_profile_id:
                line.gross_amount = line.total_deductions = line.net_amount = 0.0
                continue
            line.gross_amount = line.employee_profile_id.gross_salary
            line.total_deductions = line.employee_profile_id.total_deductions
            line.net_amount = line.employee_profile_id.net_salary
