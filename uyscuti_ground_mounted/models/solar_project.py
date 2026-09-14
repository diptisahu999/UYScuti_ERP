# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError, ValidationError


class SolarProject(models.Model):
    _inherit = 'solar.project'



    # Stage 2: Project Apply
    gm_project_apply_date = fields.Date(string='Project Apply Date')

    # Stage 3: Discom Application
    gm_discom_app_date = fields.Date(string='Discom Application Date')

    # Stage 4: Akshay Urja Connectivity Apply
    gm_akshay_urja_date = fields.Date(string='Akshay Urja Connectivity Date')

    # Stage 5: Document Submit
    gm_doc_submit_date = fields.Date(string='Document Submission Date')
    # Stage 5 Documents Checklist
    gm_doc_work_completion = fields.Binary(string='Work Completion Certificate')
    gm_doc_work_completion_name = fields.Char(string='Work Completion Certificate Filename')
    gm_doc_ceig_approval = fields.Binary(string='CEIG Approval')
    gm_doc_ceig_approval_name = fields.Char(string='CEIG Approval Filename')
    gm_doc_ppa = fields.Binary(string='PPA')
    gm_doc_ppa_name = fields.Char(string='PPA Filename')
    gm_doc_abt_meter_inspection = fields.Binary(string='ABT Meter Inspection report')
    gm_doc_abt_meter_inspection_name = fields.Char(string='ABT Meter Inspection Filename')
    gm_doc_ctpt_inspection = fields.Binary(string='CTPT Inspection report')
    gm_doc_ctpt_inspection_name = fields.Char(string='CTPT Inspection Filename')
    gm_doc_abt_meter_test = fields.Binary(string='ABT Meter test report')
    gm_doc_abt_meter_test_name = fields.Char(string='ABT Meter test Filename')
    gm_doc_line_sanction = fields.Binary(string='Line Sanction Letter')
    gm_doc_line_sanction_name = fields.Char(string='Line Sanction Filename')
    gm_doc_rrecl_registration = fields.Binary(string='RRECL Registration')
    gm_doc_rrecl_registration_name = fields.Char(string='RRECL Registration Filename')
    gm_doc_meter_plan_approval = fields.Binary(string='Meter Plan Approval Letter')
    gm_doc_meter_plan_approval_name = fields.Char(string='Meter Plan Approval Filename')
    gm_doc_trans_test_report = fields.Binary(string='Transformer Test Report')
    gm_doc_trans_test_report_name = fields.Char(string='Transformer Test Filename')
    gm_doc_inv_test_report = fields.Binary(string='Inverter test report')
    gm_doc_inv_test_report_name = fields.Char(string='Inverter test Filename')
    gm_doc_line_material_test = fields.Binary(string='Line Material Test Certificate')
    gm_doc_line_material_test_name = fields.Char(string='Line Material Test Filename')
    gm_doc_approved_sld = fields.Binary(string='Approved SLD')
    gm_doc_approved_sld_name = fields.Char(string='Approved SLD Filename')
    # Stage 5 Multiple Photos Checklist
    gm_doc_photo_ids = fields.One2many('solar.project.doc.photo', 'project_id', string='Stage 5 Photos')

    # Stage 6: Fees Payment
    gm_fees_pay_date = fields.Date(string='Fees Payment Date')
    gm_fees_amount = fields.Float(string='Fees Amount')
    gm_fees_receipt = fields.Binary(string='Fees Paid Receipt')
    gm_fees_receipt_name = fields.Char(string='Fees Paid Receipt Filename')
    # Stage 6 Invoices Checklist
    gm_invoice_trans = fields.Binary(string='Transformer Invoice')
    gm_invoice_trans_name = fields.Char(string='Transformer Invoice Filename')
    gm_invoice_inv = fields.Binary(string='Inverter Invoice')
    gm_invoice_inv_name = fields.Char(string='Inverter Invoice Filename')
    gm_invoice_module = fields.Binary(string='Module Invoice')
    gm_invoice_module_name = fields.Char(string='Module Invoice Filename')
    gm_invoice_line = fields.Binary(string='Line Material Invoice')
    gm_invoice_line_name = fields.Char(string='Line Material Invoice Filename')
    gm_invoice_rms = fields.Binary(string='RMS Invoice')
    gm_invoice_rms_name = fields.Char(string='RMS Invoice Filename')

    # Stage 7: Approval
    gm_approval_date = fields.Date(string='Approval Date')
    gm_approval_letter = fields.Binary(string='Approval Letter')
    gm_approval_letter_name = fields.Char(string='Approval Letter Filename')

    # Stage 8: Discom Agreement
    gm_discom_agreement_date = fields.Date(string='Discom Agreement Date')
    gm_discom_agreement_doc = fields.Binary(string='Discom Agreement Document')
    gm_discom_agreement_doc_name = fields.Char(string='Discom Agreement Filename')

    # Stage 9: Land
    gm_land_area_acres = fields.Float(string='Land Area (Acres)')
    gm_land_clearance_date = fields.Date(string='Land Clearance/Survey Date')
    gm_land_survey_no = fields.Char(string='Land Survey Number')
    gm_land_document = fields.Binary(string='Land Survey/Registry Document')
    gm_land_document_name = fields.Char(string='Land Document Filename')

    # Stage 10: Design
    gm_design_date = fields.Date(string='Design Finalization Date')
    gm_design_layout_dwg = fields.Binary(string='PV Syst/Autocad Design Layout')
    gm_design_layout_dwg_name = fields.Char(string='Layout Filename')
    gm_design_approved_by = fields.Char(string='Designing Engineer / Approved By')
    gm_design_image_ids = fields.One2many('solar.project.design.image', 'project_id', string='Design Images')

    # Stage 11: BOM
    gm_bom_date = fields.Date(string='BOM Creation Date')
    gm_bom_sheet = fields.Binary(string='Bill of Materials Sheet')
    gm_bom_sheet_name = fields.Char(string='BOM Sheet Filename')
    gm_bom_cost_est = fields.Float(string='Estimated BOM Cost')

    # Stage 12: Vendor Selection
    gm_vendor_select_date = fields.Date(string='Vendor Selection Date')
    gm_selected_vendor_id = fields.Many2one('res.partner', string='Selected Vendor')
    gm_purchase_order_ref = fields.Char(string='Purchase Order Reference')
    gm_po_amount = fields.Float(string='PO Amount')
    gm_po_document = fields.Binary(string='PO Copy')
    gm_po_document_name = fields.Char(string='PO Filename')

    # Stage 13: Store Incharge Manager
    gm_store_incharge_date = fields.Date(string='Material Receipt/Store Inward Date')
    gm_store_manager = fields.Char(string='Store Manager Name')
    gm_store_remarks = fields.Text(string='Store Inward Remarks')
    gm_inward_delivery_challan = fields.Binary(string='Inward Delivery Challan')
    gm_inward_delivery_challan_name = fields.Char(string='Challan Filename')

    # Stage 14: Authorised Person
    gm_authorised_person_date = fields.Date(string='Authorization/Handover Date')
    gm_authorised_person_name = fields.Char(string='Authorised Person Name')
    gm_authorised_person_id = fields.Many2one('res.users', string='Authorised Internal User')
    gm_auth_letter = fields.Binary(string='Authorisation Letter')
    gm_auth_letter_name = fields.Char(string='Authorisation Letter Filename')

    # Stage 15: MMS Report (25%)
    gm_mms_report_date = fields.Date(string='MMS Pile/Civil Work 25% Date')
    gm_mms_pile_count = fields.Integer(string='Number of Piles Completed')
    gm_mms_report_file = fields.Binary(string='25% Completion MMS Report')
    gm_mms_report_file_name = fields.Char(string='MMS Report Filename')

    # Stage 16: Blockwise Reconcile
    gm_reconcile_date = fields.Date(string='Reconciliation Date')
    gm_reconcile_status = fields.Selection([
        ('draft', 'Draft'),
        ('reconciled', 'Reconciled'),
        ('error', 'Error'),
    ], string='Reconciliation Status', default='draft')
    gm_reconcile_sheet = fields.Binary(string='Blockwise Reconciliation Sheet')
    gm_reconcile_sheet_name = fields.Char(string='Reconciliation Sheet Filename')

    # Stage 17: Tasklist
    gm_tasklist_date = fields.Date(string='Tasklist Review Date')
    gm_task_checklist_text = fields.Text(string='Remaining Task Checklist/Punch Points')
    gm_tasklist_doc = fields.Binary(string='Punch List / Tasklist Document')
    gm_tasklist_doc_name = fields.Char(string='Tasklist Document Filename')

    # Stage 18: QC
    gm_qc_date = fields.Date(string='Quality Control Inspection Date')
    gm_qc_status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional'),
    ], string='QC Status', default='pass')
    gm_qc_inspector = fields.Char(string='QC Inspector Name')
    gm_qc_report = fields.Binary(string='Final QC Inspection Report')
    gm_qc_report_name = fields.Char(string='QC Report Filename')

    def action_next_stage(self):
        self.ensure_one()
        if self.project_type == 'ground_mounted':
            selection = [s[0] for s in self._fields['state'].selection]
            current_index = selection.index(self.state)
            if current_index + 1 < len(selection):
                self.state = selection[current_index + 1]
            return True
        else:
            return super(SolarProject, self).action_next_stage()

class SolarProjectPhotoType(models.Model):
    _name = 'solar.project.photo.type'
    _description = 'Solar Project Photo Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Photo type name must be unique!'),
    ]

class SolarProjectDocPhoto(models.Model):
    _name = 'solar.project.doc.photo'
    _description = 'Solar Project Document Photos'

    project_id = fields.Many2one('solar.project', string='Project', ondelete='cascade')
    photo = fields.Binary(string='Photo', required=True)
    photo_name = fields.Char(string='Filename')
    photo_type_id = fields.Many2one('solar.project.photo.type', string='Photo Type', required=True)
    description = fields.Char(string='Description')



class SolarProjectDesignImage(models.Model):
    _name = 'solar.project.design.image'
    _description = 'Solar Project Design Images'

    project_id = fields.Many2one('solar.project', string='Project', ondelete='cascade')
    image = fields.Binary(string='Design Image', required=True)
    image_name = fields.Char(string='Filename')
    description = fields.Char(string='Description')
