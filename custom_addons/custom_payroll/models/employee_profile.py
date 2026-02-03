# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EmployeePayrollProfile(models.Model):
    _name = 'payroll.employee.profile'
    _description = 'Employee Payroll Profile'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'employee_id'
    
    # LINK TO HR - Odoo 17 CE
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        domain="[('active', '=', True)]",
        tracking=True
    )
    
    employee_name = fields.Char(
        string='Employee Name',
        related='employee_id.name',
        store=True,
        readonly=True
    )
    
    job_title = fields.Char(
        string='Job Title',
        related='employee_id.job_title',
        store=True,
        readonly=True
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
        readonly=True
    )
    
    # SALARY STRUCTURE
    structure_id = fields.Many2one(
        'payroll.structure',
        string='Salary Structure',
        required=True,
        domain="[('active', '=', True), ('company_id', '=', company_id)]",
        tracking=True
    )
    
    # BASIC SALARY
    basic_salary = fields.Monetary(
        string='Basic Salary',
        required=True,
        default=0.0,
        tracking=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )
    
    # PAYMENT DETAILS - Simple fields for Odoo 17 CE
    bank_account_number = fields.Char(
        string='Bank Account Number',
        size=20,
        tracking=True
    )
    
    bank_name = fields.Char(
        string='Bank Name',
        tracking=True
    )
    
    # NIGERIAN SPECIFIC
    tax_identification_number = fields.Char(
        string='TIN',
        size=20,
        tracking=True
    )
    
    pension_number = fields.Char(
        string='Pension Number',
        size=20,
        tracking=True
    )
    
    nhf_number = fields.Char(
        string='NHF Number',
        size=20,
        tracking=True
    )
    
    # COMPANY DETAILS
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # STATUS
    active = fields.Boolean(default=True, tracking=True)
    
    # COMPUTED FIELDS
    total_allowances = fields.Monetary(
        string='Total Allowances',
        compute='_compute_totals',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )
    
    total_deductions = fields.Monetary(
        string='Total Deductions',
        compute='_compute_totals',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )
    
    gross_salary = fields.Monetary(
        string='Gross Salary',
        compute='_compute_totals',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )
    
    net_salary = fields.Monetary(
        string='Net Salary',
        compute='_compute_totals',
        store=True,
        readonly=True,
        currency_field='currency_id'
    )
    
    @api.depends('basic_salary', 'structure_id', 'structure_id.rule_ids')
    def _compute_totals(self):
        for profile in self:
            if not profile.structure_id:
                profile.total_allowances = 0.0
                profile.total_deductions = 0.0
                profile.gross_salary = 0.0
                profile.net_salary = 0.0
                continue
            
            total_allowances = 0.0
            total_deductions = 0.0
            
            for rule in profile.structure_id.rule_ids:
                amount = rule.compute_amount(profile.basic_salary)
                
                if rule.rule_type == 'allowance':
                    total_allowances += amount
                elif rule.rule_type == 'deduction':
                    total_deductions += amount
            
            profile.total_allowances = total_allowances
            profile.total_deductions = total_deductions
            profile.gross_salary = profile.basic_salary + total_allowances
            profile.net_salary = profile.gross_salary - total_deductions
    
    # CONSTRAINTS
    @api.constrains('basic_salary')
    def _check_basic_salary(self):
        for profile in self:
            if profile.basic_salary < 0:
                raise ValidationError("Basic salary cannot be negative!")
    
    @api.constrains('employee_id', 'company_id')
    def _check_unique_employee(self):
        for profile in self:
            existing = self.search([
                ('employee_id', '=', profile.employee_id.id),
                ('company_id', '=', profile.company_id.id),
                ('id', '!=', profile.id)
            ])
            if existing:
                raise ValidationError(
                    f"Employee {profile.employee_id.name} already has a payroll profile!"
                )
    
    # BUSINESS METHODS
    def compute_payroll_lines(self):
        """Compute all salary components for this employee"""
        lines = []
        if not self.structure_id:
            return lines
        
        for rule in self.structure_id.rule_ids:
            amount = rule.compute_amount(self.basic_salary)
            lines.append({
                'rule_id': rule.id,
                'name': rule.name,
                'code': rule.code,
                'rule_type': rule.rule_type,
                'amount': amount,
                'account_id': rule.account_id.id,
            })
        
        return lines
    
    def action_open_employee(self):
        """Open related employee record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee',
            'res_model': 'hr.employee',
            'res_id': self.employee_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_archive(self):
        """Archive profile"""
        self.write({'active': False})
    
    def action_unarchive(self):
        """Unarchive profile"""
        self.write({'active': True})
    
    # SQL CONSTRAINTS
    _sql_constraints = [
        ('employee_company_uniq', 'unique(employee_id, company_id)', 
         'Each employee can have only one payroll profile per company!'),
    ]
    
    # DEFAULT METHODS
    @api.model
    def create(self, vals):
        # Set default basic salary from contract if available
        if 'basic_salary' not in vals or vals.get('basic_salary') == 0:
            employee_id = vals.get('employee_id')
            if employee_id:
                # Try to get salary from contract in Odoo 17 CE
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee_id),
                    ('state', '=', 'open')
                ], limit=1)
                if contract and contract.wage:
                    vals['basic_salary'] = contract.wage
        
        return super().create(vals)
