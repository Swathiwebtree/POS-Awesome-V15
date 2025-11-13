# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
# Import specific exceptions for better error handling
from frappe.exceptions import ValidationError, DoesNotExistError, NameError 

# The custom DocType name as per your system
VEHICLE_DOCTYPE = "Vehicle Master" 
CUSTOMER_DOCTYPE = "Customer"

# ============ POS Vehicle APIs ============

@frappe.whitelist()
def create_vehicle(
    vehicle_no, 
    customer, 
    model=None, 
    make=None, 
    chasis_no=None, 
    color=None, 
    registration_number=None, 
    mobile_no=None,
    method="create", 
    vehicle_id=None
):
    """
    Creates or updates a Vehicle Master record based on the 'method' parameter.
    
    FIX: Restructures error handling to explicitly re-raise Frappe validation 
    exceptions, preventing the BrokenPipeError during error response packaging.
    """
    
    # 1. Sanitize/Normalize inputs
    vehicle_no = (vehicle_no or '').upper().strip()
    customer = customer or ''
    
    # Use empty string for DocType fields if None is passed from frontend
    model = model or ''
    make = make or ''
    chasis_no = chasis_no or ''
    color = color or ''
    registration_number = registration_number or ''
    mobile_no = mobile_no or ''
    
    # 2. Aggressive Pre-Validation for required fields
    # This prevents the call from hitting the internal Frappe Naming logic 
    # if basic mandatory fields are missing (like the one used for DocType name).
    if not vehicle_no:
        frappe.throw(_("Vehicle No. is mandatory."), title=_("Validation Error"))
    if not customer:
        frappe.throw(_("Customer is mandatory."), title=_("Validation Error"))


    # We use a try block specifically around document operations
    try:
        if method == "create":
            # Check for existing vehicle using vehicle_no as the unique key
            if frappe.db.exists(VEHICLE_DOCTYPE, vehicle_no):
                 frappe.throw(_("Vehicle No. {0} already exists in the system.").format(vehicle_no), title=_("Already Exists"))

            # Create a new document dictionary
            doc_data = {
                "doctype": VEHICLE_DOCTYPE,
                # Setting 'name' is crucial if the DocType is configured for AutoName: field:vehicle_no
                "customer": customer,
                "vehicle_no": vehicle_no, 
                "model": model,
                "make": make,
                "chasis_no": chasis_no,
                "color": color,
                "registration_number": registration_number,
                "mobile_no": mobile_no,
            }
            
            # Insert the new document (ignore_mandatory=True removed for better validation)
            vehicle = frappe.get_doc(doc_data)
            vehicle.insert(ignore_permissions=True)
            
        elif method == "update" and vehicle_id:
            # Update an existing document
            vehicle = frappe.get_doc(VEHICLE_DOCTYPE, vehicle_id)
            
            # Update fields based on incoming data 
            vehicle.customer = customer
            vehicle.model = model
            vehicle.make = make
            vehicle.chasis_no = chasis_no
            vehicle.color = color
            vehicle.registration_number = registration_number
            vehicle.mobile_no = mobile_no
            
            # Save the document (ignore_mandatory=True removed for better validation)
            vehicle.save(ignore_permissions=True)
            
        else:
            frappe.throw(_("Invalid method or missing vehicle ID for update."), title=_("API Error"))

        # Commit changes and return the document
        frappe.db.commit()
        return vehicle.as_dict()

    # CRITICAL FIX: Explicitly catch Frappe-specific exceptions and re-raise them.
    # This pattern lets the Frappe framework handle the response properly.
    except (ValidationError, DoesNotExistError, NameError) as e:
        # Log the error for server-side debugging
        frappe.log_error(message=frappe.get_traceback(), title="POS Awesome Validation/Data Error")
        # Re-raise the original Frappe exception immediately
        raise

    except Exception as e:
        # Catch all other unexpected errors
        frappe.log_error(message=frappe.get_traceback(), title="POS Awesome Vehicle API General Error")
        # Throw a simple, generic error message only as a last resort
        frappe.throw(_("An unexpected server error occurred while processing the vehicle request."), title=_("Server Error"))

@frappe.whitelist()
def get_vehicle_and_customer(vehicle_no):
    """
    Fetches vehicle and linked customer data based on vehicle_no.
    """
    if not vehicle_no:
        return {}
        
    vehicle_no = vehicle_no.strip()
    vehicle = {} # Initialize vehicle dictionary

    try:
        # 1. Try to get the vehicle document
        vehicle_doc = frappe.get_doc(VEHICLE_DOCTYPE, vehicle_no)
        vehicle = vehicle_doc.as_dict()
        
        customer_name = vehicle.get("customer")
        cust_doc = frappe.new_doc(CUSTOMER_DOCTYPE) # Default to an empty customer doc
        
        # 2. Try to fetch the linked customer document if the link field is populated
        if customer_name:
            try:
                cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, customer_name)
            except DoesNotExistError:
                frappe.log_error(
                    f"Customer {customer_name} linked to Vehicle {vehicle_no} does not exist.",
                    "Vehicle Lookup - Missing Customer"
                )
                # Keep cust_doc as a new empty document to prevent subsequent errors
        
        # 3. Compile the response data
        return {
            "vehicle": {
                "name": vehicle.get("name"),
                "vehicle_no": vehicle.get("vehicle_no"),
                "model": vehicle.get("model"),
                "make": vehicle.get("make"),
                "chasis_no": vehicle.get("chasis_no"),
                "color": vehicle.get("color"),
                "registration_number": vehicle.get("registration_number"),
                "mobile_no": vehicle.get("mobile_no"),
            },
            "customer": {
                "name": cust_doc.name,
                "customer_name": getattr(cust_doc, "customer_name", ""),
                "email_id": getattr(cust_doc, "email_id", ""),
                "mobile_no": getattr(cust_doc, "mobile_no", ""),
                "tax_id": getattr(cust_doc, "tax_id", ""),
                "customer_group": getattr(cust_doc, "customer_group", ""),
                "territory": getattr(cust_doc, "territory", ""),
                "posa_discount": getattr(cust_doc, "posa_discount", 0),
            },
        }
    except DoesNotExistError:
        # Handles case where the Vehicle Master document itself is missing
        return {"vehicle": {"vehicle_no": vehicle_no}, "customer": {}}
        
    except Exception:
        # Catches other unexpected errors
        frappe.log_error(frappe.get_traceback(), "Vehicle Lookup Error - General Failure")
        return {}

