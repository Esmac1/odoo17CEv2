# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PayrollStructure(models.Model):
    _name = 'payroll.structure'
    _description = 'Salary Structure'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # BASIC FIELDS
    name = fields.Char(string='Structure Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, size=8, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # COMPOSITION - Odoo 17 Many2many with proper relation table
    rule_ids = fields.Many2many(
        'payroll.salary.rule',
        'payroll_structure_rule_rel',
        'structure_id',
        'rule_id',
        string='Salary Rules',
        required=True,
        domain="[('company_id', '=', company_id), ('active', '=', True)]"
    )
    
    # BASIC SALARY RULE
    basic_rule_id = fields.Many2one(
        'payroll.salary.rule',
        string='Basic Salary Rule',
        domain="[('id', 'in', rule_ids), ('rule_type', '=', 'basic')]",
        required=True,
        tracking=True
    )
    
    # TOTALS - Odoo 17 computed fields
    total_fixed = fields.Float(
        string='Total Fixed Amount',
        compute='_compute_totals',
        store=True,
        readonly=True
    )
    
    total_percentage = fields.Float(
        string='Total Percentage',
        compute='_compute_totals',
        store=True,
        readonly=True
    )
    
    # DESCRIPTION
    description = fields.Html(string='Description', sanitize=True)
    note = fields.Text(string='Internal Notes')
    
    # COMPUTED FIELDS - Odoo 17 style
    @api.depends('rule_ids', 'rule_ids.amount_type', 'rule_ids.amount', 'rule_ids.percentage')
    def _compute_totals(self):
        for structure in self:
            fixed_total = 0.0
            percentage_total = 0.0
            
            for rule in structure.rule_ids:
                if rule.amount_type == 'fixed':
                    fixed_total += rule.amount
                elif rule.amount_type == 'percentage':
                    percentage_total += rule.percentage
            
            structure.total_fixed = fixed_total
            structure.total_percentage = percentage_total
    
    # CONSTRAINTS
    @api.constrains('basic_rule_id', 'rule_ids')
    def _check_basic_rule(self):
        for structure in self:
            if structure.basic_rule_id and structure.basic_rule_id not in structure.rule_ids:
                raise ValidationError("Basic salary rule must be part of the structure rules!")
            if structure.basic_rule_id and structure.basic_rule_id.rule_type != 'basic':
                raise ValidationError("Basic rule must be of type 'Basic Salary'!")
    
    # BUSINESS METHODS
    def compute_structure_salary(self, basic_salary):
        """Compute total salary for this structure - Odoo 17 method"""
        total = basic_salary
        for rule in self.rule_ids:
            amount = rule.compute_amount(basic_salary)
            if rule.rule_type == 'allowance':
                total += amount
            elif rule.rule_type == 'deduction':
                total -= amount
        return total
    
    def action_archive(self):
        """Archive structure - Odoo 17 method"""
        self.write({'active': False})
    
    def action_unarchive(self):
        """Unarchive structure - Odoo 17 method"""
        self.write({'active': True})
    
    # SQL CONSTRAINTS
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Structure code must be unique per company!'),
    ]
