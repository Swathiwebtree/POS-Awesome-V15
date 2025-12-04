<template>
	<!-- Main Invoice Wrapper -->
	<div class="invoice-container">
		<!-- Cancel Sale Confirmation Dialog -->
		<CancelSaleDialog v-model="cancel_dialog" @confirm="cancel_invoice" />

		<!-- Scrollable Content Area -->
		<div class="invoice-content">
			<!-- Main Invoice Card (contains all invoice content) -->
			<v-card
				ref="invoiceCard"
				:style="{
					backgroundColor: isDarkTheme ? '#121212' : '',
				}"
				:class="[
					'cards my-0 py-0 resizable',
					isDarkTheme ? '' : 'bg-grey-lighten-5',
					{ 'return-mode': isReturnInvoice },
				]"
			>
				<!-- Dynamic padding wrapper -->
				<div class="dynamic-padding">
					<v-alert
						type="info"
						density="compact"
						class="mb-2"
						v-if="pos_profile.create_pos_invoice_instead_of_sales_invoice"
					>
						{{ __("Invoices saved as POS Invoices") }}
					</v-alert>

					<!-- Top Row: Customer Selection and Invoice Type -->
					<v-row align="center" class="items px-3 py-2">
						<v-col :cols="pos_profile.posa_allow_sales_order ? 9 : 12" class="pb-0 pr-0">
							<!-- Customer selection component -->
							<Customer />
						</v-col>
						<!-- Invoice Type Selection (Only shown if sales orders are allowed) -->
						<v-col v-if="pos_profile.posa_allow_sales_order" cols="3" class="pb-4">
							<v-select
								density="compact"
								hide-details
								variant="solo"
								color="primary"
								:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
								class="dark-field sleek-field"
								:items="invoiceTypes"
								:label="frappe._('Type')"
								v-model="invoiceType"
								:disabled="invoiceType == 'Return'"
							></v-select>
						</v-col>
					</v-row>

					<!-- Delivery Charges Section (Only if enabled in POS profile) -->
					<DeliveryCharges
						:pos_profile="pos_profile"
						:delivery_charges="delivery_charges"
						:selected_delivery_charge="selected_delivery_charge"
						:delivery_charges_rate="delivery_charges_rate"
						:deliveryChargesFilter="deliveryChargesFilter"
						:formatCurrency="formatCurrency"
						:currencySymbol="currencySymbol"
						:readonly="readonly"
						@update:selected_delivery_charge="
							(val) => {
								selected_delivery_charge = val;
								update_delivery_charges();
							}
						"
					/>

					<!-- Posting Date and Customer Balance Section -->
					<PostingDateRow
						:pos_profile="pos_profile"
						:posting_date_display="posting_date_display"
						:customer_balance="customer_balance"
						:price-list="selected_price_list"
						:price-lists="price_lists"
						:formatCurrency="formatCurrency"
						@update:posting_date_display="
							(val) => {
								posting_date_display = val;
							}
						"
						@update:priceList="
							(val) => {
								selected_price_list = val;
							}
						"
					/>

					<!-- Multi-Currency Section (Only if enabled in POS profile) -->
					<MultiCurrencyRow
						:pos_profile="pos_profile"
						:selected_currency="selected_currency"
						:plc_conversion_rate="exchange_rate"
						:conversion_rate="conversion_rate"
						:available_currencies="available_currencies"
						:isNumber="isNumber"
						:price_list_currency="price_list_currency"
						@update:selected_currency="
							(val) => {
								selected_currency = val;
								update_currency(val);
							}
						"
						@update:plc_conversion_rate="
							(val) => {
								exchange_rate = val;
								update_exchange_rate();
							}
						"
						@update:conversion_rate="
							(val) => {
								conversion_rate = val;
								update_conversion_rate();
							}
						"
					/>

					<!-- Items Table Section (Main items list for invoice) -->
					<div class="items-table-wrapper">
						<!-- Column selector button moved outside the table -->
						<div class="column-selector-container">
							<v-btn
								density="compact"
								variant="text"
								color="#4169E1"
								prepend-icon="mdi-cog-outline"
								@click="toggleColumnSelection"
								class="column-selector-btn"
							>
								{{ __("Columns") }}
							</v-btn>

							<v-dialog v-model="show_column_selector" max-width="500px">
								<v-card>
									<v-card-title class="text-h6 pa-4 d-flex align-center">
										<span>{{ __("Select Columns to Display") }}</span>
										<v-spacer></v-spacer>
										<v-btn
											icon="mdi-close"
											variant="text"
											density="compact"
											@click="show_column_selector = false"
										></v-btn>
									</v-card-title>
									<v-divider></v-divider>
									<v-card-text class="pa-4">
										<v-row dense>
											<v-col
												cols="12"
												v-for="column in available_columns.filter(
													(col) => !col.required,
												)"
												:key="column.key"
											>
												<v-switch
													v-model="temp_selected_columns"
													:label="column.title"
													:value="column.key"
													hide-details
													density="compact"
													color="primary"
													class="column-switch mb-1"
													:disabled="column.required"
												></v-switch>
											</v-col>
										</v-row>
										<div class="text-caption mt-2">
											{{ __("Required columns cannot be hidden") }}
										</div>
									</v-card-text>
									<v-card-actions class="pa-4 pt-0">
										<v-btn color="error" variant="text" @click="cancelColumnSelection">{{
											__("Cancel")
										}}</v-btn>
										<v-spacer></v-spacer>
										<v-btn
											color="primary"
											variant="tonal"
											@click="updateSelectedColumns"
											>{{ __("Apply") }}</v-btn
										>
									</v-card-actions>
								</v-card>
							</v-dialog>
						</div>

						<!-- ItemsTable component with reorder event handler -->
						<ItemsTable
							ref="itemsTable"
							:headers="items_headers"
							:items="items"
							v-model:expanded="expanded"
							:itemsPerPage="itemsPerPage"
							:itemSearch="itemSearch"
							:pos_profile="pos_profile"
							:invoice_doc="invoice_doc"
							:invoiceType="invoiceType"
							:stock_settings="stock_settings"
							:displayCurrency="displayCurrency"
							:formatFloat="formatFloat"
							:formatCurrency="formatCurrency"
							:currencySymbol="currencySymbol"
							:isNumber="isNumber"
							:setFormatedQty="setFormatedQty"
							:setFormatedCurrency="setFormatedCurrency"
							:calcPrices="calc_prices"
							:calcUom="calc_uom"
							:setSerialNo="set_serial_no"
							:setBatchQty="set_batch_qty"
							:validateDueDate="validate_due_date"
							:removeItem="remove_item"
							:subtractOne="subtract_one"
							:addOne="add_one"
							:toggleOffer="toggleOffer"
							:changePriceListRate="change_price_list_rate"
							:isNegative="isNegative"
							:shouldHidePricing="shouldHidePricing"
							@update:expanded="handleExpandedUpdate"
							@reorder-items="handleItemReorder"
							@add-item-from-drag="handleItemDrop"
							@show-drop-feedback="showDropFeedback"
							@item-dropped="showDropFeedback(false)"
							@view-packed="openPackedItems"
						/>

						<v-dialog v-model="show_packed_dialog" max-width="800px">
							<v-card>
								<v-card-title class="d-flex align-center">
									<span>{{ __("Packing List") }} ({{ packed_dialog_items.length }})</span>
									<v-spacer></v-spacer>
									<v-btn
										icon="mdi-close"
										variant="text"
										density="compact"
										@click="show_packed_dialog = false"
									></v-btn>
								</v-card-title>
								<v-divider></v-divider>
								<v-card-text>
									<v-alert type="warning" density="compact" class="mb-2">
										{{
											__(
												"For 'Product Bundle' items, Warehouse, Serial No and Batch No will be considered from the 'Packing List' table. If Warehouse and Batch No are same for all packing items for any 'Product Bundle' item, those values can be entered in the main Item table; values will be copied to 'Packing List' table.",
											)
										}}
									</v-alert>
									<v-data-table
										:headers="packedItemsHeaders"
										:items="packed_dialog_items"
										class="elevation-1"
										hide-default-footer
										density="compact"
									>
										<template v-slot:item.index="{ index }">
											{{ index + 1 }}
										</template>
										<template v-slot:item.qty="{ item }">
											{{ formatFloat(item.qty) }}
										</template>
										<template v-slot:item.rate="{ item }">
											<div class="currency-display">
												<span class="currency-symbol">{{
													currencySymbol(displayCurrency)
												}}</span>
												<span class="amount-value">{{
													formatCurrency(item.rate)
												}}</span>
											</div>
										</template>
										<template v-slot:item.warehouse="{ item }">
											<v-text-field
												v-model="item.warehouse"
												hide-details
												density="compact"
											/>
										</template>
										<template v-slot:item.batch_no="{ item }">
											<v-text-field
												v-model="item.batch_no"
												hide-details
												density="compact"
											/>
										</template>
										<template v-slot:item.serial_no="{ item }">
											<v-text-field
												v-model="item.serial_no"
												hide-details
												density="compact"
											/>
										</template>
									</v-data-table>
								</v-card-text>
							</v-card>
						</v-dialog>
					</div>
				</div>
			</v-card>
		</div>

		<!-- Fixed Footer Controls -->
		<div class="invoice-controls">
			<InvoiceSummary
				:pos_profile="pos_profile"
				:total_qty="total_qty"
				:additional_discount="additional_discount"
				:additional_discount_percentage="additional_discount_percentage"
				:total_items_discount_amount="total_items_discount_amount"
				:subtotal="subtotal"
				:displayCurrency="displayCurrency"
				:formatFloat="formatFloat"
				:formatCurrency="formatCurrency"
				:currencySymbol="currencySymbol"
				:discount_percentage_offer_name="discount_percentage_offer_name"
				:isNumber="isNumber"
				:selectedCustomerId="customer"
				@apply-frequent-card="handleApplyFrequentCard"
				:items_group="items_group"
				v-model:item_group="item_group"
				@update:item_group="handleItemGroupUpdate"
				:active_price_list="selected_price_list"
				:offersCount="offersCount"
				:couponsCount="couponsCount"
				v-model:items_view="items_view"
				@update:additional_discount="(val) => (additional_discount = val)"
				@update:additional_discount_percentage="(val) => (additional_discount_percentage = val)"
				@update_discount_umount="apply_additional_discount"
				@save-and-clear="save_and_clear_invoice"
				@load-drafts="get_draft_invoices"
				@select-order="get_draft_orders"
				@cancel-sale="cancel_dialog = true"
				@open-returns="open_returns"
				@print-draft="print_draft_invoice"
				@show-payment="show_payment"
				@show-offers="handleShowOffers"
				@show-coupons="handleShowCoupons"
			/>
		</div>
	</div>
</template>

<script>
/* global frappe, __ */
import format from "../../format";
import Customer from "./Customer.vue";
import DeliveryCharges from "./DeliveryCharges.vue";
import PostingDateRow from "./PostingDateRow.vue";
import MultiCurrencyRow from "./MultiCurrencyRow.vue";
import CancelSaleDialog from "./CancelSaleDialog.vue";
import InvoiceSummary from "./InvoiceSummary.vue";
import ItemsTable from "./ItemsTable.vue";
import invoiceItemMethods from "./invoiceItemMethods";
import invoiceComputed from "./invoiceComputed";
import invoiceWatchers from "./invoiceWatchers";
import offerMethods from "./invoiceOfferMethods";
import shortcutMethods from "./invoiceShortcuts";

