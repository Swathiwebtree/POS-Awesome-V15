import frappe

WORKSPACE_NAME = "POS Awesome"
DOCTYPE_NAME = "Scale Barcode Settings"
PROFILE_CARD_LABEL = "Profile"


def execute():
    # 1. Ensure the workspace and doctype exist
    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        frappe.log_message(
            f"Workspace '{WORKSPACE_NAME}' not found. Skipping patch.", "POSAwesome Patch"
        )
        return

    if not frappe.db.exists("DocType", DOCTYPE_NAME):
        frappe.log_message(
            f"DocType '{DOCTYPE_NAME}' not found. Skipping patch.", "POSAwesome Patch"
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
        if existing_link.hidden:
            existing_link.hidden = 0
            frappe.log_message(
                f"Unhiding existing link for '{DOCTYPE_NAME}' in '{WORKSPACE_NAME}'.",
                "POSAwesome Patch",
            )
        else:
            frappe.log_message(
                f"Link for '{DOCTYPE_NAME}' already exists and is visible.",
                "POSAwesome Patch",
            )
            # No changes needed if it's already visible
            return
    else:
        # 4. If link does not exist, add it after the 'Profile' card
        frappe.log_message(
            f"Adding link for '{DOCTYPE_NAME}' to '{WORKSPACE_NAME}'.", "POSAwesome Patch"
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
            # Insert after the profile card for better organization
            links.insert(profile_card_index + 1, new_link_data)
        else:
            # Fallback to appending at the end
            links.append(new_link_data)

    # Re-index all links to maintain order
    for idx, link in enumerate(links, start=1):
        link.idx = idx

    try:
        workspace.save(ignore_permissions=True)
        # 5. Clear cache to ensure changes are reflected immediately
        frappe.clear_cache()
        frappe.clear_website_cache()
        frappe.log_message(
            f"Successfully updated workspace '{WORKSPACE_NAME}' and cleared cache.",
            "POSAwesome Patch",
        )
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            f"Failed to save workspace '{WORKSPACE_NAME}': {e}", "POSAwesome Patch Error"
        )
