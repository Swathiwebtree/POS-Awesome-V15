from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from posawesome.posawesome.api.discounts import get_customer_item_discount


class TestCustomerItemDiscount(FrappeTestCase):
    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=True)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=False)
    def test_default_discount_takes_precedence_over_manual_cap(
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
        self.assertEqual(result["max_discount"], 12.0)
        self.assertEqual(result["auto_apply_value"], 12.0)

    @patch("posawesome.posawesome.api.discounts.get_customer_discount_config")
    @patch("posawesome.posawesome.api.discounts.get_item_context")
    @patch("posawesome.posawesome.api.discounts.is_engine_oil", return_value=False)
    @patch("posawesome.posawesome.api.discounts.is_service_item", return_value=True)
    @patch("posawesome.posawesome.api.discounts.is_stock_item", return_value=False)
    def test_manual_cap_is_retained_when_no_default_discount(
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
        self.assertEqual(result["max_discount"], 18.0)