export default {
	name: "POSInvoice",
	mixins: [format],
	data() {
		return {
			loaded_draft_name: null,
			// POS profile settings
			pos_profile: "",
			pos_opening_shift: "",
			stock_settings: "",
			invoice_doc: "",
			return_doc: "",
			customer: "",
			customer_info: "",
			customer_balance: 0,
			discount_amount: 0,
			additional_discount: 0,
			additional_discount_percentage: 0,
			service_employee: null,
			service_employee_name: null,
			service_employee_designation: null,
			service_employee_department: null,
			custom_odometer_reading: null,
			contact_mobile: "",
			custom_vehicle_no: "",
			total_tax: 0,
			items: [], // List of invoice items
			packed_items: [], // Packed items for bundles
			packed_dialog_items: [], // Packed items displayed in dialog
			show_packed_dialog: false, // Packing list dialog visibility
			posOffers: [], // All available offers
			posa_offers: [], // Offers applied to this invoice
			posa_coupons: [], // Coupons applied
			isApplyingOffer: false, // Flag to prevent offer watcher loops
			allItems: [], // All items for offer logic
			discount_percentage_offer_name: null, // Track which offer is applied
			invoiceTypes: ["Invoice", "Order"], // Types of invoices
			invoiceType: "Invoice", // Current invoice type
			itemsPerPage: 1000, // Items per page in table
			expanded: [], // Array of expanded row IDs
			singleExpand: true, // Only one row expanded at a time
			cancel_dialog: false, // Cancel dialog visibility
			float_precision: 6, // Float precision for calculations
			currency_precision: 6, // Currency precision for display
			new_line: false, // Add new line for item
			available_stock_cache: {},
			brand_cache: {},
			delivery_charges: [], // List of delivery charges
			delivery_charges_rate: 0, // Selected delivery charge rate
			selected_delivery_charge: "", // Selected delivery charge object
			invoice_posting_date: false, // Posting date dialog
			posting_date: frappe.datetime.nowdate(), // Invoice posting date
			posting_date_display: "", // Display value for date picker
			items_headers: [],
			items_group: ["ALL"],
			item_group: "ALL",
			items_view: "list",
			offersCount: 0,
			couponsCount: 0,
			packedItemsHeaders: [
				{ title: __("No."), key: "index" },
				{ title: __("Parent Item"), key: "parent_item" },
				{ title: __("Item Code"), key: "item_code" },
				{ title: __("Description"), key: "item_name" },
				{ title: __("Qty"), key: "qty" },
				{ title: __("Rate"), key: "rate" },
				{ title: __("Warehouse"), key: "warehouse" },
				{ title: __("Batch"), key: "batch_no" },
				{ title: __("Serial"), key: "serial_no" },
			],
			selected_currency: "", // Currently selected currency
			exchange_rate: 1, // Current exchange rate
			conversion_rate: 1, // Currency to company rate
			exchange_rate_date: frappe.datetime.nowdate(), // Date of fetched exchange rate
			company: null, // Company doc with default currency
			available_currencies: [], // List of available currencies
			price_lists: [], // Available selling price lists
			selected_price_list: "", // Currently selected price list
			price_list_currency: "", // Currency of the selected price list
			selected_columns: [], // Selected columns for items table
			temp_selected_columns: [], // Temporary array for column selection
			available_columns: [], // All available columns
			show_column_selector: false, // Column selector dialog visibility
		};
	},

	components: {
		Customer,
		DeliveryCharges,
		PostingDateRow,
		MultiCurrencyRow,
		InvoiceSummary,
		CancelSaleDialog,
		ItemsTable,
	},
	computed: {
		...invoiceComputed,
		// Check if pricing should be hidden
		shouldHidePricing() {
			if (!this.items || this.items.length === 0) return false;

			return this.items.some(item => {
				return item.item_group === "Engine Oil";
			});
		},

	},

	methods: {
		...shortcutMethods,
		...offerMethods,
		...invoiceItemMethods,

		handleItemGroupUpdate(newGroup) {
			console.log("[Invoice] Item group updated:", newGroup);
			this.item_group = newGroup;
		},

		initializeItemsHeaders() {
			// Define all available columns
			this.available_columns = [
				{ title: __("Name"), align: "start", sortable: true, key: "item_name", required: true },
				{ title: __("QTY"), key: "qty", align: "start", required: true },
				{ title: __("UOM"), key: "uom", align: "start", required: false },
				{ title: __("Price"), key: "price_list_rate", align: "start", required: false },
				{ title: __("Discount %"), key: "discount_value", align: "start", required: false },
				{ title: __("Discount Amount"), key: "discount_amount", align: "start", required: false },
				{ title: __("Rate"), key: "rate", align: "start", required: false },
				{ title: __("Amount"), key: "amount", align: "start", required: true },
				{ title: __("Actions"), key: "actions", align: "start", required: true },
				{ title: __("Offer?"), key: "posa_is_offer", align: "center", required: false },
			];

			// Initialize selected columns if empty
			if (!this.selected_columns || this.selected_columns.length === 0) {
				// By default, select all required columns and those enabled in POS profile
				this.selected_columns = this.available_columns
					.filter((col) => {
						if (col.required) return true;
						if (col.key === "price_list_rate") return true;
						if (col.key === "discount_value" && this.pos_profile.posa_display_discount_percentage)
							return true;
						if (col.key === "discount_amount" && this.pos_profile.posa_display_discount_amount)
							return true;
						return false;
					})
					.map((col) => col.key);
			}

			// Generate headers based on selected columns
			this.updateHeadersFromSelection();
		},

		// Add this NEW method to handle frequent card application
		handleApplyFrequentCard(cardData) {
			console.log("[Invoice] Applying frequent card:", cardData);

			try {
				// Create free item object with all required fields
				const freeItem = {
					item_code: cardData.item_code,
					item_name: cardData.item_name || cardData.service_item_name,
					qty: 1,
					rate: 0, // FREE!
					price_list_rate: 0,
					discount_percentage: 100,
					discount_amount: 0,
					amount: 0,
					frequent_card: cardData.frequent_card || cardData.name,
					is_free_item: 1,
					warehouse: this.pos_profile?.warehouse || "",
					uom: "Nos",
					stock_uom: "Nos",
					conversion_factor: 1,
					posa_row_id: this.makeid(50), // Generate unique ID
				};

				// CORRECT: Add to local items array
				this.items.push(freeItem);

				// Recalculate totals
				this.$nextTick(() => {
					this.apply_additional_discount();
					this.$forceUpdate();
				});

				// Show success message
				frappe.show_alert({
					message: this.__(` Free ${cardData.service_item_name} added to invoice!`),
					indicator: "green",
				});
			} catch (error) {
				console.error("[Invoice] Error applying frequent card:", error);
				frappe.show_alert({
					message: this.__("Failed to add free service"),
					indicator: "red",
				});
			}
		},

		checkForEngineOilItem() {
			console.log("[Invoice] Checking for Engine Oil items");

			if (!this.items || this.items.length === 0) {
				return false;
			}

			const hasOilItem = this.items.some((item) => {
				return (item.item_group || "").trim() === "Engine Oil";
			});


			console.log("[Invoice] Has Engine Oil item:", hasOilItem);
			return hasOilItem;
		},

		checkForCarWashServices() {
			if (!this.items || this.items.length === 0) {
				return false;
			}

			// Check if any item is a car wash service
			const hasCarWashService = this.items.some((item) => {
				// Check item group
				const itemGroupMatch =
					item.item_group &&
					(item.item_group.toLowerCase().includes("car wash") ||
						item.item_group.toLowerCase().includes("Carwash") ||
						item.item_group.toLowerCase().includes("wash"));

				// Check item code
				const itemCodeMatch =
					item.item_code &&
					(item.item_code.toLowerCase().includes("wash") ||
						item.item_code.toLowerCase().includes("service"));

				// Check if item has service_item flag
				const serviceItemFlag = item.service_item === 1 || item.is_service_item === 1;

				// Check item name
				const itemNameMatch = item.item_name && item.item_name.toLowerCase().includes("wash");

				return itemGroupMatch || itemCodeMatch || serviceItemFlag || itemNameMatch;
			});

			console.log("[Invoice] checkForCarWashServices result:", hasCarWashService);
			return hasCarWashService;
		},

		updateServiceEmployeeInDoc() {
			// Ensure invoice_doc exists - create if it doesn't
			if (!this.invoice_doc) {
				console.log("[Invoice] Creating invoice_doc for employee update");
				this.invoice_doc = {
					doctype: "Sales Invoice",
					customer: this.customer || "",
					posting_date: this.posting_date || frappe.datetime.nowdate(),
					items: this.items || [],
					pos_profile: this.pos_profile?.name || "",
					company: this.pos_profile?.company || "",
				};
			}

			if (!this.service_employee) {
				console.warn("[Invoice] No service employee to update");
				return;
			}

			console.log("[Invoice] Updating invoice_doc with employee:", this.service_employee);

			// Add custom fields for service employee
			this.invoice_doc.custom_service_employee = this.service_employee;
			this.invoice_doc.custom_service_employee_name = this.service_employee_name;

			// Optional: store additional employee details
			if (this.service_employee_designation) {
				this.invoice_doc.custom_service_employee_designation = this.service_employee_designation;
			}
			if (this.service_employee_department) {
				this.invoice_doc.custom_service_employee_department = this.service_employee_department;
			}

			console.log("[Invoice] Invoice doc updated with employee:", {
				employee_id: this.invoice_doc.custom_service_employee,
				employee_name: this.invoice_doc.custom_service_employee_name,
			});

			// Force update
			this.$forceUpdate();
		},

		clearServiceEmployee() {
			console.log("[Invoice] Clearing service employee");
			this.service_employee = null;
			this.service_employee_name = null;
			this.service_employee_designation = null;
			this.service_employee_department = null;

			if (this.invoice_doc) {
				this.invoice_doc.custom_service_employee = null;
				this.invoice_doc.custom_service_employee_name = null;
				this.invoice_doc.custom_service_employee_designation = null;
				this.invoice_doc.custom_service_employee_department = null;
			}
		},

		apply_additional_discount() {
			console.log("[Invoice] apply_additional_discount called");

			// Get subtotal from computed property (already calculated)
			const totalBeforeDiscount = this.subtotal;
			let discountAmount = 0;

			// Calculate discount based on percentage or fixed amount
			if (this.flt(this.additional_discount_percentage) > 0) {
				discountAmount = this.flt(
					(totalBeforeDiscount * this.flt(this.additional_discount_percentage)) / 100,
				);
			} else if (this.flt(this.additional_discount) > 0) {
				discountAmount = this.flt(this.additional_discount);
			}

			// Update discount_amount (this triggers grand_total recalculation)
			this.discount_amount = Math.round(discountAmount);

			console.log("[Invoice] Discount calculated:", {
				subtotal: totalBeforeDiscount,
				discount_percentage: this.additional_discount_percentage,
				discount_amount: this.additional_discount,
				calculated_discount: discountAmount,
				grand_total: this.grand_total,
				rounded_total: this.rounded_total,
			});

			// Sync to invoice_doc
			if (this.invoice_doc) {
				this.invoice_doc.discount_amount = this.discount_amount;
				this.invoice_doc.additional_discount = this.additional_discount;
				this.invoice_doc.additional_discount_percentage = this.additional_discount_percentage;
				this.invoice_doc.net_total = this.subtotal;
				this.invoice_doc.grand_total = this.grand_total;
				this.invoice_doc.rounded_total = this.rounded_total;
			}

			// Force UI update to reflect changes
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		},

		// Recalculate subtotal and total qty
		update_totals() {
			this.subtotal = this.items.reduce((sum, i) => sum + i.qty * i.rate, 0);
			this.total_qty = this.items.reduce((sum, i) => sum + i.qty, 0);
		},

		// Handle item dropped from ItemsSelector to ItemsTable
		handleItemDrop(item) {
			console.log("Item dropped:", item);

			// Use the existing add_item method to add the dropped item
			this.add_item(item);

			// Show success feedback
			this.eventBus.emit("show_message", {
				title: __(`Item {0} added to invoice`, [item.item_name]),
				color: "success",
			});
		},

		handleShowOffers() {
			console.log("[Invoice] handleShowOffers called");
			this.eventBus.emit("show_offers", "true");
		},

		handleShowCoupons() {
			console.log("[Invoice] handleShowCoupons called");
			this.eventBus.emit("show_coupons", "true");
		},

		get_draft_invoices() {
			this.eventBus.emit("open_drafts_modal");
		},

		get_draft_orders() {
			this.eventBus.emit("select_order");
		},

		open_returns() {
			this.eventBus.emit("open_returns");
		},

		show_payment() {
			console.log("[Invoice] show_payment called");
			const invoice = this.prepareForPayment();
			if (invoice && invoice.items && invoice.items.length > 0) {
				this.eventBus.emit("payment_ready", invoice);
				this.eventBus.emit("show_payment", "true");
			} else {
				frappe.show_alert({
					message: this.__("Please add items before proceeding to payment"),
					indicator: "warning",
				});
			}
		},

		// Show visual feedback when item is being dragged over drop zone
		showDropFeedback(isDragging) {
			// Add visual feedback class to the items table
			const itemsTable = this.$el.querySelector(".modern-items-table");
			if (itemsTable) {
				if (isDragging) {
					itemsTable.classList.add("drag-over");
				} else {
					itemsTable.classList.remove("drag-over");
				}
			}
		},

		openPackedItems(bundle_id) {
			this.packed_dialog_items = this.packed_items.filter((it) => it.bundle_id === bundle_id);
			this.show_packed_dialog = true;
		},

		toggleColumnSelection() {
			// Create a copy of selected columns for temporary editing
			this.temp_selected_columns = [...this.selected_columns];
			this.show_column_selector = true;
		},

		cancelColumnSelection() {
			// Discard changes
			this.show_column_selector = false;
		},

		updateHeadersFromSelection() {
			// Generate headers based on selected columns (without closing dialog)
			this.items_headers = this.available_columns.filter(
				(col) => this.selected_columns.includes(col.key) || col.required,
			);
		},

		updateSelectedColumns() {
			// Apply the temporary selection
			this.selected_columns = [...this.temp_selected_columns];

			// Add required columns if they're not already included
			const requiredKeys = this.available_columns.filter((col) => col.required).map((col) => col.key);

			requiredKeys.forEach((key) => {
				if (!this.selected_columns.includes(key)) {
					this.selected_columns.push(key);
				}
			});

			// Update headers
			this.updateHeadersFromSelection();

			// Save preferences
			this.saveColumnPreferences();

			// Close dialog
			this.show_column_selector = false;
		},

		saveColumnPreferences() {
			try {
				localStorage.setItem("posawesome_selected_columns", JSON.stringify(this.selected_columns));
			} catch (e) {
				console.error("Failed to save column preferences:", e);
			}
		},

		loadColumnPreferences() {
			try {
				const saved = localStorage.getItem("posawesome_selected_columns");
				if (saved) {
					this.selected_columns = JSON.parse(saved);
				}
			} catch (e) {
				console.error("Failed to load column preferences:", e);
			}
		},

		makeid(length) {
			let result = "";
			const characters = "abcdefghijklmnopqrstuvwxyz0123456789";
			const charactersLength = characters.length;
			for (var i = 0; i < length; i++) {
				result += characters.charAt(Math.floor(Math.random() * charactersLength));
			}
			return result;
		},

		handleExpandedUpdate(ids) {
			this.expanded = Array.isArray(ids) ? ids.slice(-1) : [];
		},

		print_draft_invoice() {
			if (!this.pos_profile.posa_allow_print_draft_invoices) {
				this.eventBus.emit("show_message", {
					title: __(`You are not allowed to print draft invoices`),
					color: "error",
				});
				return;
			}
			let invoice_name = this.invoice_doc.name;
			frappe.run_serially([
				() => {
					const invoice_doc = this.save_and_clear_invoice();
					invoice_name = invoice_doc.name ? invoice_doc.name : invoice_name;
				},
				() => {
					this.load_print_page(invoice_name);
				},
			]);
		},

		async set_delivery_charges() {
			var vm = this;
			if (!this.pos_profile || !this.customer || !this.pos_profile.posa_use_delivery_charges) {
				this.delivery_charges = [];
				this.delivery_charges_rate = 0;
				this.selected_delivery_charge = "";
				return;
			}
			this.delivery_charges_rate = 0;
			this.selected_delivery_charge = "";
			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.offers.get_applicable_delivery_charges",
					args: {
						company: this.pos_profile.company,
						pos_profile: this.pos_profile.name,
						customer: this.customer,
					},
				});
				if (r.message && r.message.length) {
					console.log(r.message);
					vm.delivery_charges = r.message;
				}
			} catch (error) {
				console.error("Failed to fetch delivery charges", error);
			}
		},

		deliveryChargesFilter(itemText, queryText, itemRow) {
			const item = itemRow.raw;
			console.log("dl charges", item);
			const textOne = item.name.toLowerCase();
			const searchText = queryText.toLowerCase();
			return textOne.indexOf(searchText) > -1;
		},

		update_delivery_charges() {
			if (this.selected_delivery_charge) {
				this.delivery_charges_rate = this.selected_delivery_charge.rate;
			} else {
				this.delivery_charges_rate = 0;
			}
		},

		updatePostingDate(date) {
			if (!date) return;
			this.posting_date = date;
			this.$forceUpdate();
		},

		// Override setFormatedFloat for qty field to handle stock limits and return mode
		setFormatedQty(item, field_name, precision, no_negative, value) {
			// Parse and set the value using the mixin's formatter
			let parsedValue = this.setFormatedFloat(item, field_name, precision, no_negative, value);

			// Enforce available stock limits
			if (item.max_qty !== undefined && this.flt(item[field_name]) > this.flt(item.max_qty)) {
				const blockSale =
					!this.stock_settings.allow_negative_stock ||
					this.pos_profile.posa_block_sale_beyond_available_qty;
				if (blockSale) {
					item[field_name] = item.max_qty;
					parsedValue = item.max_qty;
					this.eventBus.emit("show_message", {
						title: __(`Maximum available quantity is {0}. Quantity adjusted to match stock.`, [
							this.formatFloat(item.max_qty),
						]),
						color: "error",
					});
				} else {
					this.eventBus.emit("show_message", {
						title: __("Stock is lower than requested. Proceeding may create negative stock."),
						color: "warning",
					});
				}
			}

			// Ensure negative value for return invoices
			if (this.isReturnInvoice && parsedValue > 0) {
				parsedValue = -Math.abs(parsedValue);
				item[field_name] = parsedValue;
			}

			// Recalculate stock quantity with the adjusted value
			this.calc_stock_qty(item, item[field_name]);
			if (field_name === "qty" && item.is_bundle) {
				this.packed_items
					.filter((it) => it.bundle_id === item.bundle_id)
					.forEach((ch) => {
						ch.qty = item.qty * (ch.child_qty_per_bundle || 1);
						this.calc_stock_qty(ch, ch.qty);
					});
			}
			return parsedValue;
		},

		async fetch_available_currencies() {
			try {
				console.log("Fetching available currencies...");
				const r = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_available_currencies",
				});

				if (r.message) {
					console.log("Received currencies:", r.message);

					// Get base currency for reference
					const baseCurrency = this.pos_profile.currency;

					// Create simple currency list with just names
					this.available_currencies = r.message.map((currency) => {
						return {
							value: currency.name,
							title: currency.name,
						};
					});

					// Sort currencies - base currency first, then others alphabetically
					this.available_currencies.sort((a, b) => {
						if (a.value === baseCurrency) return -1;
						if (b.value === baseCurrency) return 1;
						return a.value.localeCompare(b.value);
					});

					// Set default currency if not already set
					if (!this.selected_currency) {
						this.selected_currency = baseCurrency;
					}

					return this.available_currencies;
				}

				return [];
			} catch (error) {
				console.error("Error fetching currencies:", error);
				// Set default currency as fallback
				const defaultCurrency = this.pos_profile.currency;
				this.available_currencies = [
					{
						value: defaultCurrency,
						title: defaultCurrency,
					},
				];
				this.selected_currency = defaultCurrency;
				return this.available_currencies;
			}
		},

		async fetch_price_lists() {
			if (this.pos_profile.posa_enable_price_list_dropdown) {
				try {
					const r = await frappe.call({
						method: "posawesome.posawesome.api.utilities.get_selling_price_lists",
					});
					if (r && r.message) {
						this.price_lists = r.message.map((pl) => pl.name);
					}
				} catch (error) {
					console.error("Failed fetching price lists", error);
					this.price_lists = [this.pos_profile.selling_price_list];
				}
			} else {
				// Fallback to the price list defined in the POS Profile
				this.price_lists = [this.pos_profile.selling_price_list];
			}

			if (!this.selected_price_list) {
				this.selected_price_list = this.pos_profile.selling_price_list;
			}

			// Fetch and store currency for the applied price list
			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.invoices.get_price_list_currency",
					args: { price_list: this.selected_price_list },
				});
				if (r && r.message) {
					this.price_list_currency = r.message;
				}
			} catch (error) {
				console.error("Failed fetching price list currency", error);
			}

			return this.price_lists;
		},

		async update_currency(currency) {
			if (!currency) return;
			this.selected_currency = currency;
			await this.update_currency_and_rate();
		},

		update_exchange_rate() {
			if (!this.exchange_rate || this.exchange_rate <= 0) {
				this.exchange_rate = 1;
			}

			// Emit currency update
			this.eventBus.emit("update_currency", {
				currency: this.selected_currency || this.pos_profile.currency,
				exchange_rate: this.exchange_rate,
			});

			this.update_item_rates();
		},

		update_conversion_rate() {
			if (!this.conversion_rate || this.conversion_rate <= 0) {
				this.conversion_rate = 1;
			}

			this.sync_exchange_rate();
		},

		update_item_rates() {
			console.log("Updating item rates with exchange rate:", this.exchange_rate);

			this.items.forEach((item) => {
				try {
					// ===== DEFENSIVE: ensure item object exists =====
					if (!item) return;

					// Set skip flag to avoid double calculations
					item._skip_calc = true;

					// ===== DEFENSIVE: ensure qty is numeric and service items keep qty=1 =====
					const parsedQty = Number(item.qty);
					const looksLikeService = item.is_service_item === 1 || item.service_item === 1
						|| /Carwash|car wash|bike wash|bikewash/i.test(item.item_group || item.item_name || '');
					if (looksLikeService) {
						item.qty = (Number.isFinite(parsedQty) && parsedQty > 0) ? parsedQty : 1;
						item.is_service_item = 1;
						item.update_stock = 0;
					} else {
						item.qty = Number.isFinite(parsedQty) ? parsedQty : 0;
					}

					// First ensure base rates exist for all items
					if (!item.base_rate) {
						console.log(`Setting base rates for ${item.item_code} for the first time`);
						const baseCurrency = this.price_list_currency || this.pos_profile.currency;
						if (this.selected_currency === baseCurrency) {
							// When in base currency, base rates = displayed rates
							item.base_rate = Number(item.rate) || 0;
							item.base_price_list_rate = Number(item.price_list_rate) || 0;
							item.base_discount_amount = Number(item.discount_amount || 0);
						} else {
							// When in another currency, calculate base rates (avoid divide by zero)
							const ex = this.exchange_rate || 1;
							item.base_rate = (Number(item.rate) || 0) / ex;
							item.base_price_list_rate = (Number(item.price_list_rate) || 0) / ex;
							item.base_discount_amount = (Number(item.discount_amount || 0)) / ex;
						}
					}

					// Currency conversion logic
					const baseCurrency = this.price_list_currency || this.pos_profile.currency;
					if (this.selected_currency === baseCurrency) {
						// When switching back to default currency, restore from base rates
						console.log(`Restoring rates for ${item.item_code} from base rates`);
						item.price_list_rate = Number(item.base_price_list_rate) || 0;
						item.rate = Number(item.base_rate) || 0;
						item.discount_amount = Number(item.base_discount_amount || 0);
					} else if (item.original_currency === this.selected_currency) {
						// When selected currency matches the price list currency,
						// no conversion should be applied
						console.log(`Using original currency rates for ${item.item_code}`);
						item.price_list_rate = Number(item.base_price_list_rate) || 0;
						item.rate = Number(item.base_rate) || 0;
						item.discount_amount = Number(item.base_discount_amount || 0);
					} else {
						// When switching to another currency, convert from base rates
						console.log(`Converting rates for ${item.item_code} to ${this.selected_currency}`);

						const ex = this.exchange_rate || 1;

						// Convert base currency values to the selected currency
						const converted_price = this.flt((Number(item.base_price_list_rate) || 0) * ex, this.currency_precision);
						const converted_rate = this.flt((Number(item.base_rate) || 0) * ex, this.currency_precision);
						const converted_discount = this.flt((Number(item.base_discount_amount) || 0) * ex, this.currency_precision);

						// Preserve previous non-zero values if conversion results in tiny noise
						const prev_price = Number(item.price_list_rate) || 0;
						const prev_rate = Number(item.rate) || 0;
						const prev_discount = Number(item.discount_amount) || 0;

						const tinyThreshold = 0.000001;

						item.price_list_rate = (Math.abs(converted_price) < tinyThreshold) ? prev_price : converted_price;
						item.rate = (Math.abs(converted_rate) < tinyThreshold) ? prev_rate : converted_rate;
						item.discount_amount = (Math.abs(converted_discount) < tinyThreshold) ? prev_discount : converted_discount;
					}

					// Always recalculate final amounts (use numeric values)
					const qtyNum = Number(item.qty) || 0;
					const rateNum = Number(item.rate) || 0;
					const baseRateNum = Number(item.base_rate) || 0;

					item.amount = this.flt(qtyNum * rateNum, this.currency_precision);
					item.base_amount = this.flt(qtyNum * baseRateNum, this.currency_precision);

					console.log(`Updated rates for ${item.item_code}:`, {
						price_list_rate: item.price_list_rate,
						base_price_list_rate: item.base_price_list_rate,
						rate: item.rate,
						base_rate: item.base_rate,
						discount: item.discount_amount,
						base_discount: item.base_discount_amount,
						amount: item.amount,
						base_amount: item.base_amount,
						qty: item.qty
					});

					// Apply any other pricing rules if needed
					this.calc_item_price && this.calc_item_price(item);
				} catch (e) {
					console.warn("[update_item_rates] error processing item", item && item.item_name, e);
				} finally {
					// Clear skip flag
					if (item) item._skip_calc = false;
				}
			});

			// Force UI update after all calculations
			this.$forceUpdate && this.$forceUpdate();

			this.apply_additional_discount && this.apply_additional_discount();
		},

		formatCurrency(value, precision = null) {
			// Force integer formatting for pricing
			const val = parseFloat(value) || 0;
			return Math.round(val).toString();
		},
		flt(value, precision = null) {
			// Enhanced float handling for small numbers
			if (precision === null) {
				precision = this.float_precision;
			}

			const _value = Number(value);
			if (isNaN(_value)) {
				return 0;
			}

			// Handle very small numbers to prevent them from becoming 0
			if (Math.abs(_value) < 0.000001) {
				return _value;
			}

			return Number((_value || 0).toFixed(precision));
		},

		// Update currency and exchange rate when currency is changed
		async update_currency_and_rate() {
			if (!this.selected_currency) return;

			const companyCurrency =
				(this.company && this.company.default_currency) || this.pos_profile.currency;
			const priceListCurrency = this.price_list_currency || companyCurrency;

			try {
				// Price list currency to selected currency rate
				if (this.selected_currency === priceListCurrency) {
					this.exchange_rate = 1;
				} else {
					const r = await frappe.call({
						method: "posawesome.posawesome.api.invoices.fetch_exchange_rate_pair",
						args: {
							from_currency: priceListCurrency,
							to_currency: this.selected_currency,
						},
					});
					if (r && r.message) {
						this.exchange_rate = r.message.exchange_rate;
					}
				}

				// Selected currency to company currency rate
				if (this.selected_currency === companyCurrency) {
					this.conversion_rate = 1;
					this.exchange_rate_date = this.formatDateForBackend(this.posting_date_display);
				} else {
					const r2 = await frappe.call({
						method: "posawesome.posawesome.api.invoices.fetch_exchange_rate_pair",
						args: {
							from_currency: this.selected_currency,
							to_currency: companyCurrency,
						},
					});
					if (r2 && r2.message) {
						this.conversion_rate = r2.message.exchange_rate;
						this.exchange_rate_date = r2.message.date;
						const posting_backend = this.formatDateForBackend(this.posting_date_display);
						if (this.exchange_rate_date && posting_backend !== this.exchange_rate_date) {
							this.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										this.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
				}
			} catch (error) {
				console.error("Error updating currency:", error);
				this.eventBus.emit("show_message", {
					title: "Error updating currency",
					color: "error",
				});
			}

			this.sync_exchange_rate();

			// If items already exist, update the invoice on the server so that
			// the document currency and rates remain consistent
			if (this.items.length) {
				const doc = this.get_invoice_doc();
				doc.currency = this.selected_currency;
				doc.price_list_currency = priceListCurrency || this.pos_profile.currency;
				doc.conversion_rate = this.conversion_rate;
				doc.plc_conversion_rate = this.exchange_rate;
				try {
					await this.update_invoice(doc);
				} catch (error) {
					console.error("Error updating invoice currency:", error);
					this.eventBus.emit("show_message", {
						title: "Error updating currency",
						color: "error",
					});
				}
			}
		},

		get_invoice_doc() {
			console.log("[Invoice] get_invoice_doc() called");

			if (!this.invoice_doc) {
				this.invoice_doc = {
					doctype: "Sales Invoice",
					items: [],
					payments: [],
				};
			}

			// Defensive: Ensure this.items is an array
			this.items = Array.isArray(this.items) ? this.items : [];

			// DEFENSE 0: Protect service items in-place BEFORE any processing
			// This prevents other code (rate updates, expands) from accidentally zeroing qty
			try {
				this.items.forEach(it => {
					if (!it) return;
					const looksLikeService = (it.is_service_item || it.service_item) || /carwash|car wash|bike wash|bikewash/i.test(it.item_group || it.item_name || '');
					if (looksLikeService) {
						const q = Number(it.qty);
						if (!Number.isFinite(q) || q <= 0) {
							console.log("[DEFENSE] fixing service item qty (in-place) for", it.item_name, "from", it.qty, "to 1");
							it.qty = 1;
						}
						// enforce service flags
						it.is_service_item = 1;
						it.update_stock = 0;
					} else {
						// ensure numeric qty for non-service items (do not force it to 0 if it's valid)
						const q = Number(it.qty);
						it.qty = Number.isFinite(q) ? q : 0;
					}
				});
			} catch (e) {
				console.warn("[Invoice] error in initial service-item defense:", e);
			}

			// If invoice contains ONLY service items, disable stock updates/validation
			try {
				// Use current items list (this.items) or fallback to invoice_doc.items
				const itemsForCheck = this.items.length ? this.items : (this.invoice_doc && this.invoice_doc.items) || [];

				const allService = itemsForCheck.length > 0 && itemsForCheck.every(function (it) {
					const ig = (it.item_group || "").toString().toLowerCase();
					const name = (it.item_name || "").toString().toLowerCase();
					const code = (it.item_code || "").toString().toLowerCase();
					return (
						ig.includes("carwash") ||
						ig.includes("car wash") ||
						ig.includes("bike wash") ||
						ig.includes("bikewash") ||
						name.includes("wash") ||
						code.includes("wash") ||
						it.service_item === 1 ||
						it.is_service_item === 1
					);
				});

				if (allService) {
					// Prevent server from doing stock validation / stock ledger updates on document
					this.invoice_doc.update_stock = 0;

					// Ensure we operate on the array that will be sent to server
					this.invoice_doc.items = (itemsForCheck || []).map((it) => {
						const itemRow = { ...it };
						try {
							// Mark line as non-stock and prevent stock ledger updates
							itemRow.update_stock = 0;
							itemRow.is_stock_item = 0;
							// Remove warehouse reference to avoid server trying to consume stock
							if (itemRow.warehouse) itemRow.warehouse = null;
							// ensure doctype is still correct
							itemRow.doctype = itemRow.doctype || "Sales Invoice Item";

							// Defensive: ensure qty for service rows is valid
							const q = Number(itemRow.qty);
							if (!Number.isFinite(q) || q <= 0) {
								itemRow.qty = 1;
							} else {
								itemRow.qty = q;
							}

							// Defensive: normalize rate to number
							itemRow.rate = Number.isFinite(Number(itemRow.rate ?? itemRow.price ?? 0)) ? Number(itemRow.rate ?? itemRow.price ?? 0) : 0;

							// ensure flags numeric
							itemRow.is_service_item = itemRow.is_service_item ? 1 : 0;
							itemRow.update_stock = 0;
						} catch (e) {
							console.warn("[Invoice] mark service item non-stock error:", e);
						}
						return itemRow;
					});
					console.log("[Invoice] All lines are detected as service items - disabled update_stock for doc and lines");
				}
			} catch (e) {
				console.warn("[Invoice] Error while disabling stock update for service-only invoice:", e);
			}

			// CRITICAL: Sync ALL values (defensive normalization of items)
			console.log("[Invoice] get_invoice_doc - syncing items (pre-normalize):", (this.items || []).map(i => ({ code: i.item_code, qty: i.qty, is_service_item: i.is_service_item })));

			// Normalize items into invoice_doc.items (do not completely replace source item objects)
			try {
				this.invoice_doc.items = (this.items || []).map(it => {
					const row = { ...it };

					// Parse numeric fields defensively
					const qty = Number(row.qty);
					const rate = Number(row.rate ?? row.price ?? 0);

					// If item marked as service (or looks like carwash), default invalid qty -> 1
					const looksLikeService = row.is_service_item || row.service_item || /carwash|car wash|bike wash|bikewash/i.test(row.item_group || row.item_name || '');
					if (looksLikeService) {
						row.qty = (Number.isFinite(qty) && qty > 0) ? qty : 1;
					} else {
						row.qty = (Number.isFinite(qty) && qty > 0) ? qty : 0;
					}

					row.rate = Number.isFinite(rate) ? rate : 0;

					// flags
					row.is_service_item = row.is_service_item ? 1 : 0;
					row.update_stock = typeof row.update_stock !== 'undefined' ? row.update_stock : (row.is_service_item ? 0 : 1);

					return row;
				});
			} catch (e) {
				console.warn("[Invoice] error normalizing items into invoice_doc.items:", e);
				// fallback: copy items as-is
				this.invoice_doc.items = this.items || [];
			}

			console.log("[Invoice] get_invoice_doc - items after normalize:", (this.invoice_doc.items || []).map(i => ({ code: i.item_code, qty: i.qty, rate: i.rate, is_service_item: i.is_service_item })));

			// SYNC other fields
			this.invoice_doc.customer = this.customer || "";
			this.invoice_doc.posting_date = this.posting_date || frappe.datetime.nowdate();
			this.invoice_doc.currency = this.selected_currency || this.pos_profile?.currency || "USD";

			// SYNC TOTALS (defensive)
			this.invoice_doc.net_total = (this.invoice_doc.items || []).reduce((sum, line) => {
				const q = Number(line.qty);
				const r = Number(line.rate);
				const safeQ = (Number.isFinite(q) && q > 0) ? q : 0;
				const safeR = Number.isFinite(r) ? r : 0;
				return sum + safeQ * safeR;
			}, 0);

			this.invoice_doc.total_qty = (this.invoice_doc.items || []).reduce((sum, line) => {
				const q = Number(line.qty);
				return sum + ((Number.isFinite(q) && q > 0) ? q : 0);
			}, 0);

			// Keep rest of totals/fields
			this.invoice_doc.total_taxes_and_charges = this.flt(this.total_tax || 0);
			this.invoice_doc.discount_amount = this.flt(this.discount_amount || 0);
			this.invoice_doc.additional_discount = this.flt(this.additional_discount || 0);
			this.invoice_doc.additional_discount_percentage = this.flt(this.additional_discount_percentage || 0);
			this.invoice_doc.grand_total = this.flt(this.grand_total || 0);
			this.invoice_doc.rounded_total = this.flt(this.rounded_total || this.grand_total || 0);

			this.invoice_doc.conversion_rate = this.conversion_rate || 1;
			this.invoice_doc.plc_conversion_rate = this.exchange_rate || 1;
			this.invoice_doc.pos_profile = this.pos_profile?.name || "";
			this.invoice_doc.company = this.pos_profile?.company || "";

			if (this.service_employee) {
				this.invoice_doc.custom_service_employee = this.service_employee;
				this.invoice_doc.custom_service_employee_name = this.service_employee_name;
				if (this.service_employee_designation) {
					this.invoice_doc.custom_service_employee_designation = this.service_employee_designation;
				}
				if (this.service_employee_department) {
					this.invoice_doc.custom_service_employee_department = this.service_employee_department;
				}
			}

			//ODOMETER FIELDS
			const hasOilItem = this.checkForEngineOilItem();
			this.invoice_doc.custom_has_oil_item = hasOilItem ? 1 : 0;

			if (hasOilItem && this.custom_odometer_reading) {
				this.invoice_doc.custom_odometer_reading = this.custom_odometer_reading;
			} else {
				this.invoice_doc.custom_odometer_reading = null;
			}

			// Always sync mobile and vehicle (fetched from customer)
			this.invoice_doc.contact_mobile = this.contact_mobile || "";
			this.invoice_doc.custom_vehicle_no = this.custom_vehicle_no || "";

			console.log("[Invoice] Synced odometer fields:", {
				has_oil: hasOilItem,
				odometer: this.custom_odometer_reading,
				mobile: this.contact_mobile,
				vehicle: this.custom_vehicle_no,
			});

			console.log("[Invoice] get_invoice_doc returning:", {
				items: (this.invoice_doc.items || []).length,
				net_total: this.invoice_doc.net_total,
				discount: this.invoice_doc.discount_amount,
				grand_total: this.invoice_doc.grand_total,
				rounded_total: this.invoice_doc.rounded_total,
				employee: this.invoice_doc.custom_service_employee,
				odometer: this.invoice_doc.custom_odometer_reading,
				mobile: this.invoice_doc.contact_mobile,
				vehicle: this.invoice_doc.custom_vehicle_no,
			});

			return this.invoice_doc;
		},

		// Alternative method name for compatibility
		getInvoiceDoc() {
			return this.get_invoice_doc();
		},

		// Broadcast invoice updates to parent/sibling components
		broadcastInvoiceUpdate() {
			if (this.invoice_doc && this.eventBus) {
				console.log("[Invoice] Broadcasting invoice update");
				this.eventBus.emit("invoice_updated", this.invoice_doc);
			}
		},

		// Get full invoice with all calculated values
		getFullInvoiceData() {
			console.log("[Invoice] getFullInvoiceData() called");

			const invoiceData = {
				// Basic info
				name: this.invoice_doc?.name || "",
				doctype: "Sales Invoice",
				customer: this.customer || "",
				posting_date: this.posting_date || frappe.datetime.nowdate(),

				// Items
				items: this.items || [],

				// Amounts
				net_total: this.net_total || 0,
				total_taxes_and_charges: this.total_tax || 0,
				total: this.subtotal || 0,
				discount_amount: this.discount_amount || 0,
				grand_total: this.grand_total || 0,
				rounded_total: this.rounded_total || this.grand_total || 0,

				// Additional discounts
				additional_discount: this.additional_discount || 0,
				additional_discount_percentage: this.additional_discount_percentage || 0,

				// Currency
				currency: this.selected_currency || this.pos_profile.currency,
				conversion_rate: this.conversion_rate || 1,
				plc_conversion_rate: this.exchange_rate || 1,

				// Payments
				payments: this.invoice_doc?.payments || [],

				// POS specific
				pos_profile: this.pos_profile?.name || "",
				company: this.pos_profile?.company || "",
				is_return: this.invoice_doc?.is_return || 0,

				// Other fields
				...this.invoice_doc,
			};

			console.log("[Invoice] Full invoice data:", invoiceData);
			return invoiceData;
		},

		// Ensure invoice_doc is updated before payment
		prepareForPayment() {
			console.log("[Invoice] prepareForPayment() called");

			// Call get_invoice_doc to ensure sync
			const invoiceData = this.get_invoice_doc();

			console.log("[Invoice] prepareForPayment result:", {
				items_count: (invoiceData.items || []).length,
				subtotal: invoiceData.net_total,
				tax: invoiceData.total_taxes_and_charges,
				discount: invoiceData.discount_amount,
				grand_total: invoiceData.grand_total,
				rounded_total: invoiceData.rounded_total,
				currency: invoiceData.currency,
			});

			return invoiceData;
		},

		async update_exchange_rate_on_server() {
			if (this.conversion_rate) {
				if (!this.items.length) {
					this.sync_exchange_rate();
					return;
				}

				const doc = this.get_invoice_doc();
				doc.conversion_rate = this.conversion_rate;
				doc.plc_conversion_rate = this.exchange_rate;
				try {
					const resp = await this.update_invoice(doc);
					if (resp && resp.exchange_rate_date) {
						this.exchange_rate_date = resp.exchange_rate_date;
						const posting_backend = this.formatDateForBackend(this.posting_date_display);
						if (posting_backend !== this.exchange_rate_date) {
							this.eventBus.emit("show_message", {
								title: __(
									"Exchange rate date " +
										this.exchange_rate_date +
										" differs from posting date " +
										posting_backend,
								),
								color: "warning",
							});
						}
					}
					this.sync_exchange_rate();
				} catch (error) {
					console.error("Error updating exchange rate:", error);
					this.eventBus.emit("show_message", {
						title: "Error updating exchange rate",
						color: "error",
					});
				}
			}
		},

		sync_exchange_rate() {
			if (!this.exchange_rate || this.exchange_rate <= 0) {
				this.exchange_rate = 1;
			}
			if (!this.conversion_rate || this.conversion_rate <= 0) {
				this.conversion_rate = 1;
			}

			// Emit currency update
			this.eventBus.emit("update_currency", {
				currency: this.selected_currency || this.pos_profile.currency,
				exchange_rate: this.exchange_rate,
				conversion_rate: this.conversion_rate,
			});

			this.update_item_rates();
		},

		// Add new rounding function
		roundAmount(amount) {
			// Respect POS Profile setting to disable rounding
			if (this.pos_profile.disable_rounded_total) {
				// Use configured precision without applying rounding
				return this.flt(amount, this.currency_precision);
			}
			// If multi-currency is enabled and selected currency is different from base currency
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.pos_profile.posa_allow_multi_currency && this.selected_currency !== baseCurrency) {
				// For multi-currency, just keep 2 decimal places without rounding to nearest integer
				return this.flt(amount, 2);
			}
			// For base currency or when multi-currency is disabled, round to nearest integer
			return Math.round(amount);
		},

		// Increase quantity of an item (handles return logic)
		add_one(item) {
			if (this.isReturnInvoice) {
				// For returns, make quantity more negative
				item.qty--;
			} else {
				const proposed = item.qty + 1;
				const blockSale =
					!this.stock_settings.allow_negative_stock ||
					this.pos_profile.posa_block_sale_beyond_available_qty;
				if (blockSale && item.max_qty !== undefined && proposed > item.max_qty) {
					item.qty = item.max_qty;
					this.calc_stock_qty(item, item.qty);
					this.eventBus.emit("show_message", {
						title: __("Maximum available quantity is {0}. Quantity adjusted to match stock.", [
							this.formatFloat(item.max_qty),
						]),
						color: "error",
					});
					return;
				}
				item.qty = proposed;
			}

			if (item.qty == 0) {
				this.remove_item(item);
				return;
			}

			// Recalculate stock and amount
			this.calc_stock_qty(item, item.qty);
			item.amount = this.flt(item.qty * item.rate, this.currency_precision);

			// Update packed items if bundle
			if (item.is_bundle) {
				this.packed_items
					.filter((it) => it.bundle_id === item.bundle_id)
					.forEach((ch) => {
						ch.qty = item.qty * (ch.child_qty_per_bundle || 1);
						this.calc_stock_qty(ch, ch.qty);
					});
			}

			// Use Vue.set to ensure reactivity
			const index = this.items.findIndex((i) => i.posa_row_id === item.posa_row_id);
			if (index !== -1) {
				// Create new object to trigger reactivity
				this.$set(this.items, index, { ...item });
			}

			// Trigger recalculation
			this.$nextTick(() => {
				this.apply_additional_discount();
			});
		},
		// Decrease quantity of an item (handles return logic)
		subtract_one(item) {
			if (this.isReturnInvoice) {
				// For returns, move quantity toward zero
				item.qty++;
			} else {
				item.qty--;
			}

			if (item.qty == 0) {
				this.remove_item(item);
				return;
			}

			// Recalculate stock and amount
			this.calc_stock_qty(item, item.qty);
			item.amount = this.flt(item.qty * item.rate, this.currency_precision);

			// Update packed items if bundle
			if (item.is_bundle) {
				this.packed_items
					.filter((it) => it.bundle_id === item.bundle_id)
					.forEach((ch) => {
						ch.qty = item.qty * (ch.child_qty_per_bundle || 1);
						this.calc_stock_qty(ch, ch.qty);
					});
			}

			// Use Vue.set to ensure reactivity
			const index = this.items.findIndex((i) => i.posa_row_id === item.posa_row_id);
			if (index !== -1) {
				// Create new object to trigger reactivity
				this.$set(this.items, index, { ...item });
			}

			// Trigger recalculation
			this.$nextTick(() => {
				this.apply_additional_discount();
			});
		},

		// UPDATE: save_and_clear_invoice method - CORRECTED VERSION
		async save_and_clear_invoice() {
			console.log("[Invoice] save_and_clear_invoice() called");
			console.log("[Invoice] loaded_draft_name:", this.loaded_draft_name);

			// Basic validations
			if (!this.items || this.items.length === 0) {
				frappe.show_alert({
					message: this.__("Please add items to invoice before saving"),
					indicator: "warning",
				});
				return null;
			}

			// ===== FIX: CARWASH QTY VALIDATION =====
			console.log("[Invoice] Validating CarWash items...");
			this.items.forEach((item, idx) => {
				if (this.isCarWashItem(item)) {
					console.log(`[Invoice] CarWash item detected at idx ${idx}: ${item.item_name}`);

					// CRITICAL: Force qty to 1 for CarWash items
					if (item.qty === null || item.qty === undefined || item.qty === 0) {
						console.log(
							`[Invoice] AUTO-FIXING qty for ${item.item_name} from ${item.qty} to 1`
						);
						item.qty = 1;
						item.amount = item.rate * 1; // Recalculate amount
						item.is_service_item = 1;
						item.update_stock = 0;
					}

					// Ensure these flags are set
					item.is_service_item = 1;
					item.update_stock = 0;
				}
			});
			// ===== END FIX =====

			// Check if all items are Carwash items (service items only)
			const hasOnlyServiceItems = this.items.every(item => {
				return this.isCarWashItem(item);
			});

			// Validate employee for car wash services
			const hasCarWashService = this.checkForCarWashServices();
			if (hasCarWashService && !this.service_employee) {
				frappe.show_alert({
					message: this.__("Please select a service employee for car wash services"),
					indicator: "warning",
				});
				return null;
			}

			if (!hasOnlyServiceItems) {
				// Validate stock for non-service items
				const insufficientStockItems = this.items.filter(item => {
					// Only check stock for non-carwash items
					return !this.isCarWashItem(item) && (item.actual_qty < item.qty);
				});

				if (insufficientStockItems.length > 0) {
					const itemNames = insufficientStockItems.map(i => i.item_name).join(', ');
					frappe.show_alert({
						message: this.__("Insufficient stock for: {0}", [itemNames]),
						indicator: "error",
					});
					return null;
				}
			}

			// Ensure invoice_doc exists
			if (!this.invoice_doc) {
				this.invoice_doc = {};
			}

			// ===== CRITICAL: APPLY CARWASH FIXES TO ITEMS BEFORE SAVE =====
			let itemsToSave = this.items.map(it => {
				const row = { ...it };

				// For CarWash items, FORCE qty to 1
				if (this.isCarWashItem(row)) {
					console.log(`[Invoice] Applying CarWash fix to ${row.item_code}`);
					row.qty = 1;
					row.amount = row.rate * 1;
					row.is_service_item = 1;
					row.update_stock = 0;
				}

				return row;
			});

			// Update items to save with fixed CarWash quantities
			this.invoice_doc.items = itemsToSave;
			// ===== END CRITICAL FIX =====

			// Populate/sync fields from UI into invoice_doc
			this.invoice_doc.customer = this.customer;
			this.invoice_doc.posting_date = this.posting_date || frappe.datetime.nowdate();
			this.invoice_doc.currency =
				this.selected_currency || (this.pos_profile && this.pos_profile.currency) || "INR";
			this.invoice_doc.net_total = this.subtotal || 0;
			this.invoice_doc.total_taxes_and_charges = this.total_tax || 0;
			this.invoice_doc.discount_amount = this.discount_amount || 0;
			this.invoice_doc.additional_discount = this.additional_discount || 0;
			this.invoice_doc.additional_discount_percentage = this.additional_discount_percentage || 0;
			this.invoice_doc.grand_total = this.grand_total || this.subtotal || 0;
			this.invoice_doc.rounded_total = this.rounded_total || this.invoice_doc.grand_total;
			this.invoice_doc.conversion_rate = this.conversion_rate || 1;
			this.invoice_doc.plc_conversion_rate = this.exchange_rate || 1;
			this.invoice_doc.pos_profile = this.pos_profile && this.pos_profile.name;
			this.invoice_doc.company = this.pos_profile && this.pos_profile.company;

			// ===== NEW: ADD ODOMETER, MOBILE, VEHICLE FIELDS =====
			// Employee fields
			if (this.service_employee) {
				this.invoice_doc.custom_service_employee = this.service_employee;
				this.invoice_doc.custom_service_employee_name = this.service_employee_name;
				console.log("[Invoice] Employee added to invoice:", this.service_employee);
			}

			// Mobile number
			if (this.contact_mobile) {
				this.invoice_doc.contact_mobile = this.contact_mobile;
				console.log("[Invoice] Mobile added to invoice:", this.contact_mobile);
			}

			// Vehicle number
			if (this.custom_vehicle_no) {
				this.invoice_doc.custom_vehicle_no = this.custom_vehicle_no;
				console.log("[Invoice] Vehicle added to invoice:", this.custom_vehicle_no);
			}

			// Odometer reading and oil item flag
			if (this.custom_odometer_reading) {
				this.invoice_doc.custom_odometer_reading = this.custom_odometer_reading;
				console.log("[Invoice] Odometer added to invoice:", this.custom_odometer_reading);
			}

			// Set oil item flag based on items
			const hasOilItem = this.items.some(item =>
				item.item_code && (
					item.item_code.toLowerCase().includes('engine oil') ||
					item.item_code.toLowerCase().includes('oil change') ||
					item.item_name?.toLowerCase().includes('engine oil') ||
					item.item_name?.toLowerCase().includes('oil change')
				)
			);
			this.invoice_doc.custom_has_oil_item = hasOilItem ? 1 : 0;
			console.log("[Invoice] Has oil item:", hasOilItem);
			// ===== END NEW FIELDS =====

			// Required: ensure parent doctype is set for insert
			this.invoice_doc.doctype = "Sales Invoice";

			// Ensure items exist and each child row has proper doctype
			if (!Array.isArray(this.invoice_doc.items)) {
				this.invoice_doc.items = itemsToSave || [];
			}

			this.invoice_doc.items = this.invoice_doc.items.map((it) => {
				const itemRow = Object.assign({}, it);
				itemRow.doctype = "Sales Invoice Item";

				// FINAL CHECK: Force CarWash qty to 1
				if (this.isCarWashItem(itemRow)) {
					itemRow.qty = 1;
					itemRow.amount = itemRow.rate * 1;
					itemRow.is_service_item = 1;
					itemRow.update_stock = 0;
				}

				return itemRow;
			});

			console.log("[Invoice] Invoice ready to save:", {
				customer: this.invoice_doc.customer,
				items_count: this.invoice_doc.items.length,
				grand_total: this.invoice_doc.grand_total,
				currency: this.invoice_doc.currency,
				employee: this.invoice_doc.custom_service_employee,
				mobile: this.invoice_doc.contact_mobile,
				vehicle: this.invoice_doc.custom_vehicle_no,
				odometer: this.invoice_doc.custom_odometer_reading,
				has_oil: this.invoice_doc.custom_has_oil_item,
				items: this.invoice_doc.items.map(i => ({
					code: i.item_code,
					qty: i.qty,
					is_carwash: this.isCarWashItem(i),
				})),
			});

			try {
				// 1) Ensure customer exists
				const customer_name = this.invoice_doc.customer;
				if (customer_name) {
					const existsResp = await frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "Customer",
							fields: ["name"],
							filters: { name: customer_name },
							limit_page_length: 1,
						},
					});
					const exists = Array.isArray(existsResp.message) && existsResp.message.length > 0;
					if (!exists) {
						console.log("[Invoice] Customer does not exist, creating Customer:", customer_name);
						const newCustomerResp = await frappe.call({
							method: "frappe.client.insert",
							args: {
								doc: {
									doctype: "Customer",
									customer_name: customer_name,
									name: customer_name,
								},
							},
						});
						if (!newCustomerResp.message) {
							throw new Error("Failed to create Customer: " + (newCustomerResp.exc || ""));
						}
						console.log("[Invoice] Customer created:", newCustomerResp.message.name);
					}
				}

				// 2) Resolve and validate POS Opening Shift
				let openingShiftName = null;

				if (this.pos_opening_shift) {
					openingShiftName =
						typeof this.pos_opening_shift === "string"
							? this.pos_opening_shift
							: this.pos_opening_shift.name || null;
				}

				if (!openingShiftName && this.pos_profile) {
					openingShiftName =
						(this.pos_profile.posa_pos_opening_shift &&
							String(this.pos_profile.posa_pos_opening_shift)) ||
						(this.pos_profile.pos_opening_shift && String(this.pos_profile.pos_opening_shift)) ||
						null;
				}

				if (!openingShiftName && this.invoice_doc.posa_pos_opening_shift) {
					openingShiftName = String(this.invoice_doc.posa_pos_opening_shift);
				}

				console.log("[Invoice] Resolved openingShiftName:", openingShiftName);

				if (openingShiftName) {
					const shiftResp = await frappe.call({
						method: "frappe.client.get",
						args: { doctype: "POS Opening Shift", name: openingShiftName },
					});

					if (!shiftResp || !shiftResp.message) {
						frappe.show_alert({
							message: this.__("Referenced POS Opening Shift {0} not found", [
								openingShiftName,
							]),
							indicator: "red",
						});
						return null;
					}

					const shiftDoc = shiftResp.message;
					if (String(shiftDoc.status).toLowerCase() !== "open") {
						frappe.show_alert({
							message: this.__(
								"POS Shift {0} is not open. Please open/start the shift before saving invoice.",
								[openingShiftName],
							),
							indicator: "red",
						});
						return null;
					}

					this.invoice_doc.posa_pos_opening_shift = openingShiftName;
				} else {
					frappe.show_alert({
						message: this.__(
							"No POS Opening Shift selected. Please select/open a POS shift before saving invoice.",
						),
						indicator: "warning",
					});
					return null;
				}

				// -------- Resolve draft name to update
				const draft_name_to_update =
					this.loaded_draft_name || (this.invoice_doc && this.invoice_doc.name) || null;
				console.log("[Invoice] resolved draft_name_to_update:", draft_name_to_update);

				if (draft_name_to_update) {
					// UPDATE EXISTING DRAFT
					console.log("[Invoice] Updating existing draft:", draft_name_to_update);

					const field_map = {
						items: this.invoice_doc.items,
						customer: this.invoice_doc.customer,
						posting_date: this.invoice_doc.posting_date,
						currency: this.invoice_doc.currency,
						net_total: this.invoice_doc.net_total,
						total_taxes_and_charges: this.invoice_doc.total_taxes_and_charges,
						discount_amount: this.invoice_doc.discount_amount,
						additional_discount: this.invoice_doc.additional_discount,
						additional_discount_percentage: this.invoice_doc.additional_discount_percentage,
						grand_total: this.invoice_doc.grand_total,
						rounded_total: this.invoice_doc.rounded_total,
						conversion_rate: this.invoice_doc.conversion_rate,
						plc_conversion_rate: this.invoice_doc.plc_conversion_rate,
						pos_profile: this.invoice_doc.pos_profile,
						company: this.invoice_doc.company,
						posa_pos_opening_shift: this.invoice_doc.posa_pos_opening_shift,
						custom_service_employee: this.invoice_doc.custom_service_employee,
						custom_service_employee_name: this.invoice_doc.custom_service_employee_name,
						// ===== NEW: ADD TO UPDATE =====
						contact_mobile: this.invoice_doc.contact_mobile,
						custom_vehicle_no: this.invoice_doc.custom_vehicle_no,
						custom_odometer_reading: this.invoice_doc.custom_odometer_reading,
						custom_has_oil_item: this.invoice_doc.custom_has_oil_item,
						// ===== END NEW =====
					};

					const updResp = await frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "Sales Invoice",
							name: draft_name_to_update,
							fieldname: field_map,
						},
					});

					if (updResp.message) {
						console.log("[Invoice] Existing draft updated successfully:", draft_name_to_update);
						frappe.show_alert({
							message: this.__("Draft invoice updated: {0}", [draft_name_to_update]),
							indicator: "green",
						});
						this.loaded_draft_name = draft_name_to_update;
						this.invoice_doc.name = draft_name_to_update;
						this.eventBus.emit("invoice_saved_successfully", { name: draft_name_to_update });

						try {
							const savedDraft = {
								name: draft_name_to_update,
								customer: this.invoice_doc.customer,
								posting_date: this.invoice_doc.posting_date,
								posting_time: this.invoice_doc.posting_time || null,
								grand_total: this.invoice_doc.grand_total,
								currency: this.invoice_doc.currency,
								custom_service_employee: this.invoice_doc.custom_service_employee,
								// ===== NEW: ADD TO EVENT =====
								contact_mobile: this.invoice_doc.contact_mobile,
								custom_vehicle_no: this.invoice_doc.custom_vehicle_no,
								custom_odometer_reading: this.invoice_doc.custom_odometer_reading,
								custom_has_oil_item: this.invoice_doc.custom_has_oil_item,
								// ===== END NEW =====
							};
							this.eventBus.emit("draft_saved", savedDraft);
							console.log(
								"[Invoice] Emitted draft_saved for updated draft:",
								draft_name_to_update,
							);
						} catch (e) {
							console.warn("[Invoice] Failed to emit draft_saved for update", e);
						}

						this.service_employee = null;
						this.service_employee_name = null;
						this.service_employee_designation = null;
						this.service_employee_department = null;
						console.log("[Invoice] Employee selection cleared after save");

						this.eventBus.emit("clear_employee_selection");
						this.clear_invoice();

						return updResp.message;
					} else {
						throw new Error("Failed to update draft: " + (updResp.exc || ""));
					}
				} else {
					// CREATE NEW DRAFT
					console.log("[Invoice] Creating new draft (no existing draft loaded)");

					const insertResp = await frappe.call({
						method: "frappe.client.insert",
						args: {
							doc: this.invoice_doc,
						},
					});

					if (insertResp.message) {
						const saved_doc = insertResp.message;
						const saved_name = saved_doc.name;
						console.log("[Invoice] Invoice saved as new draft:", saved_name);

						this.loaded_draft_name = saved_name;
						this.invoice_doc.name = saved_name;

						frappe.show_alert({
							message: this.__("Draft invoice saved: {0}", [saved_name]),
							indicator: "green",
						});

						this.eventBus.emit("invoice_saved_successfully", { name: saved_name });

						try {
							const savedDraft = {
								name: saved_doc.name,
								customer: saved_doc.customer || this.invoice_doc.customer,
								posting_date: saved_doc.posting_date || this.invoice_doc.posting_date,
								posting_time: saved_doc.posting_time || this.invoice_doc.posting_time || null,
								grand_total:
									saved_doc.grand_total != null
										? saved_doc.grand_total
										: this.invoice_doc.grand_total,
								currency: saved_doc.currency || this.invoice_doc.currency,
								custom_service_employee:
									saved_doc.custom_service_employee ||
									this.invoice_doc.custom_service_employee,
								// ===== NEW: ADD TO EVENT =====
								contact_mobile: saved_doc.contact_mobile || this.invoice_doc.contact_mobile,
								custom_vehicle_no: saved_doc.custom_vehicle_no || this.invoice_doc.custom_vehicle_no,
								custom_odometer_reading: saved_doc.custom_odometer_reading || this.invoice_doc.custom_odometer_reading,
								custom_has_oil_item: saved_doc.custom_has_oil_item || this.invoice_doc.custom_has_oil_item,
								// ===== END NEW =====
							};
							this.eventBus.emit("draft_saved", savedDraft);
							console.log("[Invoice] Emitted draft_saved for new draft:", saved_doc.name);
						} catch (e) {
							console.warn("[Invoice] Failed to emit draft_saved for create", e);
						}

						this.service_employee = null;
						this.service_employee_name = null;
						this.service_employee_designation = null;
						this.service_employee_department = null;
						console.log("[Invoice] Employee selection cleared after save");

						this.eventBus.emit("clear_employee_selection");
						this.clear_invoice();

						return saved_doc;
					} else {
						throw new Error("Failed to create invoice: " + (insertResp.exc || ""));
					}
				}
			} catch (error) {
				console.error("[Invoice] Error saving invoice:", error);
				if (error && error._server_messages) {
					try {
						const msgs = JSON.parse(error._server_messages);
						if (Array.isArray(msgs) && msgs.length) {
							const parsed = JSON.parse(msgs[0]);
							frappe.show_alert({ message: parsed.message || parsed, indicator: "red" });
						} else {
							frappe.show_alert({
								message: this.__("Error saving invoice") + ": " + error.message,
								indicator: "red",
							});
						}
					} catch (e) {
						frappe.show_alert({
							message: this.__("Error saving invoice") + ": " + (error.message || error),
							indicator: "red",
						});
					}
				} else {
					frappe.show_alert({
						message: this.__("Error saving invoice: ") + (error.message || error),
						indicator: "red",
					});
				}
				return null;
			} finally {
				this.$nextTick(() => this.$forceUpdate && this.$forceUpdate());
			}
		},
		async save_invoice() {
			console.log("[Invoice] save_invoice() called");

			let invoice = this.get_invoice_doc();

			if (!invoice) {
				throw new Error("Invoice document not found");
			}

			return new Promise((resolve, reject) => {
				invoice
					.save("Save", function () {
						console.log("[Invoice] Invoice saved via frappe.db.save");
						resolve(invoice);
					})
					.catch((error) => {
						console.error("[Invoice] Error in save:", error);
						reject(error);
					});
			});
		},

		clear_invoice() {
			console.log("[Invoice] Clearing invoice");

			// Reset all data
			this.invoice_doc = null;
			this.customer = "";
			this.customer_name = "";
			this.vehicle_number = "";
			this.items = [];
			this.additional_discount = 0;
			this.additional_discount_percentage = 0;
			this.discount_amount = 0;
			this.total_tax = 0;
			this.subtotal = 0;
			this.grand_total = 0;
			this.rounded_total = 0;
			this.total_qty = 0;
			this.loaded_draft_name = null;

			// Clear employee fields
			this.service_employee = null;
			this.service_employee_name = null;
			this.service_employee_designation = null;
			this.service_employee_department = null;

			// Emit events to clear UI components
			this.eventBus.emit("invoice_cleared");
			this.eventBus.emit("clear_employee_selection");
			this.eventBus.emit("clear_customer");
			this.eventBus.emit("clear_vehicle_number");
			this.eventBus.emit("clear_all_fields");

			console.log("[Invoice] Invoice cleared successfully");
		},
		// Handle item reordering from drag and drop
		handleItemReorder(reorderData) {
			const { fromIndex, toIndex } = reorderData;

			if (fromIndex === toIndex) return;

			// Create a copy of the items array
			const newItems = [...this.items];

			// Remove the item from its original position
			const [movedItem] = newItems.splice(fromIndex, 1);

			// Insert the item at its new position
			newItems.splice(toIndex, 0, movedItem);

			// Update the items array
			this.items = newItems;

			// Show success feedback
			this.eventBus.emit("show_message", {
				title: __("Item order updated"),
				color: "success",
			});

			// Optionally, you can also update the idx field for each item
			this.items.forEach((item, index) => {
				item.idx = index + 1;
			});
		},
	},

	mounted() {
		this.eventBus.on("draft_selected", async (draftName) => {
			console.log("[Invoice] Draft selected:", draftName);

			try {
				// Fetch the full draft invoice document
				const response = await frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Sales Invoice",
						name: draftName,
					},
				});

				if (response.message) {
					console.log("[Invoice] Draft data received:", response.message);

					// IMPORTANT: Store the draft name before loading
					this.loaded_draft_name = draftName;

					// Load the complete draft invoice
					this.load_invoice(response.message);

					frappe.show_alert({
						message: this.__("Draft invoice {0} loaded successfully", [draftName]),
						indicator: "green",
					});
				}
			} catch (error) {
				console.error("[Invoice] Error loading draft:", error);
				frappe.show_alert({
					message: this.__("Error loading draft invoice: ") + (error.message || error),
					indicator: "red",
				});
			}
		});

		// Listen for odometer data updates from InvoiceSummary
		this.eventBus.on("update_odometer_data", (data) => {
			console.log("[Invoice] Odometer data received:", data);

			this.custom_odometer_reading = data.custom_odometer_reading;
			this.contact_mobile = data.contact_mobile || "";
			this.custom_vehicle_no = data.custom_vehicle_no || "";

			// Update invoice_doc immediately
			if (this.invoice_doc) {
				this.invoice_doc.custom_has_oil_item = data.custom_has_oil_item || 0;
				this.invoice_doc.custom_odometer_reading = data.custom_odometer_reading;
				this.invoice_doc.contact_mobile = data.contact_mobile || "";
				this.invoice_doc.custom_vehicle_no = data.custom_vehicle_no || "";

				console.log("[Invoice] invoice_doc updated with odometer data");
			}

			// Broadcast update
			this.broadcastInvoiceUpdate();
		});

		// Listen for customer details from Customer component
		this.eventBus.on("update_customer_details", (data) => {
			console.log("[Invoice] Customer details received:", data);

			// Store customer mobile and vehicle
			this.contact_mobile = data.contact_mobile || "";
			this.custom_vehicle_no = data.custom_vehicle_no || "";

			// Update invoice_doc
			if (this.invoice_doc) {
				this.invoice_doc.contact_mobile = data.contact_mobile || "";
				this.invoice_doc.custom_vehicle_no = data.custom_vehicle_no || "";
			}
		});

		this.eventBus.on("employee_selected", (data) => {
			console.log("[Invoice] employee_selected event received:", data);

			if (!data || !data.employee_id) {
				// Employee cleared
				this.clearServiceEmployee();
				return;
			}

			// Update employee data
			this.service_employee = data.employee_id;
			this.service_employee_name = data.employee_name;
			this.service_employee_designation = data.designation || null;
			this.service_employee_department = data.department || null;

			// Update invoice document
			this.updateServiceEmployeeInDoc();

			console.log("[Invoice] Service employee set:", {
				id: this.service_employee,
				name: this.service_employee_name,
			});
		});

		this.eventBus.on("check_items_for_service", (data) => {
			console.log("[Invoice] check_items_for_service event received");

			const hasCarWashService = this.checkForCarWashServices();

			if (data && typeof data.callback === "function") {
				data.callback(hasCarWashService);
			}
		});

		this.$nextTick(() => {
			const hasCarWashService = this.checkForCarWashServices();
			if (hasCarWashService) {
				console.log("[Invoice] Car wash service detected on mount");
				this.eventBus.emit("show_employee_selection", true);
			}
		});

		// ADD THESE NEW EVENT LISTENERS
		this.eventBus.on("get_current_invoice_from_component", () => {
			console.log("[Invoice] get_current_invoice_from_component event received");
			const invoiceData = this.prepareForPayment();
			if (invoiceData) {
				this.eventBus.emit("current_invoice_data", invoiceData);
			}
		});

		this.eventBus.on("prepare_invoice_for_payment", () => {
			console.log("[Invoice] prepare_invoice_for_payment event received");
			const invoice = this.prepareForPayment();
			this.eventBus.emit("invoice_prepared", invoice);
		});

		this.eventBus.on("show_payment_modal", () => {
			console.log("[Invoice] show_payment_modal event received");
			this.show_payment();
		});
		this.eventBus.on("update_offers_counters", (data) => {
			console.log("[Invoice] Offers counter updated:", data);
			this.offersCount = data.offersCount || 0;
		});

		this.eventBus.on("update_coupons_counters", (data) => {
			console.log("[Invoice] Coupons counter updated:", data);
			this.couponsCount = data.couponsCount || 0;
		});

		// FIXED: Listen for item groups registration
		this.eventBus.on("register_item_groups", (groups) => {
			console.log("[Invoice] Item groups registered:", groups);
			this.items_group = ["ALL", ...groups];
		});

		// Load saved column preferences
		this.loadColumnPreferences();

		// Register event listeners for POS profile, items, customer, offers, etc.
		this.eventBus.on("register_pos_profile", (data) => {
			this.pos_profile = data.pos_profile;
			this.company = data.company || null;
			this.customer = data.pos_profile.customer;
			this.pos_opening_shift = data.pos_opening_shift;
			this.stock_settings = data.stock_settings;
			const prec = parseInt(data.pos_profile.posa_decimal_precision);
			if (!isNaN(prec)) {
				this.float_precision = prec;
				this.currency_precision = prec;
			}
			this.invoiceType = this.pos_profile.posa_default_sales_order ? "Order" : "Invoice";
			this.initializeItemsHeaders();

			// Add this block to handle currency initialization
			if (this.pos_profile.posa_allow_multi_currency) {
				this.fetch_available_currencies()
					.then(async () => {
						// Set default currency after currencies are loaded
						this.selected_currency = this.pos_profile.currency;
						// Fetch proper exchange rate from server
						await this.update_currency_and_rate();
					})
					.catch((error) => {
						console.error("Error initializing currencies:", error);
						this.eventBus.emit("show_message", {
							title: __("Error loading currencies"),
							color: "error",
						});
					});
			}

			this.fetch_price_lists();
			this.update_price_list();
		});

		this.eventBus.on("add_item", (item) => {
			this.add_item(item);
		});
		this.eventBus.on("update_customer", (customer) => {
			console.log("[Invoice] update_customer event received:", customer);
			this.customer = customer;

			// Sync to invoice_doc
			if (this.invoice_doc) {
				this.invoice_doc.customer = customer;
			}

			// Trigger any necessary updates
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		});
		this.eventBus.on("fetch_customer_details", () => {
			this.fetch_customer_details();
		});
		this.eventBus.on("clear_invoice", () => {
			this.clear_invoice();
		});
		this.eventBus.on("load_invoice", (data) => {
			this.load_invoice(data);
		});
		this.eventBus.on("load_order", (data) => {
			this.new_order(data);
		});
		this.eventBus.on("set_offers", (data) => {
			this.posOffers = data;
		});
		this.eventBus.on("update_invoice_offers", (data) => {
			this.updateInvoiceOffers(data);
		});
		this.eventBus.on("update_invoice_coupons", (data) => {
			this.posa_coupons = data;
			this.handelOffers();
		});
		this.eventBus.on("set_all_items", (data) => {
			this.allItems = data;
			this.items.forEach((item) => {
				this.update_item_detail(item);
			});
		});
		this.eventBus.on("load_return_invoice", (data) => {
			console.log("Invoice component received load_return_invoice event with data:", data);
			this.load_invoice(data.invoice_doc);
			this.loaded_draft_name = null;
			// Explicitly mark as return invoice
			this.invoiceType = "Return";
			this.invoiceTypes = ["Return"];
			this.invoice_doc.is_return = 1;
			// Ensure negative values for returns
			if (this.items && this.items.length) {
				this.items.forEach((item) => {
					// Ensure item quantities are negative
					if (item.qty > 0) item.qty = -Math.abs(item.qty);
					if (item.stock_qty > 0) item.stock_qty = -Math.abs(item.stock_qty);
				});
			}
			if (data.return_doc) {
				console.log("Return against existing invoice:", data.return_doc.name);
				this.discount_amount = data.return_doc.discount_amount || 0;
				this.additional_discount = data.return_doc.discount_amount || 0;
				this.return_doc = data.return_doc;
				// Set return_against reference
				this.invoice_doc.return_against = data.return_doc.name;
			} else {
				console.log("Return without invoice reference");
				// For return without invoice, reset discount values
				this.discount_amount = 0;
				this.additional_discount = 0;
				this.additional_discount_percentage = 0;
			}
			console.log("Invoice state after loading return:", {
				invoiceType: this.invoiceType,
				is_return: this.invoice_doc.is_return,
				items: this.items.length,
				customer: this.customer,
			});
		});

		// Listener to get current invoice on demand
		this.eventBus.on("get_current_invoice_from_component", () => {
			console.log("[Invoice] get_current_invoice_from_component event received");
			const invoiceData = this.prepareForPayment();
			if (invoiceData) {
				this.eventBus.emit("current_invoice_data", invoiceData);
			}
		});

		// Listener to prepare invoice for payment
		this.eventBus.on("prepare_invoice_for_payment", () => {
			console.log("[Invoice] prepare_invoice_for_payment event received");
			this.prepareForPayment();
			this.eventBus.emit("invoice_prepared", this.invoice_doc);
		});

		this.eventBus.on("set_new_line", (data) => {
			this.new_line = data;
		});

		if (this.pos_profile.posa_allow_multi_currency) {
			this.fetch_available_currencies();
		}

		// Listen for reset_posting_date to reset posting date after invoice submission
		this.eventBus.on("reset_posting_date", () => {
			this.posting_date = frappe.datetime.nowdate();
		});

		this.eventBus.on("calc_uom", this.calc_uom);

		this.eventBus.on("item-drag-start", () => {
			this.showDropFeedback(true);
		});

		this.eventBus.on("item-drag-end", () => {
			this.showDropFeedback(false);
		});
	},

	beforeDestroy() {
		// Cleanup if needed
	},

	// Cleanup event listeners before component is destroyed
	beforeUnmount() {
		this.eventBus.off("draft_selected");
		this.eventBus.off("update_offers_counters");
		this.eventBus.off("update_coupons_counters");
		this.eventBus.off("register_item_groups");
		// Existing cleanup
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("add_item");
		this.eventBus.off("update_customer");
		this.eventBus.off("fetch_customer_details");
		this.eventBus.off("clear_invoice");
		// Cleanup reset_posting_date listener
		this.eventBus.off("reset_posting_date");

		this.eventBus.off("get_current_invoice_from_component");
		this.eventBus.off("prepare_invoice_for_payment");

		// Clean up employee selection event listeners
		this.eventBus.off("employee_selected");
		this.eventBus.off("check_items_for_service");

		console.log("[Invoice] Employee event listeners cleaned up");

		this.eventBus.off("update_odometer_data");
        this.eventBus.off("update_customer_details");
	},

	// Register global keyboard shortcuts when component is created
	created() {
		document.addEventListener("keydown", this.shortOpenPayment.bind(this));
		document.addEventListener("keydown", this.shortDeleteFirstItem.bind(this));
		document.addEventListener("keydown", this.shortOpenFirstItem.bind(this));
		document.addEventListener("keydown", this.shortSelectDiscount.bind(this));
	},

	// Remove global keyboard shortcuts when component is unmounted
	unmounted() {
		document.removeEventListener("keydown", this.shortOpenPayment);
		document.removeEventListener("keydown", this.shortDeleteFirstItem);
		document.removeEventListener("keydown", this.shortOpenFirstItem);
		document.removeEventListener("keydown", this.shortSelectDiscount);
	},

	watch: {
		...invoiceWatchers,

		// Watch invoice_doc changes and broadcast them
		invoice_doc: {
			handler(newVal) {
				if (newVal) {
					console.log("[Invoice] invoice_doc changed, broadcasting update");
					this.broadcastInvoiceUpdate();
				}
			},
			deep: true,
		},

		// Watch items changes and update invoice_doc (single consolidated watcher)
		items: {
			handler(newItems, oldItems) {
				console.log("[Invoice] Items changed:", {
					count: newItems.length,
					oldCount: oldItems ? oldItems.length : 0,
				});

				// Update invoice_doc items (keep invoice_doc in sync)
				if (this.invoice_doc) {
					this.invoice_doc.items = newItems;
				}

				// --- Engine oil / odometer handling ---
				console.log("[Invoice] Items changed, checking for Engine Oil");
				const hasOilItem = this.checkForEngineOilItem();
				// Notify InvoiceSummary (or other listeners) whether to show odometer
				this.eventBus.emit("show_odometer_field", hasOilItem);

				// If no engine-oil items, clear only the odometer reading (keep mobile/vehicle)
				if (!hasOilItem) {
					this.custom_odometer_reading = null;
					if (this.invoice_doc) {
						// use 0/false depending what backend expects
						this.invoice_doc.custom_has_oil_item = 0;
						this.invoice_doc.custom_odometer_reading = null;
					}
				} else {
					// if has oil, ensure invoice_doc flag is set so load/save knows about it
					if (this.invoice_doc) {
						this.invoice_doc.custom_has_oil_item = 1;
					}
				}

				// --- Car wash / employee handling ---
				console.log("[Invoice] Items changed, checking for car wash services");
				const hasCarWashService = this.checkForCarWashServices();
				// Emit event to show/hide employee selection in summary
				this.eventBus.emit("show_employee_selection", hasCarWashService);

				// If no car wash services, clear any selected employee
				if (!hasCarWashService && this.service_employee) {
					this.clearServiceEmployee();
				}

				// --- Force Vue to recalculate computed properties and re-sync totals ---
				this.$nextTick(() => {
					// Sync all computed totals to invoice_doc
					if (this.invoice_doc) {
						this.invoice_doc.net_total = this.subtotal;
						this.invoice_doc.grand_total = this.grand_total;
						this.invoice_doc.rounded_total = this.rounded_total;
						this.invoice_doc.total_qty = this.total_qty;

						// Also keep odometer/mobile/vehicle in invoice_doc if present in component state
						// (do not overwrite mobile/vehicle when odometer cleared earlier)
						this.invoice_doc.custom_odometer_reading = this.custom_odometer_reading || this.invoice_doc.custom_odometer_reading || null;
						this.invoice_doc.contact_mobile = this.contact_mobile || this.invoice_doc.contact_mobile || "";
						this.invoice_doc.custom_vehicle_no = this.custom_vehicle_no || this.invoice_doc.custom_vehicle_no || "";
					}

					// Force UI update
					this.$forceUpdate();

					// Recalculate discounts
					this.apply_additional_discount();
				});
			},
			deep: true,
			immediate: false,
		},

		// Watch totals and sync to invoice_doc
		grand_total(newVal) {
			console.log("[Invoice] grand_total changed:", newVal);
			if (this.invoice_doc) {
				this.invoice_doc.grand_total = newVal;
				this.invoice_doc.rounded_total = this.rounded_total;
			}
		},

		total_qty(newVal) {
			console.log("[Invoice] total_qty computed changed:", newVal);
		},

		subtotal(newVal) {
			console.log("[Invoice] subtotal computed changed:", newVal);
			if (this.invoice_doc) {
				this.invoice_doc.net_total = newVal;
			}
		},

		// WATCH DISCOUNT
		discount_amount(newVal) {
			console.log("[Invoice] discount_amount changed:", newVal);
			if (this.invoice_doc) {
				this.invoice_doc.discount_amount = newVal;
			}
		},

		customer(newVal) {
			console.log("[Invoice] customer changed:", newVal);
			if (this.invoice_doc) {
				this.invoice_doc.customer = newVal;
			}
		},

		item_group(newVal) {
			console.log("[Invoice] Item group changed to:", newVal);
			this.eventBus.emit("update_item_group", newVal);
		},

		items_view(newVal) {
			console.log("[Invoice] Items view changed to:", newVal);
			this.eventBus.emit("update_items_view", newVal);
		},

		service_employee: {
			handler(newVal) {
				if (newVal) {
					console.log("[Invoice] Service employee changed:", newVal);
					this.updateServiceEmployeeInDoc();
				}
			},
			immediate: false,
		},
	},

};
</script>

