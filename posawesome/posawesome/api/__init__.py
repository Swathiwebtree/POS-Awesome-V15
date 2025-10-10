"""Expose API functions for POS Awesome."""

from .bundles import get_bundle_components
from .customers import (
    create_customer,
    get_customer_addresses,
    get_customer_info,
    get_customer_names,
    get_customers_count,
    get_sales_person_names,
    make_address,
    set_customer_info,
)
from .invoices import (
    delete_invoice,
    get_draft_invoices,
    search_invoices_for_return,
    submit_invoice,
    update_invoice,
    validate_return_items,
)
from .items import (
    get_item_attributes,
    get_item_brand,
    get_item_detail,
    get_items,
    get_items_count,
    get_items_details,
    get_items_from_barcode,
    get_items_groups,
)
from .offers import (
    get_active_gift_coupons,
    get_applicable_delivery_charges,
    get_offers,
    get_pos_coupon,
)
from .payments import (
    create_payment_request,
    get_available_credit,
)
from .sales_orders import (
    search_orders,
    submit_sales_order,
    update_sales_order,
)
from .shifts import (
    check_opening_shift,
    create_opening_voucher,
    get_opening_dialog_data,
)
from .utilities import (
    get_app_branch,
    get_app_info,
    get_language_options,
    get_pos_profile_tax_inclusive,
    get_selling_price_lists,
    get_translation_dict,
    get_version,
)
from .utils import get_active_pos_profile, get_default_warehouse

# Include your Vehicle Service APIs
# Include your Vehicle Service, Work Order, Inventory, and Reports APIs
from .lazer_pos import (
    get_open_work_orders,
    get_work_order_details,
    add_item_to_order,
    apply_discount,
    apply_coupon,
    settle_order,
    void_order,
    hold_order,
    print_invoice,
    get_vehicle_service_list,
    get_vehicle_master,
    get_service_issue_list,
    get_quotation_list,
    get_loyalty_points,
    get_petty_cash_transactions,
    get_sales_by_payment_list,
    get_vehicle_history,
    get_redeemed_coupon_points_list,
    get_coupon_sales_point_list,
    get_vehicle_details,
    get_material_request_list,
    get_grn_list,
    get_issue_note_list,
    get_transfer_in_list,
    get_transfer_out_list,
    get_physical_count_list,
    get_production_form_list,
    get_damage_memo_list,
    get_bills_listing_work_order,
    get_bills_listing_vehicle,
    get_payment_summary_list,
    get_stock_in_hand_list,
    get_stock_sales_list,
    get_sales_points_list,
    get_sales_transaction_list,
    get_loyalty_customer,
    validate_loyalty_coupon,
    add_service,
    update_service_status,
    get_service_records,
    get_users,
    get_cash_counting,
    get_cashier_out,
    get_daily_summary,
)
