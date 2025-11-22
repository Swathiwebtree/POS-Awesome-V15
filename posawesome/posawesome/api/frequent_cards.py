import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_customer_frequent_cards(customer, company=None):
    """Get all frequent customer cards for a customer"""
    filters = {"customer": customer, "docstatus": ["in", [0, 1]], "status": ["in", ["Active", "Completed"]]}

    if company:
        filters["company"] = company

    cards = frappe.get_all(
        "Frequent Customer Card",
        filters=filters,
        fields=[
            "name",
            "card_name",
            "service_item",
            "service_item_name",
            "visits",
            "required_visits",
            "issue_date",
            "expiry_date",
            "status",
        ],
        order_by="expiry_date desc",
    )

    # Check and update expired cards
    today = datetime.now().date()
    for card in cards:
        expiry = datetime.strptime(str(card.expiry_date), "%Y-%m-%d").date()
        card["is_expired"] = expiry < today

        # Auto-update status if expired
        if card["is_expired"] and card["status"] != "Expired":
            frappe.db.set_value("Frequent Customer Card", card["name"], "status", "Expired")

    return cards


@frappe.whitelist()
def apply_free_service(card_name, customer, service_item):
    """Apply free service from a completed frequent card"""
    try:
        card = frappe.get_doc("Frequent Customer Card", card_name)

        # Validate card
        if card.customer != customer:
            frappe.throw(_("Invalid card for this customer"))

        if card.status == "Expired":
            frappe.throw(_("This card has expired"))

        if card.status == "Redeemed":
            frappe.throw(_("This card has already been redeemed"))

        if card.visits < card.required_visits:
            frappe.throw(_("Not enough visits to redeem this card"))

        # Check expiry
        today = datetime.now().date()
        expiry = datetime.strptime(str(card.expiry_date), "%Y-%m-%d").date()
        if expiry < today:
            card.status = "Expired"
            card.save()
            frappe.throw(_("This card has expired"))

        # Mark as redeemed (will be finalized when invoice is submitted)
        card.status = "Redeemed"
        card.redeemed_on = datetime.now()
        card.save()

        return {
            "status": "success",
            "message": _("Free service applied successfully"),
            "card": card.as_dict(),
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Frequent Card Apply Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def create_or_update_card(customer, service_item, company=None):
    """Create a new card or increment visits on existing active card"""

    # Check for existing active card
    existing_cards = frappe.get_all(
        "Frequent Customer Card",
        filters={
            "customer": customer,
            "service_item": service_item,
            "status": ["in", ["Active", "Completed"]],
            "expiry_date": [">=", datetime.now().date()],
        },
        order_by="creation desc",
        limit=1,
    )

    if existing_cards:
        # Increment visits on existing card
        card = frappe.get_doc("Frequent Customer Card", existing_cards[0].name)
        card.visits += 1

        if card.visits >= card.required_visits:
            card.status = "Completed"

        card.save()
        return {"status": "updated", "card": card.as_dict(), "message": _("Visit added to existing card")}
    else:
        # Create new card
        item = frappe.get_doc("Item", service_item)

        # Default expiry: 6 months from now
        expiry_date = (datetime.now() + timedelta(days=180)).date()

        card = frappe.get_doc(
            {
                "doctype": "Frequent Customer Card",
                "customer": customer,
                "service_item": service_item,
                "service_item_name": item.item_name,
                "card_name": f"{item.item_name} - Frequent Card",
                "visits": 1,
                "required_visits": 3,
                "issue_date": datetime.now().date(),
                "expiry_date": expiry_date,
                "company": company,
                "status": "Active",
            }
        )
        card.insert()

        return {"status": "created", "card": card.as_dict(), "message": _("New frequent card created")}


@frappe.whitelist()
def check_auto_apply_card(customer, service_item):
    """Check if there's a completed card that can be auto-applied"""

    cards = frappe.get_all(
        "Frequent Customer Card",
        filters={
            "customer": customer,
            "service_item": service_item,
            "status": "Completed",
            "expiry_date": [">=", datetime.now().date()],
        },
        fields=["name", "visits", "required_visits"],
        order_by="creation asc",
        limit=1,
    )

    if cards and cards[0].visits >= cards[0].required_visits:
        return {"has_card": True, "card_name": cards[0].name}

    return {"has_card": False}