<style scoped>
/* Invoice Container - Flex layout for fixed footer */
.invoice-container {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	background: white;
}

/* Scrollable Content Area */
.invoice-content {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 10px;
	background-color: #fafafa;
}

/* Card background adjustments */
.cards {
	background-color: var(--surface-secondary) !important;
	margin: 0 !important;
}

/* Style for selected checkbox button */
.v-checkbox-btn.v-selected {
	background-color: var(--submit-start) !important;
	color: white;
}

/* Bottom border for elements */
.border_line_bottom {
	border-bottom: 1px solid var(--field-border);
}

/* Disable pointer events for elements */
.disable-events {
	pointer-events: none;
}

/* Style for customer balance field */
:deep(.balance-field) {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	flex-wrap: nowrap;
}

/* Style for balance value text */
:deep(.balance-value) {
	font-size: 1.5rem;
	font-weight: bold;
	color: var(--primary-start);
	margin-left: var(--dynamic-xs);
}

/* Red border and label for return mode card */
.return-mode {
	border: 2px solid rgb(var(--v-theme-error)) !important;
	position: relative;
}

/* Label for return mode card */
.return-mode::before {
	content: "RETURN";
	position: absolute;
	top: 0;
	right: 0;
	background-color: rgb(var(--v-theme-error));
	color: white;
	padding: 4px 12px;
	font-weight: bold;
	border-bottom-left-radius: 8px;
	z-index: 1;
}

