import json

import frappe


SHORTCUT_LABEL = "Scale Barcode Settings"
SHORTCUT_ID = "ScaleBarcodeShortcut"
SCALE_CARD_LABEL = "Scale Barcode"
SCALE_CARD_ID = "ScaleBarcodeCard"


def execute():
    if not frappe.db.table_exists("Workspace"):
        return

    if not frappe.db.exists("DocType", SHORTCUT_LABEL):
        return

    if not frappe.db.exists("Workspace", "POS Awesome"):
        return

    workspace = frappe.get_doc("Workspace", "POS Awesome")

    changed = False

    changed |= ensure_shortcut(workspace)
    changed |= ensure_links(workspace)
    changed |= ensure_content(workspace)

    if changed:
        workspace.save(ignore_permissions=True)
        frappe.clear_cache(doctype="Workspace")


def ensure_shortcut(workspace):
    shortcuts = workspace.shortcuts or []
    existing = next((s for s in shortcuts if s.link_to == SHORTCUT_LABEL), None)

    updated = False

    if not existing:
        workspace.append(
            "shortcuts",
            {
                "label": SHORTCUT_LABEL,
                "link_to": SHORTCUT_LABEL,
                "type": "DocType",
                "doc_view": "",
                "color": "Grey",
            },
        )
        shortcuts = workspace.shortcuts or []
        existing = next((s for s in shortcuts if s.link_to == SHORTCUT_LABEL), None)
        updated = True

    if existing and existing.doc_view not in ("", None):
        existing.doc_view = ""
        updated = True

    for idx, shortcut in enumerate(workspace.shortcuts or [], start=1):
        if shortcut.idx != idx:
            shortcut.idx = idx
            updated = True

    return updated


def ensure_links(workspace):
    links = workspace.links or []

    existing = next(
        (
            link
            for link in links
            if link.type == "Link" and link.link_to == SHORTCUT_LABEL
        ),
        None,
    )

    updated = False

    if not existing:
        workspace.append(
            "links",
            {
                "type": "Link",
                "label": SHORTCUT_LABEL,
                "link_to": SHORTCUT_LABEL,
                "link_type": "DocType",
                "link_count": 0,
                "hidden": 0,
                "is_query_report": 0,
                "onboard": 0,
            },
        )
        links = workspace.links or []
        existing = next(
            (
                link
                for link in links
                if link.type == "Link" and link.link_to == SHORTCUT_LABEL
            ),
            None,
        )
        updated = True

    scale_card = next(
        (
            link
            for link in links
            if link.type == "Card Break" and link.label == SCALE_CARD_LABEL
        ),
        None,
    )

    if not scale_card:
        workspace.append(
            "links",
            {
                "type": "Card Break",
                "label": SCALE_CARD_LABEL,
                "link_count": 0,
                "hidden": 0,
                "is_query_report": 0,
                "onboard": 0,
            },
        )
        links = workspace.links or []
        scale_card = next(
            (
                link
                for link in links
                if link.type == "Card Break" and link.label == SCALE_CARD_LABEL
            ),
            None,
        )
        updated = True

    if scale_card:
        shift_card = next(
            (
                link
                for link in links
                if link.type == "Card Break" and link.label == "Shift"
            ),
            None,
        )

        closing_shift_link = next(
            (
                link
                for link in links
                if link.type == "Link" and link.link_to == "POS Closing Shift"
            ),
            None,
        )

        opening_shift_link = next(
            (
                link
                for link in links
                if link.type == "Link" and link.link_to == "POS Opening Shift"
            ),
            None,
        )

        insert_after = None
        if closing_shift_link:
            insert_after = closing_shift_link
        elif opening_shift_link:
            insert_after = opening_shift_link
        elif shift_card:
            insert_after = shift_card

        if insert_after:
            desired_index = links.index(insert_after) + 1
            current_index = links.index(scale_card)
            if current_index != desired_index:
                card_break = links.pop(current_index)
                if current_index < desired_index:
                    desired_index -= 1
                links.insert(desired_index, card_break)
                updated = True

    if existing and scale_card:
        desired_index = links.index(scale_card) + 1
        current_index = links.index(existing)
        if current_index != desired_index:
            shortcut_link = links.pop(current_index)
            if current_index < desired_index:
                desired_index -= 1
            links.insert(desired_index, shortcut_link)
            updated = True

    for label in ("Profile", "Shift", SCALE_CARD_LABEL, "POS", "Delivery Charges", "Offers & Coupons"):
        updated |= _update_card_break_count(links, label)

    for idx, link in enumerate(workspace.links or [], start=1):
        if link.idx != idx:
            link.idx = idx
            updated = True

    return updated