@frappe.whitelist()
def get_all_vehicles_for_customer(customer_name):
    """
    Get all vehicles for a customer (no pagination).
    """
    # ... (Keep the rest of the function body)
    if not customer_name:
        return []
    
    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"customer": customer_name},
        fields=[
            "name",
            "vehicle_no",
            "model",
            "make",
            "chasis_no",
            "mobile_no", 
            "customer",
        ],
        order_by="creation desc",
    )
    return vehicles

@frappe.whitelist()
def search_vehicles(search_term, limit=50):
    """
    Search vehicles by: 1. vehicle_no (license plate) 2. Customer mobile_no
    """
    if not search_term or len(search_term) < 2:
        frappe.throw(_("Search term must be at least 2 characters"))
    
    search_term = search_term.strip()
    
    vehicles_by_number = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"vehicle_no": ["like", f"%{search_term}%"]},
        fields=["name", "vehicle_no", "customer", "model", "chasis_no", "make", "mobile_no"],
        limit_page_length=int(limit),
    )
    return vehicles_by_number



@frappe.whitelist()
def get_vehicles_by_customer(customer_name, limit=200, start_after=None):
	"""
	Fetch vehicles for a given customer with pagination.
	Returns vehicles with customer details including mobile_no.
	"""
	
	if not customer_name:
		frappe.throw(_("Customer name is required"))
	
	limit = int(limit) if limit else 200
	
	filters = {"customer": customer_name}
	
	if start_after:
		filters["name"] = [">", start_after]
	
	try:
		# Get customer details first (for mobile_no and customer_name)
		cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, customer_name)
		
		vehicles = frappe.get_all(
			VEHICLE_DOCTYPE,
			filters=filters,
			fields=[
				"name",
				"customer", 
				"vehicle_no",
				"model",
				"make",
				"chasis_no",
			],
			order_by="name asc",
			limit_page_length=limit,
		)
		
		# Enrich all vehicles with customer details
		for row in vehicles:
			row.setdefault('vehicle_no', row.get('name', ''))
			row.setdefault('model', '')
			row.setdefault('make', '')
			row.setdefault('chasis_no', '')
			row['customer'] = customer_name
			row['customer_name'] = cust_doc.customer_name
			row['mobile_no'] = cust_doc.mobile_no or ""
			row['email_id'] = cust_doc.email_id or ""
			row['tax_id'] = cust_doc.tax_id or ""
		
		frappe.logger().debug(f"Found {len(vehicles)} vehicles for customer: {customer_name}")
		
		return vehicles
		
	except frappe.DoesNotExistError:
		frappe.log_error(f"Customer not found: {customer_name}", "Vehicle Fetch Error")
		return []
	except Exception as e:
		frappe.logger().error(f"Error fetching vehicles for {customer_name}: {str(e)}")
		frappe.throw(_("Error fetching vehicles: {0}").format(str(e)))


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
	"""
	Return customer details for a vehicle number (exact match).
	Includes mobile_no and other customer details.
	"""
	
	if not vehicle_no:
		frappe.throw(_("Vehicle number is required"))
	
	try:
		vehicle_data = frappe.get_all(
			VEHICLE_DOCTYPE,
			filters={"vehicle_no": vehicle_no},
			fields=["name", "customer", "model", "make", "chasis_no", "vehicle_no"],
			limit_page_length=1,
		)
		
		if not vehicle_data:
			return {}
			
		vehicle = vehicle_data[0]
		cust_name = vehicle.get("customer")
		
		if not cust_name:
			return {"vehicle": vehicle, "customer": {}}
		
		try:
			cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, cust_name)
			return {
				"vehicle": {
					"name": vehicle.get("name"),
					"vehicle_no": vehicle.get("vehicle_no"),
					"model": vehicle.get("model"),
					"make": vehicle.get("make"),
					"chasis_no": vehicle.get("chasis_no"),
				},
				"customer": {
					"name": cust_doc.name,
					"customer_name": cust_doc.customer_name,
					"email_id": getattr(cust_doc, "email_id", ""),
					"mobile_no": getattr(cust_doc, "mobile_no", ""),
					"tax_id": getattr(cust_doc, "tax_id", ""),
					"customer_group": getattr(cust_doc, "customer_group", ""),
					"territory": getattr(cust_doc, "territory", ""),
					"posa_discount": getattr(cust_doc, "posa_discount", 0),
				},
			}
		except frappe.DoesNotExistError:
			return {"vehicle": vehicle, "customer": {}}
			
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Vehicle Lookup Error")
		return {}

@frappe.whitelist()
def get_vehicle_models(search_term=""):
    """
    Search and return a distinct list of Vehicle Model names for autocomplete.
    """
    filters = {}
    if search_term:
        # Correctly format filter for a single field search
        filters = [["model", "like", f"%{search_term}%"]]

    models = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters=filters,
        fields=["DISTINCT model"],
        order_by="model asc",
        limit_page_length=20
    )
    
    # Return a list of strings (model names)
    return [d.get("model") for d in models if d.get("model")]