/* Dynamic padding for responsive layout */
.dynamic-padding {
	/* Uniform spacing for better alignment */
	padding: var(--dynamic-sm);
}

/* Responsive breakpoints */
@media (max-width: 768px) {
	.dynamic-padding {
		/* Smaller uniform padding on tablets */
		padding: var(--dynamic-xs);
	}

	.dynamic-padding .v-row {
		margin: 0 -2px;
	}

	.dynamic-padding .v-col {
		padding: 2px 4px;
	}
}

@media (max-width: 480px) {
	.dynamic-padding {
		padding: var(--dynamic-xs);
	}

	.dynamic-padding .v-row {
		margin: 0 -1px;
	}

	.dynamic-padding .v-col {
		padding: 1px 2px;
	}
}

.column-selector-container {
	display: none !important;
	justify-content: flex-end;
	padding: 8px 16px;
	background-color: var(--surface-secondary);
	border-radius: 8px 8px 0 0;
	position: absolute;
	top: 0;
	right: 0;
	transform: translateY(-100%);
}

:deep([data-theme="dark"]) .column-selector-container,
:deep(.v-theme--dark) .column-selector-container {
	background-color: #1e1e1e;
}

.column-selector-btn {
	font-size: 0.875rem;
}

.items-table-wrapper {
	position: relative;
	margin-top: var(--dynamic-xl);
}

