# -*- coding: utf-8 -*-
# Custom hooks for Sales Invoice to skip due_date validation when needed

import frappe
from frappe.utils import getdate

def validate_sales_invoice(doc, method):
    """
    Custom validation that skips due_date check for POS invoices
    when the posa_skip_due_date_validation flag is set
    """
    # If this is a POS invoice with the skip flag, bypass due_date validation
    if hasattr(doc, 'flags') and getattr(doc.flags, 'posa_skip_due_date_validation', False):
        frappe.logger().info(f"Skipping due_date validation for POS invoice {doc.name}")
        # Ensure due_date is at least posting_date
        posting_date = getdate(doc.posting_date) if doc.posting_date else getdate(frappe.utils.nowdate())
        try:
            due_date = getdate(doc.due_date) if doc.due_date else posting_date
        except:
            due_date = posting_date
        
        if due_date < posting_date:
            doc.due_date = posting_date
        return  # Skip the rest of validation
    
    # For non-POS or when flag is not set, continue normally
    pass