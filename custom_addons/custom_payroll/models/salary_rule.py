# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SalaryRule(models.Model):
    _name = 'payroll.salary.rule'
    _description = 'Salary Rule'
    _order = 'sequence, code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # BASIC FIELDS
    name = fields.Char(string='Rule Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, size=8, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help='Rules are processed in sequence order')
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # RULE TYPE
    rule_type = fields.Selection(
        selection=[
            ('basic', 'Basic Salary'),
            ('allowance', 'Allowance'),
            ('deduction', 'Deduction'),
        ],
        string='Type',
        required=True,
        default='allowance',
        tracking=True
    )
    
    # CALCULATION METHOD
    amount_type = fields.Selection(
        selection=[
            ('fixed', 'Fixed Amount'),
            ('percentage', 'Percentage of Basic'),
        ],
        string='Amount Type',
        required=True,
        default='fixed',
        tracking=True
    )
    
    amount = fields.Float(string='Amount', default=0.0, tracking=True)
    percentage = fields.Float(string='Percentage (%)', default=0.0, tracking=True)
    
    # DISPLAY FIELD - Combined amount/percentage for tree view
    display_amount = fields.Char(
        string='Amount/Percentage',
        compute='_compute_display_amount',
        store=True,
        readonly=True
    )
    
    # ACCOUNTING INTEGRATION (CRITICAL for Odoo 17 CE)
    account_id = fields.Many2one(
        'custom_accounting.account',
        string='Accounting Account',
        required=True,
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        tracking=True,
        help="Account where this salary component will be posted in accounting"
    )
    
    # Odoo 17: Use compute for account_type
    account_type = fields.Selection(
        selection=[
            ('expense', 'Expense'),
            ('liability', 'Liability'),
            ('asset', 'Asset'),
        ],
        string='Account Type',
        compute='_compute_account_type',
        store=True,
        readonly=True
    )
    
    # NIGERIAN CONTEXT (Odoo 17 uses widget for boolean fields)
    is_taxable = fields.Boolean(
        string='Taxable',
        default=True,
        help='Is this amount taxable for PAYE?'
    )
    
    is_pensionable = fields.Boolean(
        string='Pensionable',
        default=True,
        help='Is this amount subject to pension contribution?'
    )
    
    is_nhf_applicable = fields.Boolean(
        string='NHF Applicable',
        default=True,
        help='Is this amount subject to NHF deduction?'
    )
    
    # APPEARANCE (Odoo 17 supports color picker)
    color = fields.Integer(string='Color Index', default=0)
    note = fields.Text(string='Description')
    
    # COMPUTED FIELDS with Odoo 17 @api.depends decorator
    @api.depends('account_id.account_type')
    def _compute_account_type(self):
        """Compute account type from linked account"""
        for rule in self:
            if rule.account_id:
                rule.account_type = rule.account_id.account_type
            else:
                rule.account_type = False
    
    @api.depends('amount_type', 'amount', 'percentage')
    def _compute_display_amount(self):
        """Compute display amount for tree view"""
        for rule in self:
            if rule.amount_type == 'fixed':
                rule.display_amount = f"{rule.amount:,.2f}"
            elif rule.amount_type == 'percentage':
                rule.display_amount = f"{rule.percentage}%"
            else:
                rule.display_amount = ""
    
    # CONSTRAINTS
    @api.constrains('amount_type', 'amount', 'percentage')
    def _check_amounts(self):
        for rule in self:
            if rule.amount_type == 'percentage' and (rule.percentage < 0 or rule.percentage > 100):
                raise ValidationError("Percentage must be between 0 and 100")
            if rule.amount < 0:
                raise ValidationError("Amount cannot be negative")
    
    @api.constrains('code')
    def _check_code(self):
        for rule in self:
            if not rule.code.isalnum():
                raise ValidationError("Code must contain only letters and numbers")
    
    # BUSINESS METHODS
    def compute_amount(self, basic_salary=0.0):
        """Compute amount based on rule type - Odoo 17 method"""
        self.ensure_one()
        if self.amount_type == 'fixed':
            return self.amount
        elif self.amount_type == 'percentage':
            return basic_salary * (self.percentage / 100.0)
        return 0.0
    
    def action_archive(self):
        """Archive rule - Odoo 17 method"""
        self.write({'active': False})
    
    def action_unarchive(self):
        """Unarchive rule - Odoo 17 method"""
        self.write({'active': True})
    
    # SQL CONSTRAINTS
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Rule code must be unique per company!'),
    ]
    
    # DEFAULT METHODS with Odoo 17 context support
    @api.model
    def default_get(self, fields_list):
        """Override default_get for Odoo 17"""
        res = super().default_get(fields_list)
        if self.env.company:
            res['company_id'] = self.env.company.id
        return res
    
    # POST INIT HOOK for Odoo 17
    @api.model
    def _post_init_hook(self):
        """Post initialization hook for Odoo 17"""
        # Create default salary rules if none exist
        if not self.search_count([]):
            self.create_default_rules()
    
    @api.model
    def create_default_rules(self):
        """Create default salary rules for Nigerian context"""
        company = self.env.company
        
        # Get required accounts from custom_accounting module
        salary_expense_account = self.env['custom_accounting.account'].search([
            ('code', '=', '600001'),  # Salary Expense account
            ('company_id', '=', company.id)
        ], limit=1)
        
        allowance_expense_account = self.env['custom_accounting.account'].search([
            ('code', '=', '600002'),  # Allowance Expense account
            ('company_id', '=', company.id)
        ], limit=1)
        
        tax_payable_account = self.env['custom_accounting.account'].search([
            ('code', '=', '200002'),  # Tax Payable account
            ('company_id', '=', company.id)
        ], limit=1)
        
        pension_payable_account = self.env['custom_accounting.account'].search([
            ('code', '=', '2103'),  # Pension Payable account (you mentioned 2103)
            ('company_id', '=', company.id)
        ], limit=1)
        
        # Create default rules only if accounts exist
        default_rules = []
        
        # Basic Salary Rule
        if salary_expense_account:
            default_rules.append({
                'name': 'Basic Salary',
                'code': 'BASIC',
                'rule_type': 'basic',
                'amount_type': 'fixed',
                'amount': 0.0,
                'account_id': salary_expense_account.id,
                'sequence': 1,
                'is_taxable': True,
                'is_pensionable': True,
                'is_nhf_applicable': True,
            })
        
        # Housing Allowance Rule
        if allowance_expense_account:
            default_rules.append({
                'name': 'Housing Allowance',
                'code': 'HOUSE',
                'rule_type': 'allowance',
                'amount_type': 'percentage',
                'percentage': 30.0,
                'account_id': allowance_expense_account.id,
                'sequence': 2,
                'is_taxable': True,
                'is_pensionable': True,
                'is_nhf_applicable': True,
            })
        
        # Transport Allowance Rule
        if allowance_expense_account:
            default_rules.append({
                'name': 'Transport Allowance',
                'code': 'TRANS',
                'rule_type': 'allowance',
                'amount_type': 'percentage',
                'percentage': 20.0,
                'account_id': allowance_expense_account.id,
                'sequence': 3,
                'is_taxable': True,
                'is_pensionable': True,
                'is_nhf_applicable': True,
            })
        
        # PAYE Tax Deduction Rule
        if tax_payable_account:
            default_rules.append({
                'name': 'PAYE Tax',
                'code': 'PAYE',
                'rule_type': 'deduction',
                'amount_type': 'percentage',
                'percentage': 7.5,
                'account_id': tax_payable_account.id,
                'sequence': 20,
                'is_taxable': False,
                'is_pensionable': False,
                'is_nhf_applicable': False,
            })
        
        # Pension Deduction Rule
        if pension_payable_account:
            default_rules.append({
                'name': 'Pension Contribution',
                'code': 'PENSION',
                'rule_type': 'deduction',
                'amount_type': 'percentage',
                'percentage': 8.0,
                'account_id': pension_payable_account.id,
                'sequence': 21,
                'is_taxable': False,
                'is_pensionable': True,
                'is_nhf_applicable': False,
            })
        
        # Create the rules
        for rule_vals in default_rules:
            self.create(rule_vals)
