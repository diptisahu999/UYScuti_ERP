# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class SolarProject(models.Model):
    _name = 'solar.project'
    _description = 'Solar Project'
    _inherit = ['mail.thread']

    name = fields.Char(string='Project No.', default='/', copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Consumer Name', required=True)
    consumer_no = fields.Char(string='Consumer No.', related='sale_order_id.name', store=True)
    project_type = fields.Selection([
        ('ground_mounted', 'Ground Mounted'),
        ('commercial', 'Commercial / Industrial'),
    ], string='Project Type', default='ground_mounted')
    date_start = fields.Date(string='Date', default=fields.Date.context_today)
    mobile = fields.Char(string='Mobile', compute='_compute_mobile', store=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.user)
    
    @api.depends('partner_id')
    def _compute_mobile(self):
        for rec in self:
            # Safely check for mobile attribute to avoid AttributeError
            partner_mobile = getattr(rec.partner_id, 'mobile', False)
            rec.mobile = partner_mobile or rec.partner_id.phone or ''
    
    # Header Info
    kw_capacity = fields.Float(string='Capacity (KW)', digits=(10, 3))
    discom_id = fields.Many2one('solar.discom', string='Discom')

    # Financial Analysis Relation
    financial_ids = fields.One2many('solar.financials', 'project_id', string='Financial Analyses')
    financial_count = fields.Integer(string='Financial Count', compute='_compute_financial_count')

    @api.depends('financial_ids')
    def _compute_financial_count(self):
        for rec in self:
            rec.financial_count = len(rec.financial_ids)

    def action_view_financials(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('uyscuti_solar_project.action_solar_financials')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {
            'default_project_id': self.id,
            'default_kw_capacity': self.kw_capacity,
        }
        return action

    # Access Control
    is_stage_editable = fields.Boolean(compute='_compute_is_stage_editable')

    @api.depends('state')
    def _compute_is_stage_editable(self):
        is_admin = self.env.user.has_group('base.group_system') or self.env.user.has_group('base.group_erp_manager')
        allowed_stages = self.env.user.solar_stage_ids.mapped('code')
        for rec in self:
            if is_admin:
                rec.is_stage_editable = True
            else:
                rec.is_stage_editable = rec.state in allowed_stages

    # Lifecycle Stages
    state = fields.Selection([
        ('loa', '1. LOA (Letter of Acceptance)'),
        ('gm_project_apply', '2. Project Apply'),
        ('gm_discom_app', '3. Discom Application'),
        ('gm_akshay_urja', '4. Akshay Urja Connectivity Apply'),
        ('gm_doc_submit', '5. Document Submit'),
        ('gm_fees_pay', '6. Fees Payment'),
        ('gm_approval', '7. Approval'),
        ('gm_discom_agreement', '8. Discom Agreement'),
        ('gm_land', '9. Land'),
        ('gm_design', '10. Design'),
        ('gm_bom', '11. BOM'),
        ('gm_vendor_select', '12. Vendor Selection (Purchase)'),
        ('gm_store_incharge', '13. Store Incharge Manager'),
        ('gm_authorised_person', '14. Authorised Person'),
        ('gm_mms_report', '15. MMS Report (25%)'),
        ('gm_blockwise_reconcile', '16. Blockwise Reconcile'),
        ('gm_tasklist', '17. Tasklist'),
        ('gm_qc', '18. Quality Control (QC)'),
        ('payment_clear', 'Payment Clear'),
    ], string='Current Stage', default='loa', tracking=True)

    # 3. LOA (Letter of Acceptance) Documents
    loa_line_ids = fields.One2many('solar.project.loa.line', 'project_id', string='LOA Documents')

    # 19. Payment Clear
    payment_line_ids = fields.One2many('solar.project.payment', 'project_id', string='Payment Entries')
    payment_total = fields.Float(string='Total Paid', compute='_compute_payment_total', store=True)

    @api.depends('payment_line_ids.amount')
    def _compute_payment_total(self):
        for rec in self:
            rec.payment_total = sum(rec.payment_line_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('solar.project') or '/'
        return super().create(vals_list)

    def action_next_stage(self):
        """Move project to the next stage after strict field validation."""
        self.ensure_one()
        selection = [s[0] for s in self._fields['state'].selection]
        current_index = selection.index(self.state)
        if current_index + 1 < len(selection):
            self.state = selection[current_index + 1]
    def action_previous_stage(self):
        """Move project to the previous stage."""
        self.ensure_one()
        selection = [s[0] for s in self._fields['state'].selection]
        current_index = selection.index(self.state)
        if current_index - 1 >= 0:
            self.state = selection[current_index - 1]
    
    def action_preview_document(self):
        """Open the document in a new tab for preview"""
        self.ensure_one()
        field_name = self.env.context.get('field_name')
        if not field_name or not getattr(self, field_name):
            return False
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/{field_name}',
            'target': 'new',
        }

    def action_set_payment_clear(self):
        self.state = 'payment_clear'

class SolarProjectPayment(models.Model):
    _name = 'solar.project.payment'
    _description = 'Solar Project Payment'
    _order = 'date desc'

    project_id = fields.Many2one('solar.project', string='Project', ondelete='cascade')
    amount = fields.Float(string='Amount', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    remark = fields.Char(string='Remark')

class SolarProjectLoaLine(models.Model):
    _name = 'solar.project.loa.line'
    _description = 'Solar Project LOA Document'

    project_id = fields.Many2one('solar.project', string='Project', ondelete='cascade')
    file = fields.Binary(string='LOA File', required=True)
    file_name = fields.Char(string='Filename')
    description = fields.Char(string='Description')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    solar_project_id = fields.Many2one('solar.project', string='Solar Project', readonly=True)
    solar_kw_capacity = fields.Float(string='Capacity (KW)')
    solar_discom_id = fields.Many2one('solar.discom', string='Discom')

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(SaleOrder, self).create(vals_list)
        for order in orders:
            if order.opportunity_id and not order.solar_project_id:
                # Determine project type from the linked Opportunity's lead tag
                project_type = 'ground_mounted'  # Default
                if order.opportunity_id.tag_ids:
                    tag_names = [t.name.upper().strip() for t in order.opportunity_id.tag_ids]
                    if 'COMMERCIAL' in tag_names or 'COMMERCIAL / INDUSTRIAL' in tag_names:
                        project_type = 'commercial'

                # Create Project automatically
                project = self.env['solar.project'].create({
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                    'kw_capacity': order.solar_kw_capacity,
                    'discom_id': order.solar_discom_id.id,
                    'date_start': order.date_order.date() if order.date_order else fields.Date.context_today(self),
                    'project_type': project_type,
                })
                order.solar_project_id = project.id

                # Automatically create project.project if the module is installed
                if 'project.project' in self.env:
                    project_obj = self.env['project.project'].search([('name', '=', order.name)], limit=1)
                    if not project_obj:
                        self.env['project.project'].with_context(default_tag_ids=False).create({
                            'name': order.name,
                            'partner_id': order.partner_id.id,
                        })
        return orders

    def write(self, vals):
        # Restrict editing on confirmed quotations
        if not self.env.context.get('bypass_edit_restriction'):
            for order in self:
                if order.state in ('sale', 'done'):
                    if not self.env.user.can_edit_confirmed_quotation:
                        allowed_fields = {'state', 'invoice_status', 'message_attachment_count', 'message_ids', 'activity_ids', 'activity_state', 'activity_type_id', 'activity_user_id', 'activity_date_deadline', 'activity_summary', 'activity_note'}
                        if not set(vals.keys()).issubset(allowed_fields):
                            raise UserError(_("You cannot edit a confirmed quotation/sales order. Only authorized users can make changes."))

        res = super(SaleOrder, self).write(vals)

        # Trigger project creation if opportunity is linked later
        if 'opportunity_id' in vals:
            for order in self:
                if order.opportunity_id and not order.solar_project_id:
                    project_type = 'ground_mounted'
                    if order.opportunity_id.tag_ids:
                        tag_names = [t.name.upper().strip() for t in order.opportunity_id.tag_ids]
                        if 'COMMERCIAL' in tag_names or 'COMMERCIAL / INDUSTRIAL' in tag_names:
                            project_type = 'commercial'

                    project = self.env['solar.project'].create({
                        'partner_id': order.partner_id.id,
                        'sale_order_id': order.id,
                        'kw_capacity': order.solar_kw_capacity,
                        'discom_id': order.solar_discom_id.id,
                        'date_start': order.date_order.date() if order.date_order else fields.Date.context_today(self),
                        'project_type': project_type,
                    })
                    order.with_context(bypass_edit_restriction=True).solar_project_id = project.id

                    if 'project.project' in self.env:
                        project_obj = self.env['project.project'].search([('name', '=', order.name)], limit=1)
                        if not project_obj:
                            self.env['project.project'].with_context(default_tag_ids=False).create({
                                'name': order.name,
                                'partner_id': order.partner_id.id,
                            })
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if not order.solar_project_id:
                # Determine project type from the linked Opportunity's lead tag
                project_type = 'ground_mounted'  # Default
                if order.opportunity_id and order.opportunity_id.tag_ids:
                    tag_names = [t.name.upper().strip() for t in order.opportunity_id.tag_ids]
                    if 'COMMERCIAL' in tag_names or 'COMMERCIAL / INDUSTRIAL' in tag_names:
                        project_type = 'commercial'

                # Create Project automatically
                project = self.env['solar.project'].create({
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                    'kw_capacity': order.solar_kw_capacity,
                    'discom_id': order.solar_discom_id.id,
                    'date_start': order.date_order.date(),
                    'project_type': project_type,
                })
                order.with_context(bypass_edit_restriction=True).solar_project_id = project.id
        return res

class SolarStagePermission(models.Model):
    _name = 'solar.stage.permission'
    _description = 'Solar Stage Permission'
    _order = 'sequence'

    name = fields.Char(string='Stage Name', required=True)
    code = fields.Char(string='Stage Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

class ResUsers(models.Model):
    _inherit = 'res.users'

    solar_stage_ids = fields.Many2many('solar.stage.permission', string='Solar Project Stage Permissions')
    can_edit_confirmed_quotation = fields.Boolean(string='Can Edit Confirmed Quotation', default=False)