/* New styles for improved column switches */
:deep(.column-switch) {
	margin: 0;
	padding: 0;
}

:deep(.column-switch .v-switch__track) {
	opacity: 0.7;
}

:deep(.column-switch .v-switch__thumb) {
	transform: scale(0.8);
}

:deep(.column-switch .v-label) {
	opacity: 0.9;
	font-size: 0.95rem;
}

/* Fixed Controls Footer */
.invoice-controls {
	flex-shrink: 0;
	background: white;
	border-top: 2px solid #e0e0e0;
	padding: 12px;
	z-index: 100;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

/* Scrollbar Styling */
.invoice-content::-webkit-scrollbar {
	width: 6px;
}

.invoice-content::-webkit-scrollbar-track {
	background: #f1f1f1;
	border-radius: 3px;
}

.invoice-content::-webkit-scrollbar-thumb {
	background: #999;
	border-radius: 3px;
}

.invoice-content::-webkit-scrollbar-thumb:hover {
	background: #666;
}
/* ------ Center QTY cell and controls ------ */
/* targets qty UI inside the table cells (qty-control OR amount-value used for qty) */
.modern-items-table :deep(td) > .qty-control,
.modern-items-table :deep(td) .qty-control,
.modern-items-table :deep(td) > .amount-value.qty-cell,
.modern-items-table :deep(td) .amount-value.qty-cell {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	width: 100%;
	box-sizing: border-box;
	padding: 4px 0;
}

/* If you used .qty-value in the control template, make sure it's centered, bold and stable width */
.qty-value {
	display: inline-block;
	min-width: 56px;
	text-align: center;
	font-weight: 600;
	padding: 2px 6px;
	border-radius: 6px;
	font-variant-numeric: lining-nums tabular-nums;
}

/* Make amount-value used for qty (fallback) centered */
.modern-items-table :deep(td) .amount-value {
	display: inline-block;
	width: 100%;
	text-align: center;
}

/* Vertical centering for table cells to keep icons/buttons centered */
.modern-items-table :deep(td) {
	vertical-align: middle;
}

/* ----- Actions column: center buttons and keep them compact/tappable ----- */
.action-buttons,
.modern-items-table :deep(td) > .action-buttons {
	display: flex;
	align-items: center;
	justify-content: center; /* center horizontally inside the column */
	gap: 8px;
	min-width: 120px; /* helps keep column width stable */
}

/* tighten button sizes and ensure good tap targets */
.item-action-btn {
	width: 36px !important;
	height: 36px !important;
	min-width: 36px !important;
	padding: 0 !important;
	border-radius: 8px !important;
	display: inline-flex !important;
	align-items: center;
	justify-content: center;
}

/* icon size inside */
.item-action-btn .v-icon,
.qty-btn .v-icon {
	font-size: 18px !important;
}

/* On small screens, increase touch target slightly */
@media (max-width: 600px) {
	.item-action-btn,
	.qty-btn {
		width: 44px !important;
		height: 44px !important;
		min-width: 44px !important;
	}
	.qty-value {
		min-width: 64px;
		font-size: 1rem;
	}
}
</style>