def _update_card_break_count(links, label):
    card = next(
        (link for link in links if link.type == "Card Break" and link.label == label),
        None,
    )

    if not card:
        return False

    card_index = links.index(card)
    link_count = 0
    for link in links[card_index + 1 :]:
        if link.type == "Card Break":
            break
        if link.type == "Link":
            link_count += 1

    if card.link_count != link_count:
        card.link_count = link_count
        return True

    return False


def ensure_content(workspace):
    content_raw = workspace.content or "[]"

    try:
        content = json.loads(content_raw)
    except Exception:
        return False

    updated = False

    updated |= _ensure_shortcut_block(content)
    updated |= _ensure_scale_card_block(content)

    if updated:
        workspace.content = json.dumps(content)

    return updated


def _ensure_shortcut_block(content):
    existing = next(
        (
            block
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "shortcut"
            and block.get("data", {}).get("shortcut_name") == SHORTCUT_LABEL
        ),
        None,
    )

    if existing:
        updated = False
        data = existing.setdefault("data", {})
        if data.get("col") != 3:
            data["col"] = 3
            updated = True

        pos_shortcut_index = None
        for idx, block in enumerate(content):
            if (
                isinstance(block, dict)
                and block.get("type") == "shortcut"
                and block.get("data", {}).get("shortcut_name") == "POS Awesome App"
            ):
                pos_shortcut_index = idx
                break

        if pos_shortcut_index is not None:
            desired_index = pos_shortcut_index + 1
            current_index = content.index(existing)
            if current_index != desired_index:
                shortcut_block = content.pop(current_index)
                if current_index < desired_index:
                    desired_index -= 1
                content.insert(desired_index, shortcut_block)
                updated = True

        return updated

    shortcut_block = {
        "id": SHORTCUT_ID,
        "type": "shortcut",
        "data": {
            "shortcut_name": SHORTCUT_LABEL,
            "col": 3,
        },
    }

    insert_at = 0
    for idx, block in enumerate(content):
        if (
            isinstance(block, dict)
            and block.get("type") == "shortcut"
            and block.get("data", {}).get("shortcut_name") == "POS Awesome App"
        ):
            insert_at = idx + 1
            break

    content.insert(insert_at, shortcut_block)
    return True


def _ensure_scale_card_block(content):
    existing = next(
        (
            block
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "card"
            and block.get("data", {}).get("card_name") == SCALE_CARD_LABEL
        ),
        None,
    )

    if existing:
        updated = False
        data = existing.setdefault("data", {})
        if data.get("col") != 4:
            data["col"] = 4
            updated = True

        shift_card_index = None
        for idx, block in enumerate(content):
            if (
                isinstance(block, dict)
                and block.get("type") == "card"
                and block.get("data", {}).get("card_name") == "Shift"
            ):
                shift_card_index = idx
                break

        if shift_card_index is not None:
            desired_index = shift_card_index + 1
            current_index = content.index(existing)
            if current_index != desired_index:
                card_block = content.pop(current_index)
                if current_index < desired_index:
                    desired_index -= 1
                content.insert(desired_index, card_block)
                updated = True

        return updated

    card_block = {
        "id": SCALE_CARD_ID,
        "type": "card",
        "data": {
            "card_name": SCALE_CARD_LABEL,
            "col": 4,
        },
    }

    insert_at = len(content)
    for idx, block in enumerate(content):
        if (
            isinstance(block, dict)
            and block.get("type") == "card"
            and block.get("data", {}).get("card_name") == "Shift"
        ):
            insert_at = idx + 1
            break

    content.insert(insert_at, card_block)
    return True
