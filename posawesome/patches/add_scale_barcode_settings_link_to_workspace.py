import frappe

WORKSPACE_NAME = "POS Awesome"
# Use a standard, known DocType for diagnostics
DOCTYPE_NAME = "User"
PROFILE_CARD_LABEL = "Profile"


def execute():
    frappe.log_message("--- Starting Diagnostic Patch ---", "POSAwesome Patch")

    # 1. Ensure the workspace and doctype exist
    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        frappe.log_message(
            f"Workspace '{WORKSPACE_NAME}' not found. Skipping patch.", "POSAwesome Patch"
        )
        return

    if not frappe.db.exists("DocType", DOCTYPE_NAME):
        frappe.log_message(
            f"Diagnostic DocType '{DOCTYPE_NAME}' not found. This should not happen. Skipping patch.",
            "POSAwesome Patch",
        )
        return

    workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
    links = workspace.links
    existing_link = None

    # 2. Check if the link already exists
    for link in links:
        if link.link_to == DOCTYPE_NAME:
            existing_link = link
            break

    if existing_link:
        # 3. If link exists, ensure it's visible
        frappe.log_message(
            f"Diagnostic link for '{DOCTYPE_NAME}' already exists. Checking visibility.",
            "POSAwesome Patch",
        )
        if existing_link.hidden:
            existing_link.hidden = 0
            frappe.log_message("Link was hidden. Unhiding now.", "POSAwesome Patch")
        else:
            frappe.log_message("Link is already visible.", "POSAwesome Patch")
    else:
        # 4. If link does not exist, add it
        frappe.log_message(
            f"Diagnostic link for '{DOCTYPE_NAME}' not found. Adding now.", "POSAwesome Patch"
        )
        profile_card_index = -1
        for i, link in enumerate(links):
            if link.type == "Card Break" and link.label == PROFILE_CARD_LABEL:
                profile_card_index = i
                break

        new_link_data = {
            "type": "Link",
            "label": DOCTYPE_NAME,
            "link_to": DOCTYPE_NAME,
            "link_type": "DocType",
            "hidden": 0,
        }

        if profile_card_index != -1:
            links.insert(profile_card_index + 1, new_link_data)
        else:
            # Fallback to appending at the end
            links.append(new_link_data)

    # Re-index all links to maintain order
    for idx, link in enumerate(links, start=1):
        link.idx = idx

    try:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.clear_cache()
        frappe.clear_website_cache()
        frappe.log_message(
            f"--- Diagnostic Patch Finished Successfully ---", "POSAwesome Patch"
        )
    except Exception as e:
        frappe.log_error(
            f"Failed to save workspace during diagnostic: {e}", "POSAwesome Patch Error"
        )
