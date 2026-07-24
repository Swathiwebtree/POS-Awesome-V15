from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from posawesome.posawesome.api import discounts as discounts_module
from posawesome.posawesome.api.discounts import get_customer_item_discount, validate_discount


class TestCustomerItemDiscount(FrappeTestCase):
    def setUp(self):
        discounts_module._ITEM_GROUP_PARENT_CACHE.clear()

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    def test_service_default_discount_auto_applies_and_locks_when_max_is_zero(
        self, mock_item_context, mock_config
    ):
        mock_item_context.return_value = {
            "item_group": "Services",
            "is_stock_item": 0,
            "custom_service_item": 1,
        }
        mock_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=12,
            custom_custom_max_discount___service_items=0,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-001")

        self.assertEqual(result["item_type"], "service")
        self.assertTrue(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertFalse(result["discount_editable"])
        self.assertEqual(result["auto_apply_value"], 12.0)
        self.assertEqual(result["max_discount"], 0.0)
        self.assertIn("locked", result["message"])

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    def test_stock_default_discount_auto_applies_and_remains_editable(self, mock_item_context, mock_config):
        mock_item_context.return_value = {
            "item_group": "Products",
            "is_stock_item": 1,
            "custom_service_item": 0,
        }
        mock_config.return_value = SimpleNamespace(
            custom_custom_default_discount___stock_items=15,
            custom_custom_max_discount___stock_items=8,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-002")

        self.assertEqual(result["item_type"], "stock")
        self.assertTrue(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertTrue(result["discount_editable"])
        self.assertEqual(result["auto_apply_value"], 15.0)
        self.assertEqual(result["max_discount"], 8.0)
        self.assertTrue(result["configuration_warning"])
        self.assertIn("Configuration warning", result["message"])

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    def test_stock_manual_discount_starts_at_zero_and_is_editable(self, mock_item_context, mock_config):
        mock_item_context.return_value = {
            "item_group": "Products",
            "is_stock_item": 1,
            "custom_service_item": 0,
        }
        mock_config.return_value = SimpleNamespace(
            custom_custom_default_discount___stock_items=0,
            custom_custom_max_discount___stock_items=9,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-003")

        self.assertEqual(result["item_type"], "stock")
        self.assertFalse(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertTrue(result["discount_editable"])
        self.assertEqual(result["auto_apply_value"], 0.0)
        self.assertEqual(result["max_discount"], 9.0)

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.frappe.db.get_value")
    def test_service_group_hierarchy_classifies_as_service(
        self, mock_get_value, mock_item_context, mock_config
    ):
        mock_item_context.return_value = {
            "item_group": "Engine Flushing",
            "item_name": "Engine Flushing",
            "is_stock_item": 1,
            "custom_service_item": 0,
        }
        mock_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=15,
            custom_custom_max_discount___service_items=0,
            custom_custom_default_discount___stock_items=15,
            custom_custom_max_discount___stock_items=8,
        )
        mock_get_value.side_effect = lambda doctype, name, fieldname: {
            ("Item Group", "Engine Flushing", "parent_item_group"): "Extra Car Services",
            ("Item Group", "Extra Car Services", "parent_item_group"): "Services",
            ("Item Group", "Services", "parent_item_group"): None,
        }.get((doctype, name, fieldname))

        result = get_customer_item_discount("CUST-001", "ITEM-004")

        self.assertEqual(result["item_type"], "service")
        self.assertEqual(result["default_discount"], 15.0)
        self.assertEqual(result["max_discount"], 0.0)
        self.assertTrue(result["auto_apply"])
        self.assertFalse(result["discount_editable"])

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    def test_zero_discount_configuration_disables_field(self, mock_item_context, mock_config):
        mock_item_context.return_value = {
            "item_group": "Services",
            "is_stock_item": 0,
            "custom_service_item": 1,
        }
        mock_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=0,
            custom_custom_max_discount___service_items=0,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-003")

        self.assertEqual(result["item_type"], "service")
        self.assertFalse(result["discount_enabled"])
        self.assertFalse(result["discount_editable"])
        self.assertEqual(result["default_discount"], 0.0)
        self.assertEqual(result["max_discount"], 0.0)
        self.assertEqual(result["message"], "Discount disabled")

    @patch("posawesome.posawesome.api.discounts.get_item_context")
    def test_engine_oil_is_blocked(self, mock_item_context):
        mock_item_context.return_value = {
            "item_group": "Engine Oil",
            "is_stock_item": 1,
            "custom_service_item": 0,
        }

        result = get_customer_item_discount("CUST-001", "OIL-001")

        self.assertEqual(result["item_type"], "engine_oil")
        self.assertFalse(result["discount_enabled"])
        self.assertIn("Engine Oil", result["message"])

    @patch("posawesome.posawesome.api.discounts.get_customer_item_discount")
    def test_validate_discount_allows_values_at_or_below_maximum(self, mock_get_discount):
        mock_get_discount.return_value = {
            "item_type": "service",
            "max_discount": 15,
            "auto_apply": True,
            "auto_apply_value": 10,
            "discount_enabled": True,
            "discount_editable": True,
            "message": "Auto-applied 10%",
        }

        result = validate_discount("CUST-001", "ITEM-004", 10)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["max_allowed"], 15)

    @patch("posawesome.posawesome.api.discounts.get_customer_item_discount")
    def test_validate_discount_rejects_values_above_maximum(self, mock_get_discount):
        mock_get_discount.return_value = {
            "item_type": "stock",
            "max_discount": 15,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": True,
            "discount_editable": True,
            "message": "Manual discount allowed up to 15%",
        }

        result = validate_discount("CUST-001", "ITEM-005", 20)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["max_allowed"], 15)
        self.assertIn("exceeds maximum", result["message"])

    @patch("posawesome.posawesome.api.discounts.get_customer_item_discount")
    def test_validate_discount_allows_locked_auto_apply_value(self, mock_get_discount):
        mock_get_discount.return_value = {
            "item_type": "service",
            "default_discount": 15,
            "max_discount": 0,
            "auto_apply": True,
            "auto_apply_value": 15,
            "discount_enabled": True,
            "discount_editable": False,
            "message": "Auto-applied 15% and locked",
        }

        result = validate_discount("CUST-001", "ITEM-006", 15)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["max_allowed"], 0)
