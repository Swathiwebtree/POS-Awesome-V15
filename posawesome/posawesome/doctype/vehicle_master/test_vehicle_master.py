# Copyright (c) 2025, Youssef Restom and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestVehicleMaster(FrappeTestCase):
    def _make_customer(self, customer_name: str) -> str:
        # ERPNext Customer typically needs customer_group + territory.
        customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_group": "All Customer Groups",
                "territory": "All Territories",
            }
        ).insert(ignore_permissions=True)
        return customer.name

    def test_vehicle_no_cannot_repeat_for_different_customers(self):
        customer_1 = self._make_customer("Vehicle Test Customer 1")
        customer_2 = self._make_customer("Vehicle Test Customer 2")

        frappe.get_doc(
            {
                "doctype": "Vehicle Master",
                "vehicle_no": "abc 123",
                "customer": customer_1,
                "model": "Test Model",
            }
        ).insert(ignore_permissions=True)

        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc(
                {
                    "doctype": "Vehicle Master",
                    "vehicle_no": "ABC123",
                    "customer": customer_2,
                    "model": "Test Model",
                }
            ).insert(ignore_permissions=True)
