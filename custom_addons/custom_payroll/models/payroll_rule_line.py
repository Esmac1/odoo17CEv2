# models/payroll_rule_line.py
from odoo import models, fields

class PayrollRuleLine(models.Model):
    _name = 'payroll.rule.line'
    _description = 'Payroll Rule Line'
    _order = 'sequence'

    payroll_line_id = fields.Many2one('payroll.line', required=True, ondelete='cascade')
    rule_id = fields.Many2one('payroll.salary.rule', string='Salary Rule', required=True)
    sequence = fields.Integer(related='rule_id.sequence', store=True)
    code = fields.Char(related='rule_id.code', readonly=True)
    name = fields.Char(related='rule_id.name', readonly=True)
    rule_type = fields.Selection(related='rule_id.rule_type', readonly=True)
    amount = fields.Monetary(string='Amount', required=True)
    account_id = fields.Many2one(related='rule_id.account_id', readonly=True)
    currency_id = fields.Many2one(related='payroll_line_id.currency_id')
