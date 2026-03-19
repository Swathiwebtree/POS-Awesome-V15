# Copyright (c) 2025, Youssef Restom and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class VehicleMaster(Document):
    def validate(self):
        self._normalize_vehicle_no()
        self._validate_vehicle_no_unique()

    def _normalize_vehicle_no(self):
        vehicle_no = (getattr(self, "vehicle_no", None) or "").strip().upper()
        # Treat whitespace differences as the same vehicle number.
        vehicle_no = re.sub(r"\s+", "", vehicle_no)
        if vehicle_no:
            self.vehicle_no = vehicle_no

    def _validate_vehicle_no_unique(self):
        vehicle_no = (getattr(self, "vehicle_no", None) or "").strip()
        if not vehicle_no:
            return

        filters: dict[str, object] = {"vehicle_no": vehicle_no}
        if getattr(self, "name", None):
            filters["name"] = ["!=", self.name]

        # If this site has make/model fields on Vehicle Master, enforce uniqueness within make+model too.
        # Otherwise, fall back to vehicle_no alone (which is what most users expect anyway).
        meta = getattr(self, "meta", None)
        if meta and meta.has_field("make") and getattr(self, "make", None):
            filters["make"] = self.make
        if meta and meta.has_field("model") and getattr(self, "model", None):
            filters["model"] = self.model

        existing = frappe.get_all(
            "Vehicle Master",
            filters=filters,
            fields=["name", "customer", "vehicle_no"],
            limit_page_length=1,
        )
        if not existing:
            return

        row = existing[0]
        existing_customer = row.get("customer")
        this_customer = getattr(self, "customer", None)

        # Primary requirement: prevent two different customers using the same vehicle number.
        if existing_customer != this_customer:
            frappe.throw(
                _(
                    "Vehicle No {0} already exists on Vehicle Master {1}{2}. It cannot be used for another customer."
                ).format(
                    frappe.bold(vehicle_no),
                    frappe.bold(row.get("name")),
                    f" (Customer: {frappe.bold(existing_customer)})" if existing_customer else "",
                )
            )
