from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from posawesome.posawesome.api.discounts import get_customer_item_discount, validate_discount


class TestCustomerItemDiscount(FrappeTestCase):
    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=True)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=False)
    def test_service_default_and_max_use_default_to_auto_apply_and_max_as_ceiling(
        self,
        _mock_stock_item,
        _mock_service_item,
        _mock_engine_oil,
        mock_item_context,
        mock_discount_config,
    ):
        mock_item_context.return_value = {"item_group": "Services", "is_stock_item": 0}
        mock_discount_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=12,
            custom_custom_max_discount___service_items=25,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-001")

        self.assertTrue(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertEqual(result["max_discount"], 25.0)
        self.assertEqual(result["auto_apply_value"], 12.0)

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=True)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=False)
    def test_service_default_only_auto_applies_and_sets_its_own_ceiling(
        self,
        _mock_stock_item,
        _mock_service_item,
        _mock_engine_oil,
        mock_item_context,
        mock_discount_config,
    ):
        mock_item_context.return_value = {"item_group": "Services", "is_stock_item": 0}
        mock_discount_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=0,
            custom_custom_max_discount___service_items=18,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-001")

        self.assertFalse(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertEqual(result["max_discount"], 18.0)
        self.assertEqual(result["auto_apply_value"], 0)

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=True)
    def test_stock_max_only_allows_manual_discount_without_auto_apply(
        self,
        _mock_stock_item,
        _mock_service_item,
        _mock_engine_oil,
        mock_item_context,
        mock_discount_config,
    ):
        mock_item_context.return_value = {"item_group": "Products", "is_stock_item": 1}
        mock_discount_config.return_value = SimpleNamespace(
            custom_custom_default_discount___stock_items=0,
            custom_custom_max_discount___stock_items=8,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-002")

        self.assertFalse(result["auto_apply"])
        self.assertTrue(result["discount_enabled"])
        self.assertEqual(result["max_discount"], 8.0)
        self.assertEqual(result["auto_apply_value"], 0)

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=True)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=False)
    def test_discount_is_disabled_when_all_item_fields_are_empty(
        self,
        _mock_stock_item,
        _mock_service_item,
        _mock_engine_oil,
        mock_item_context,
        mock_discount_config,
    ):
        mock_item_context.return_value = {"item_group": "Services", "is_stock_item": 0}
        mock_discount_config.return_value = SimpleNamespace(
            custom_custom_default_discount___service_items=0,
            custom_custom_max_discount___service_items=0,
        )

        result = get_customer_item_discount("CUST-001", "ITEM-003")

        self.assertFalse(result["auto_apply"])
        self.assertFalse(result["discount_enabled"])
        self.assertEqual(result["max_discount"], 0)
        self.assertEqual(result["auto_apply_value"], 0)

    @patch("posawesome.posawesome.api.discounts.get_customer_item_discount")
    def test_validation_rejects_discounts_above_final_maximum(self, mock_get_discount):
        mock_get_discount.return_value = {
            "item_type": "service",
            "max_discount": 15,
            "auto_apply": True,
            "auto_apply_value": 10,
            "discount_enabled": True,
        }

        result = validate_discount("CUST-001", "ITEM-004", 20)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["max_allowed"], 15)
