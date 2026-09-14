# -*- coding: utf-8 -*-
from odoo import models

class L10nInEwaybill(models.Model):
    _inherit = "l10n.in.ewaybill"

    def _get_l10n_in_ewaybill_line_details(self, line, tax_details):
        res = super()._get_l10n_in_ewaybill_line_details(line, tax_details)
        
        # Apply the fix: Ensure qtyUnit is max 3 chars
        qty_unit = res.get('qtyUnit', 'OTH')
        if len(str(qty_unit)) > 3:
            # Attempt to extract from UOM if possible, otherwise default to OTH
            uom_code = line.product_uom_id.l10n_in_code
            if uom_code:
                code_part = uom_code.split("-")[0]
                if len(code_part) <= 3:
                    res['qtyUnit'] = code_part
                else:
                    res['qtyUnit'] = 'OTH'
            else:
                res['qtyUnit'] = 'OTH'
        
        return res
