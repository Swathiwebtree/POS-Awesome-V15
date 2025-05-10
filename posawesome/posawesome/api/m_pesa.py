# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests
from frappe import _
from requests.auth import HTTPBasicAuth
import json
from frappe.utils import now, add_to_date, get_datetime
from requests.exceptions import Timeout, RequestException


def get_token(app_key, app_secret, base_url, timeout=30):
    try:
        auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(
            auth_url,
            auth=(app_key, app_secret),
            timeout=timeout
        )
        r.raise_for_status()  # Raise exception for non-200 status codes
        return r.json().get("access_token")
    except Timeout:
        frappe.log_error("Mpesa API token request timed out", "Mpesa Token Error")
        raise frappe.ValidationError(_("Failed to connect to Mpesa. Please try again later."))
    except RequestException as e:
        frappe.log_error(f"Mpesa API token request failed: {str(e)}", "Mpesa Token Error")
        raise frappe.ValidationError(_("Failed to authenticate with Mpesa. Please check your settings."))


@frappe.whitelist(allow_guest=True)
def confirmation(**kwargs):
    try:
        args = frappe._dict(kwargs)
        doc = frappe.new_doc("Mpesa Payment Register")
        doc.transactiontype = args.get("TransactionType")
        doc.transid = args.get("TransID")
        doc.transtime = args.get("TransTime")
        doc.transamount = args.get("TransAmount")
        doc.businessshortcode = args.get("BusinessShortCode")
        doc.billrefnumber = args.get("BillRefNumber")
        doc.invoicenumber = args.get("InvoiceNumber")
        doc.orgaccountbalance = args.get("OrgAccountBalance")
        doc.thirdpartytransid = args.get("ThirdPartyTransID")
        doc.msisdn = args.get("MSISDN")
        doc.firstname = args.get("FirstName")
        doc.middlename = args.get("MiddleName")
        doc.lastname = args.get("LastName")
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        context = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return dict(context)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), str(e)[:140])
        context = {"ResultCode": 1, "ResultDesc": "Rejected"}
        return dict(context)


@frappe.whitelist(allow_guest=True)
def validation(**kwargs):
    context = {"ResultCode": 0, "ResultDesc": "Accepted"}
    return dict(context)


@frappe.whitelist()
def get_mpesa_mode_of_payment(company):
    modes = frappe.get_all(
        "Mpesa C2B Register URL",
        filters={"company": company, "register_status": "Success"},
        fields=["mode_of_payment"],
    )
    modes_of_payment = []
    for mode in modes:
        if mode.mode_of_payment not in modes_of_payment:
            modes_of_payment.append(mode.mode_of_payment)
    return modes_of_payment


@frappe.whitelist()
def get_mpesa_draft_payments(
    company=None,
    mode_of_payment=None,
    full_name=None,
    mobile_no=None,
    timeout=30
):
    try:
        filters = {
            "docstatus": 0,
            "submit_payment": 1
        }
        
        if company:
            filters["company"] = company
        if mode_of_payment:
            filters["mode_of_payment"] = mode_of_payment
        if full_name:
            filters["full_name"] = ["like", f"%{full_name}%"]
        if mobile_no:
            filters["mobile_no"] = ["like", f"%{mobile_no}%"]
            
        return frappe.get_all(
            "Mpesa Payment Register",
            filters=filters,
            fields=["name", "transaction_date", "full_name", "mobile_no", "amount"],
            order_by="transaction_date desc",
            timeout=timeout
        )
        
    except Timeout:
        frappe.log_error("Mpesa draft payments query timed out", "Mpesa Query Error")
        raise frappe.ValidationError(_("Request timed out. Please try again."))
    except Exception as e:
        frappe.log_error(f"Error fetching Mpesa draft payments: {str(e)}", "Mpesa Query Error")
        raise frappe.ValidationError(_("Failed to fetch payments: {0}").format(str(e)))


@frappe.whitelist()
def submit_mpesa_payment(payment_name, customer, timeout=30):
    try:
        if not payment_name:
            raise frappe.ValidationError(_("Payment reference is required"))
            
        payment_doc = frappe.get_doc("Mpesa Payment Register", payment_name)
        
        if payment_doc.docstatus != 0:
            raise frappe.ValidationError(_("Payment has already been processed"))
            
        if payment_doc.customer and payment_doc.customer != customer:
            raise frappe.ValidationError(_("Payment belongs to a different customer"))
        
        # Set timeout for payment processing
        payment_doc.flags.timeout = timeout
        
        # Submit the payment with timeout handling
        try:
            payment_doc.submit()
        except Exception as e:
            frappe.log_error(f"Failed to submit Mpesa payment {payment_name}: {str(e)}", "Mpesa Payment Error")
            raise frappe.ValidationError(_("Failed to process payment. Please try again."))
            
        return payment_doc.name
        
    except Timeout:
        frappe.log_error(f"Mpesa payment submission timed out for {payment_name}", "Mpesa Payment Error")
        raise frappe.ValidationError(_("Payment processing timed out. Please check status and try again if needed."))
    except Exception as e:
        frappe.log_error(f"Error processing Mpesa payment {payment_name}: {str(e)}", "Mpesa Payment Error")
        raise frappe.ValidationError(_("Failed to process payment: {0}").format(str(e)))
