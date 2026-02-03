# wizards/generate_payroll_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class GeneratePayrollWizard(models.TransientModel):
    _name = 'generate.payroll.wizard'
    _description = 'Generate Payroll Lines Wizard'

    run_id = fields.Many2one(
        'payroll.run',
        required=True,
        ondelete='cascade'
    )

    def action_generate(self):
        self.ensure_one()
        run = self.run_id

        if run.line_ids:
            raise UserError(_("Payroll lines already exist. Cannot generate again."))

        profiles = self.env['payroll.employee.profile'].search([
            ('active', '=', True),
            ('company_id', '=', run.company_id.id)
        ])

        if not profiles:
            raise UserError(_("No active employee payroll profiles found for this company."))

        lines_to_create = []
        rule_lines_to_create = []

        for profile in profiles:
            line_vals = {
                'run_id': run.id,
                'employee_profile_id': profile.id,
            }
            lines_to_create.append(line_vals)

            # Get computed rule lines from employee profile
            for rule_data in profile.compute_payroll_lines():
                rule_data['employee_profile_id'] = profile.id  # temporary tag
                rule_lines_to_create.append(rule_data)

        # Create payroll lines
        payroll_lines = self.env['payroll.line'].create(lines_to_create)

        # Create rule lines and link them
        for line in payroll_lines:
            profile = line.employee_profile_id
            relevant_rules = [r for r in rule_lines_to_create if r.get('employee_profile_id') == profile.id]
            commands = []
            for r in relevant_rules:
                commands.append((0, 0, {
                    'rule_id': r['rule_id'],
                    'amount': r['amount'],
                }))
            if commands:
                line.rule_line_ids = commands

        run.message_post(body=_("Generated payroll lines for %d employees.") % len(payroll_lines))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payroll.run',
            'res_id': run.id,
            'view_mode': 'form',
            'target': 'current',
        }
