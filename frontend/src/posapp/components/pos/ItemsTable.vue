<template>
	<div class="my-0 py-0 overflow-y-auto items-table-container"
		:style="{ height: 'calc(100% - 80px)', maxHeight: 'calc(100% - 80px)' }"
		@dragover="onDragOverFromSelector($event)" @drop="onDropFromSelector($event)"
		@dragenter="onDragEnterFromSelector" @dragleave="onDragLeaveFromSelector">
		<v-data-table-virtual :headers="headers" :items="items" :theme="$theme.current" :expanded="expanded" show-expand
			item-value="posa_row_id" class="modern-items-table elevation-2" :items-per-page="itemsPerPage"
			expand-on-click density="compact" hide-default-footer :single-expand="true" :header-props="headerProps"
			:no-data-text="__('No items in cart')" @update:expanded="
				(val) =>
					$emit(
						'update:expanded',
						val.map((v) => (typeof v === 'object' ? v.posa_row_id : v)),
					)
			" :search="itemSearch">
			<!-- Item name column -->
			<template v-slot:item.item_name="{ item }">
				<div class="d-flex align-center">
					<span>{{ item.item_name }}</span>
					<v-chip v-if="item.is_bundle" color="secondary" size="x-small" class="ml-1">{{
						__("Bundle")
						}}</v-chip>
					<v-chip v-if="item.name_overridden" color="primary" size="x-small" class="ml-1">{{
						__("Edited")
						}}</v-chip>
					<v-icon v-if="pos_profile.posa_allow_line_item_name_override && !item.posa_is_replace"
						size="x-small" class="ml-1" @click.stop="openNameDialog(item)">
						mdi-pencil
					</v-icon>
					<v-icon v-if="item.name_overridden" size="x-small" class="ml-1" @click.stop="resetItemName(item)">
						mdi-undo
					</v-icon>
				</div>
			</template>

			<!-- Quantity column -->
			<template v-slot:item.qty="{ item }">
				<div class="qty-control" :class="{ 'negative-number': isNegative(item.qty) }" role="group"
					:aria-label="__('Quantity controls')">
					<!-- Decrease -->
					<v-btn class="qty-btn qty-decrease" icon size="small" :disabled="!!item.posa_is_replace"
						@click.stop="subtractOne(item)" :aria-label="__('Decrease quantity')" title="Decrease">
						<v-icon size="18">mdi-minus</v-icon>
					</v-btn>

					<!-- Quantity display -->
					<div class="qty-value">
						{{ formatFloat(item.qty, hide_qty_decimals ? 0 : undefined) }}
					</div>

					<!-- Increase -->
					<v-btn class="qty-btn qty-increase" icon size="small" :disabled="
							!!item.posa_is_replace ||
							((!stock_settings.allow_negative_stock ||
								pos_profile.posa_block_sale_beyond_available_qty) &&
								item.max_qty !== undefined &&
								item.qty >= item.max_qty)
						" @click.stop="addOne(item)" :aria-label="__('Increase quantity')" title="Increase">
						<v-icon size="18">mdi-plus</v-icon>
					</v-btn>
				</div>
			</template>

			<!-- Rate column (hidden if shouldHidePricing is true) -->
			<template v-if="!shouldHidePricing" v-slot:item.rate="{ item }">
				<div class="currency-display">
					<span class="currency-symbol">{{ currencySymbol(displayCurrency) }}</span>
					<span class="amount-value" :class="{ 'negative-number': isNegative(item.rate) }">{{
						formatCurrency(item.rate)
						}}</span>
				</div>
			</template>

			<!-- Amount column -->
			<template v-slot:item.amount="{ item }">
				<div class="currency-display">
					<span class="currency-symbol">{{ currencySymbol(displayCurrency) }}</span>
					<span class="amount-value" :class="{ 'negative-number': isNegative(item.qty * item.rate) }">{{
						formatCurrency(item.qty * item.rate) }}
					</span>
				</div>
			</template>

			<!-- Actions column -->
			<template v-slot:item.actions="{ item }">
				<div class="actions-cell">
					<div class="actions-center" role="group" :aria-label="__('Item Actions')">
						<v-tooltip location="top">
							<template #activator="{ props }">
								<v-btn v-bind="props" :disabled="!!item.posa_is_replace"
									class="action-btn action-delete" variant="tonal" size="small"
									@click.stop="removeItem(item)" :aria-label="__('Remove item')" title="Remove">
									<v-icon size="18">mdi-trash-can-outline</v-icon>
								</v-btn>
							</template>
							<span>{{ __("Remove") }}</span>
						</v-tooltip>
					</div>
				</div>
			</template>

			<!-- Discount amount column (hidden if shouldHidePricing is true) -->
			<template v-if="!shouldHidePricing" v-slot:item.discount_amount="{ item }">
				<div class="currency-display">
					<span class="currency-symbol">{{ currencySymbol(displayCurrency) }}</span>
					<span class="amount-value" :class="{ 'negative-number': isNegative(item.discount_amount || 0) }">{{
						formatCurrency(item.discount_amount || 0) }}</span>
				</div>
			</template>

			<!-- Price list rate column (hidden if shouldHidePricing is true) -->
			<template v-if="!shouldHidePricing" v-slot:item.price_list_rate="{ item }">
				<div class="currency-display">
					<span class="currency-symbol">{{ currencySymbol(displayCurrency) }}</span>
					<span class="amount-value" :class="{ 'negative-number': isNegative(item.price_list_rate) }">{{
						formatCurrency(item.price_list_rate) }}</span>
				</div>
			</template>

			<!-- Offer toggle button column (hidden if shouldHidePricing is true) -->
			<template v-if="!shouldHidePricing" v-slot:item.posa_is_offer="{ item }">
				<v-btn size="x-small" color="primary" variant="tonal" class="ma-0 pa-0" @click.stop="toggleOffer(item)">
					{{ item.posa_offer_applied ? __("Remove Offer") : __("Apply Offer") }}
				</v-btn>
			</template>

			<!-- Expanded row content using Vuetify's built-in system -->
			<template v-slot:expanded-row="{ item }">
				<td :colspan="headers.length" class="ma-0 pa-0">
					<div class="expanded-content">
						<!-- Enhanced Item Details Form with better organization -->
						<div class="item-details-form">
							<!-- Basic Information Section -->
							<div class="form-section">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-information-outline</v-icon>
									<span class="section-title">{{ __("Basic Information") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Item Code')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details v-model="item.item_code" disabled
											prepend-inner-icon="mdi-barcode"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('QTY')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details :model-value="
												formatFloat(item.qty, hide_qty_decimals ? 0 : undefined)
											" @change="
												setFormatedQty(item, 'qty', null, false, $event.target.value)
											" :rules="[isNumber]" :disabled="!!item.posa_is_replace" prepend-inner-icon="mdi-numeric"></v-text-field>
										<div v-if="item.max_qty !== undefined" class="text-caption mt-1">
											{{
											__("In stock: {0}", [
											formatFloat(
											item.max_qty,
											hide_qty_decimals ? 0 : undefined,
											),
											])
											}}
										</div>
									</div>
									<div class="form-field">
										<v-select density="compact" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" :label="frappe._('UOM')" v-model="item.uom"
											:items="item.item_uoms" variant="outlined" item-title="uom" item-value="uom"
											hide-details @update:model-value="calcUom(item, $event)" :disabled="
												!!item.posa_is_replace ||
												(isReturnInvoice && invoice_doc.return_against)
											" prepend-inner-icon="mdi-weight"></v-select>
									</div>
								</div>
							</div>

							<!-- Pricing Section (hidden when parent requests pricing hide) -->
							<div v-if="!shouldHidePricing" class="form-section">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-currency-usd</v-icon>
									<span class="section-title">{{ __("Pricing & Discounts") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary" id="rate"
											:label="frappe._('Rate')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details :model-value="Math.round(item.rate || 0)"
											type="number" step="1" @change="[ 
												item.rate = Math.round($event.target.value || 0),
												setFormatedCurrency(item, 'rate', null, false, $event),
												calcPrices(item, $event.target.value, $event),
											]" :disabled="!pos_profile.posa_allow_user_to_edit_rate ||
												!!item.posa_is_replace ||
												!!item.posa_offer_applied
												" prepend-inner-icon="mdi-currency-usd"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											id="discount_percentage" :label="frappe._('Discount %')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="Math.round(item.discount_percentage || 0)"
											type="number" step="1" @change="[ 
												item.discount_percentage = Math.round($event.target.value || 0),
												setFormatedCurrency(
													item,
													'discount_percentage',
													null,
													false,
													$event,
												),
												calcPrices(item, $event.target.value, $event),
											]" :disabled="!pos_profile.posa_allow_user_to_edit_item_discount ||
												!!item.posa_is_replace ||
												!!item.posa_offer_applied
												" prepend-inner-icon="mdi-percent"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											id="discount_amount" :label="frappe._('Discount Amount')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="Math.round(item.discount_amount || 0)"
											type="number" step="1" @change="[ 
												item.discount_amount = Math.round($event.target.value || 0),
												setFormatedCurrency(
													item,
													'discount_amount',
													null,
													false,
													$event,
												),
												calcPrices(item, $event.target.value, $event),
											]" :disabled="!pos_profile.posa_allow_user_to_edit_item_discount ||
												!!item.posa_is_replace ||
												!!item.posa_offer_applied
												" prepend-inner-icon="mdi-tag-minus"></v-text-field>
									</div>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Price List Rate')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="Math.round(item.price_list_rate || 0)"
											type="number" step="1"
											:disabled="!pos_profile.posa_allow_price_list_rate_change"
											prepend-inner-icon="mdi-format-list-numbered"
											:prefix="currencySymbol(pos_profile.currency)"
											@change="changePriceListRate(item)"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Total Amount')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="formatCurrency(item.qty * item.rate)" disabled
											prepend-inner-icon="mdi-calculator"></v-text-field>
									</div>
									<div class="form-field" v-if="pos_profile.posa_allow_price_list_rate_change">
										<v-btn size="small" color="primary" variant="outlined" class="change-price-btn"
											@click.stop="changePriceListRate(item)">
											<v-icon size="small" class="mr-1">mdi-pencil</v-icon>
											{{ __("Change Price") }}
										</v-btn>
									</div>
								</div>
							</div>

							<!-- Stock Information Section -->
							<div class="form-section">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-warehouse</v-icon>
									<span class="section-title">{{ __("Stock Information") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Available QTY')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="formatFloat(item.actual_qty)" disabled
											prepend-inner-icon="mdi-package-variant"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Stock QTY')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details :model-value="formatFloat(item.stock_qty)"
											disabled prepend-inner-icon="mdi-scale-balance"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Stock UOM')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details v-model="item.stock_uom" disabled
											prepend-inner-icon="mdi-weight-pound"></v-text-field>
									</div>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Warehouse')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details v-model="item.warehouse" disabled
											prepend-inner-icon="mdi-warehouse"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Group')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field" hide-details v-model="item.item_group" disabled
											prepend-inner-icon="mdi-folder-outline"></v-text-field>
									</div>
									<div class="form-field" v-if="item.posa_offer_applied">
										<v-checkbox density="compact" :label="frappe._('Offer Applied')"
											v-model="item.posa_offer_applied" readonly hide-details class="mt-1"
											color="success"></v-checkbox>
									</div>
								</div>
							</div>

							<!-- Serial Number Section -->
							<div class="form-section" v-if="item.has_serial_no || item.serial_no">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-barcode-scan</v-icon>
									<span class="section-title">{{ __("Serial Numbers") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Serial No QTY')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details v-model="item.serial_no_selected_count" type="number" disabled
											prepend-inner-icon="mdi-counter"></v-text-field>
									</div>
								</div>
								<div class="form-row">
									<div class="form-field full-width">
										<v-autocomplete v-model="item.serial_no_selected" :items="item.serial_no_data"
											item-title="serial_no" item-value="serial_no" variant="outlined"
											density="compact" chips color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											:label="frappe._('Serial No')" multiple
											@update:model-value="setSerialNo(item)"
											prepend-inner-icon="mdi-barcode"></v-autocomplete>
									</div>
								</div>
							</div>

							<!-- Batch Number Section -->
							<div class="form-section" v-if="item.has_batch_no || item.batch_no">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-package-variant-closed</v-icon>
									<span class="section-title">{{ __("Batch Information") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Batch No. Available QTY')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details :model-value="formatFloat(item.actual_batch_qty)" disabled
											prepend-inner-icon="mdi-package-variant"></v-text-field>
									</div>
									<div class="form-field">
										<v-text-field density="compact" variant="outlined" color="primary"
											:label="frappe._('Batch No Expiry Date')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											hide-details v-model="item.batch_no_expiry_date" disabled
											prepend-inner-icon="mdi-calendar-clock"></v-text-field>
									</div>
									<div class="form-field">
										<v-autocomplete v-model="item.batch_no" :items="item.batch_no_data"
											item-title="batch_no" variant="outlined" density="compact" color="primary"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field"
											:label="frappe._('Batch No')"
											@update:model-value="setBatchQty(item, $event)" hide-details
											prepend-inner-icon="mdi-package-variant-closed">
											<template v-slot:item="{ props, item }">
												<v-list-item v-bind="props">
													<v-list-item-title v-html="item.raw.batch_no"></v-list-item-title>
													<v-list-item-subtitle v-html="
															`Available QTY  '${item.raw.batch_qty}' - Expiry Date ${item.raw.expiry_date}`"
														"></v-list-item-subtitle>
												</v-list-item>
											</template>
										</v-autocomplete>
									</div>
								</div>
							</div>

							<!-- Delivery Date Section -->
							<div class="form-section"
								v-if="pos_profile.posa_allow_sales_order && invoiceType == 'Order'">
								<div class="section-header">
									<v-icon size="small" class="section-icon">mdi-calendar-check</v-icon>
									<span class="section-title">{{ __("Delivery Information") }}</span>
								</div>
								<div class="form-row">
									<div class="form-field">
										<VueDatePicker v-model="item.posa_delivery_date" model-type="format"
											format="dd-MM-yyyy" :min-date="new Date()" auto-apply :dark="isDarkTheme"
											@update:model-value="validateDueDate(item)" />
									</div>
								</div>
							</div>
						</div>
					</div>
				</td>
			</template>
		</v-data-table-virtual>
		<v-dialog v-model="editNameDialog" max-width="400">
			<v-card>
				<v-card-title>{{ __("Item Name") }}</v-card-title>
				<v-card-text>
					<v-text-field v-model="editedName" :maxlength="140" />
				</v-card-text>
				<v-card-actions>
					<v-btn v-if="editNameTarget && editNameTarget.name_overridden" variant="text"
						@click="resetItemName(editNameTarget)">{{ __("Reset") }}</v-btn>
					<v-spacer></v-spacer>
					<v-btn variant="text" @click="editNameDialog = false">{{ __("Cancel") }}</v-btn>
					<v-btn color="primary" variant="text" @click="saveItemName">{{ __("Save") }}</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</div>
</template>

<script>
import _ from "lodash";
export default {
	name: "ItemsTable",
	props: {
		headers: Array,
		items: Array,
		expanded: Array,
		itemsPerPage: Number,
		itemSearch: String,
		pos_profile: Object,
		invoice_doc: Object,
		invoiceType: String,
		stock_settings: Object,
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		isNumber: Function,
		setFormatedQty: Function,
		setFormatedCurrency: Function,
		calcPrices: Function,
		calcUom: Function,
		setSerialNo: Function,
		setBatchQty: Function,
		validateDueDate: Function,
		removeItem: Function,
		subtractOne: Function,
		addOne: Function,
		isReturnInvoice: Boolean,
		toggleOffer: Function,
		changePriceListRate: Function,
		isNegative: Function,
		// NEW prop - parent decides when to hide pricing
		shouldHidePricing: {
			type: Boolean,
			default: false,
		},
	},
	data() {
		return {
			draggedItem: null,
			draggedIndex: null,
			dragOverIndex: null,
			isDragging: false,
			pendingAdd: null,
			editNameDialog: false,
			editNameTarget: null,
			editedName: "",
		};
	},
	computed: {
		headerProps() {
			return this.isDarkTheme ? { style: "background-color:#121212;color:#fff" } : {};
		},
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		hide_qty_decimals() {
			try {
				const saved = localStorage.getItem("posawesome_item_selector_settings");
				if (saved) {
					const opts = JSON.parse(saved);
					return !!opts.hide_qty_decimals;
				}
			} catch (e) {
				console.error("Failed to load item selector settings:", e);
			}
			return false;
		},
	},
	methods: {

		isCarWashItem(item) {
			if (!item) return false;

			const ig = item.item_group || '';
			const name = item.item_name || '';
			const code = item.item_code || '';

			return (
				ig.includes('Carwash') ||
				ig.includes('Car wash') ||
				name.includes('Carwash') ||
				name.includes('Car wash') ||
				code.includes('Carwash') ||
				code.includes('Car wash')
			);
		},

		// === SAFE: applyRatesToItem ===
		// Call this whenever you update rates from server so qty is preserved.
		applyRatesToItem(item, rates) {
			try {
				const existingQty = Number(item.qty);

				// update numeric rate fields only (do NOT overwrite qty)
				item.base_rate = Number(rates.base_rate ?? item.base_rate ?? 0);
				item.rate = Number(rates.rate ?? item.rate ?? 0);
				item.base_price_list_rate = Number(rates.base_price_list_rate ?? item.base_price_list_rate ?? 0);
				item.price_list_rate = Number(rates.price_list_rate ?? item.price_list_rate ?? 0);
				item.exchange_rate = Number(rates.exchange_rate ?? item.exchange_rate ?? 1);

				// detect service (Carwash) - adjust regex if you use strict case-sensitive matching
				const looksLikeService = item.is_service_item === 1 || item.service_item === 1
					|| /Carwash|car wash|bike wash|bikewash/i.test(item.item_group || item.item_name || '');

				if (looksLikeService) {
					// restore/ensure qty >= 1 for service items
					item.qty = (Number.isFinite(existingQty) && existingQty > 0) ? existingQty : 1;
					item.is_service_item = 1;
					item.update_stock = 0;
				} else {
					// for stock items keep numeric qty (don't implicitly zero valid qty)
					item.qty = Number.isFinite(existingQty) ? existingQty : (Number(rates.qty) || 0);
				}

			} catch (e) {
				console.warn('[applyRatesToItem] error applying rates to', item && item.item_name, e);
			}
		},


		async update_item_detail(item, force_update = false) {
			// Defensive: ensure object
			item = item || {};

			// Normalize flags
			item.is_service_item = item.is_service_item ? 1 : 0;

			// If CarWash/service item -> protect qty and skip server normalization
			const isCarWash = this.isCarWashItem ? this.isCarWashItem(item) : (item.is_service_item === 1);
			if (isCarWash || item.is_service_item) {

				// Ensure qty numeric and default to 1 for service items
				item.qty = Number(item.qty);
				if (!Number.isFinite(item.qty) || item.qty <= 0) {
					item.qty = 1;
				}

				item.actual_qty = item.qty;
				item.is_service_item = 1;
				item.update_stock = 0;

				return; // do not call server update that might overwrite qty
			}

			// Non-service items: coerce qty to numeric (default 0)
			item.qty = Number(item.qty);
			if (!Number.isFinite(item.qty)) item.qty = 0;

			// Continue your existing stock/rate update logic here for stock items.
			try {
				// If you have a helper that fetches rates/stock, call it (keeps existing behavior).
				if (typeof this._fetchAndUpdateStockAndRate === 'function') {
					await this._fetchAndUpdateStockAndRate(item, force_update);
				} else {
					// Insert your original server call / logic here
				}
			} catch (e) {
				console.warn('[ItemsTable] update_item_detail error for stock item:', e);
			}

		},
		calc_stock_qty(item, qty) {
			// ===== CARWASH PROTECTION =====
			if (this.isCarWashItem(item)) {
				item.qty = 1;
				item.stock_qty = 1;
				return;
			}
			// ===== END PROTECTION =====

			// Regular stock calculation for non-CarWash items
			const stock_qty = parseFloat(qty);
			item.stock_qty = this.flt(stock_qty);
		},

		setFormatedQty(item, field_name, precision, no_negative, value) {
			// ===== CARWASH PROTECTION: Don't allow qty changes for CarWash =====
			if (this.isCarWashItem(item)) {
				item.qty = 1;
				item.stock_qty = 1;
				return 1;
			}
			// ===== END PROTECTION =====

			// For regular items - call the parent's setFormatedQty if it exists
			if (this.setFormatedQty) {
				return this.setFormatedQty(item, field_name, precision, no_negative, value);
			}

			// Fallback: just set the value directly
			item[field_name] = value;
			return value;
		},
		onDragOverFromSelector(event) {
			// Check if drag data is from item selector
			const dragData = event.dataTransfer.types.includes("application/json");
			if (dragData) {
				event.preventDefault();
				event.dataTransfer.dropEffect = "copy";
			}
		},

		onDragEnterFromSelector() {
			this.$emit("show-drop-feedback", true);
		},

		onDragLeaveFromSelector(event) {
			// Only hide feedback if leaving the entire table area
			if (!event.currentTarget.contains(event.relatedTarget)) {
				this.$emit("show-drop-feedback", false);
			}
		},

		onDropFromSelector(event) {
			event.preventDefault();

			try {
				const dragData = JSON.parse(event.dataTransfer.getData("application/json"));

				if (dragData.type === "item-from-selector") {
					this.addItemDebounced(dragData.item);
					this.$emit("item-dropped", false);
				}
			} catch (error) {
				console.error("Error parsing drag data:", error);
			}
		},
		addItem(newItem) {
			// safe merge: match by item_code + uom + rate if possible
			const match = this.items.find(
				(item) =>
					item.item_code === newItem.item_code &&
					item.uom === newItem.uom &&
					item.rate === newItem.rate,
			);

			if (match) {
				// If found, increment quantity (ensure numeric)
				match.qty = Number(match.qty) + (Number(newItem.qty) || 1);
				match.amount = Number(match.qty) * Number(match.rate || 0);
				this.$forceUpdate && this.$forceUpdate();
				return;
			}

			// If no exact match, attempt to find by item_code and merge safely
			const idx = this.items.findIndex(i => i.item_code === newItem.item_code);
			if (idx !== -1) {
				// merge rates safely using helper if rates present on newItem
				if (newItem.rate !== undefined || newItem.base_rate !== undefined) {
					this.applyRatesToItem(this.items[idx], newItem);
					// merge non-rate fields carefully
					this.items[idx].description = newItem.description ?? this.items[idx].description;
					this.items[idx].price_list_rate = newItem.price_list_rate ?? this.items[idx].price_list_rate;
					this.$forceUpdate && this.$forceUpdate();
				} else {
					// just update qty if that's the purpose
					this.items[idx].qty = (Number(this.items[idx].qty) || 0) + (Number(newItem.qty) || 1);
				}
				return;
			}

			// If genuinely a new item: ensure qty is correct (service->1 else numeric)
			const newItemCopy = { ...newItem };
			const isService = newItemCopy.is_service_item === 1 || /carwash|car wash|bike wash|bikewash/i.test(newItemCopy.item_group || newItemCopy.item_name || '');
			newItemCopy.qty = isService ? (Number(newItemCopy.qty) || 1) : (Number(newItemCopy.qty) || 0);
			newItemCopy.is_service_item = isService ? 1 : (newItemCopy.is_service_item ? 1 : 0);
			newItemCopy.update_stock = isService ? 0 : (typeof newItemCopy.update_stock !== 'undefined' ? newItemCopy.update_stock : 1);

			this.items.push(newItemCopy);
			this.$forceUpdate && this.$forceUpdate();
		},
		addItemDebounced: _.debounce(function (item) {
			this.addItem(item);
		}, 50),
		openNameDialog(item) {
			this.editNameTarget = item;
			this.editedName = item.item_name;
			this.editNameDialog = true;
		},
		sanitizeName(name) {
			const div = document.createElement("div");
			div.innerHTML = name;
			return (div.textContent || div.innerText || "").trim().slice(0, 140);
		},
		saveItemName() {
			if (!this.editNameTarget) return;
			const clean = this.sanitizeName(this.editedName);
			if (!this.editNameTarget.original_item_name) {
				this.editNameTarget.original_item_name = this.editNameTarget.item_name;
			}
			this.editNameTarget.item_name = clean;
			this.editNameTarget.name_overridden = clean !== this.editNameTarget.original_item_name ? 1 : 0;
			this.editNameDialog = false;
		},
		resetItemName(item) {
			if (item && item.original_item_name) {
				item.item_name = item.original_item_name;
				item.name_overridden = 0;
			}
			if (this.editNameTarget === item) {
				this.editedName = item.item_name;
			}
		},
	},
};
</script>

<style scoped>
/* Modern table styling with enhanced visual hierarchy */
.modern-items-table {
	border-radius: var(--border-radius-lg);
	overflow: hidden;
	box-shadow: var(--shadow-md);
	border: 1px solid rgba(0, 0, 0, 0.09);
	height: 100%;
	display: flex;
	flex-direction: column;
	transition: all 0.3s ease;
}

/* Ensure items table can scroll when many rows exist */
.items-table-container {
	overflow-y: auto;
}

/* Table wrapper styling */
.modern-items-table :deep(.v-data-table__wrapper),
.modern-items-table :deep(.v-table__wrapper) {
	border-radius: var(--border-radius-sm);
	height: 100%;
	overflow-y: auto;
	scrollbar-width: thin;
}

/* Table header styling */
.modern-items-table :deep(th) {
	font-weight: 600;
	font-size: 0.9rem;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	padding: 12px 16px;
	transition: background-color var(--transition-normal);
	border-bottom: 2px solid var(--table-header-border);
	background-color: var(--table-header-bg, var(--surface-secondary, #f5f5f5));
	color: var(--table-header-text);
	position: sticky;
	top: 0;
	z-index: 1;
}

/* Table row styling */
.modern-items-table :deep(tr) {
	transition: all 0.2s ease;
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.modern-items-table :deep(tr:hover) {
	background-color: var(--table-row-hover);
	transform: translateY(-1px);
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

/* Table cell styling */
.modern-items-table :deep(td) {
	padding: 12px 16px;
	vertical-align: middle;
}

/* Expanded content styling */
.expanded-content {
	padding: 24px;
	background: linear-gradient(135deg, var(--surface-primary) 0%, var(--surface-secondary) 100%);
	border-radius: 0 0 var(--border-radius-lg) var(--border-radius-lg);
	box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.03);
	animation: fadeIn 0.4s ease;
	border: 1px solid var(--border-color, rgba(0, 0, 0, 0.06));
	border-top: none;
}

:deep([data-theme="dark"]) .expanded-content,
:deep(.v-theme--dark) .expanded-content {
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.01) 0%, rgba(255, 255, 255, 0.03) 100%);
	box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.1);
	border: 1px solid rgba(255, 255, 255, 0.08);
}

@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(-15px);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}

/* Action panel styling */
.action-panel {
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding: 16px;
	margin-bottom: 20px;
	background: linear-gradient(135deg, var(--surface-secondary) 0%, var(--surface-tertiary) 100%);
	border-radius: var(--border-radius-lg);
	border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
	transition: all 0.3s ease;
}

:deep([data-theme="dark"]) .action-panel,
:deep(.v-theme--dark) .action-panel {
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.06) 100%);
	border: 1px solid rgba(255, 255, 255, 0.12);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.action-panel-header {
	display: flex;
	align-items: center;
	padding-bottom: 8px;
	border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.06));
}

:deep([data-theme="dark"]) .action-panel-header,
:deep(.v-theme--dark) .action-panel-header {
	border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.action-panel-icon {
	margin-right: 8px;
	color: var(--primary-color, #1976d2);
}

.action-panel-title {
	font-weight: 600;
	font-size: 0.9rem;
	color: var(--text-primary);
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

.action-panel-content {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 12px;
	flex-wrap: wrap;
}

.action-button-group {
	display: flex;
	gap: 8px;
}

/* Item action buttons styling */
.item-action-btn {
	min-width: 32px !important; /* smaller width */
	height: 32px !important; /* smaller height */
	border-radius: 8px !important; /* slightly smaller curve */
	transition: all 0.2s ease;
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08) !important;
	position: relative;
	overflow: hidden;
	display: flex;
	align-items: center;
	padding: 0 8px !important; /* smaller padding */
	font-size: 0.8rem !important; /* smaller text */
	font-weight: 500;
}

.item-action-btn .action-label {
	display: none !important;
}

@media (min-width: 600px) {
	.item-action-btn .action-label {
		display: inline-block;
	}

	.item-action-btn {
		min-width: px !important;
	}
}

.item-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 5px 12px rgba(0, 0, 0, 0.15) !important;
}

.item-action-btn .v-icon {
	font-size: 22px !important;
	position: relative;
	z-index: 2;
}

/* Light theme button styles with enhanced gradients */
.item-action-btn.delete-btn {
	background: linear-gradient(145deg, #ffebee, #ffcdd2) !important;
}

.item-action-btn.delete-btn:hover {
	background: linear-gradient(145deg, #ffcdd2, #ef9a9a) !important;
}

.item-action-btn.minus-btn {
	background: linear-gradient(145deg, #fff8e1, #ffecb3) !important;
}

.item-action-btn.minus-btn:hover {
	background: linear-gradient(145deg, #ffecb3, #ffe082) !important;
}

.item-action-btn.plus-btn {
	background: linear-gradient(145deg, #e8f5e9, #c8e6c9) !important;
}

.item-action-btn.plus-btn:hover {
	background: linear-gradient(145deg, #c8e6c9, #a5d6a7) !important;
}

/* Dark theme button styles */
:deep([data-theme="dark"]) .item-action-btn.delete-btn,
:deep(.v-theme--dark) .item-action-btn.delete-btn {
	background: linear-gradient(145deg, #4a1515, #3a1010) !important;
	color: #ff8a80 !important;
}

:deep([data-theme="dark"]) .item-action-btn.delete-btn:hover,
:deep(.v-theme--dark) .item-action-btn.delete-btn:hover {
	background: linear-gradient(145deg, #5a1a1a, #4a1515) !important;
}

:deep([data-theme="dark"]) .item-action-btn.minus-btn,
:deep(.v-theme--dark) .item-action-btn.minus-btn {
	background: linear-gradient(145deg, #4a3c10, #3a2e0c) !important;
	color: #ffe082 !important;
}

:deep([data-theme="dark"]) .item-action-btn.minus-btn:hover,
:deep(.v-theme--dark) .item-action-btn.minus-btn:hover {
	background: linear-gradient(145deg, #5a4a14, #4a3c10) !important;
}

:deep([data-theme="dark"]) .item-action-btn.plus-btn,
:deep(.v-theme--dark) .item-action-btn.plus-btn {
	background: linear-gradient(145deg, #1b4620, #133419) !important;
	color: #a5d6a7 !important;
}

:deep([data-theme="dark"]) .item-action-btn.plus-btn:hover,
:deep(.v-theme--dark) .item-action-btn.plus-btn:hover {
	background: linear-gradient(145deg, #235828, #1b4620) !important;
}

:deep([data-theme="dark"]) .item-action-btn .v-icon,
:deep(.v-theme--dark) .item-action-btn .v-icon {
	opacity: 0.9;
}

/* Form layout styling */
.item-details-form {
	margin-top: 16px;
}

.form-row {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	margin-bottom: 8px;
}

.form-field {
	flex: 1;
	min-width: 200px;
}

.form-field.full-width {
	flex-basis: 100%;
}

.form-section {
	margin-top: 12px;
	padding: 10px;
	background: var(--surface-secondary);
	border-radius: var(--border-radius-lg);
	border: 1px solid var(--border-color, rgba(0, 0, 0, 0.06));
	box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
	transition: all 0.3s ease;
}

.form-section:hover {
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
	transform: translateY(-1px);
}

:deep([data-theme="dark"]) .form-section,
:deep(.v-theme--dark) .form-section {
	background: rgba(255, 255, 255, 0.02);
	border: 1px solid rgba(255, 255, 255, 0.08);
	box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

:deep([data-theme="dark"]) .form-section:hover,
:deep(.v-theme--dark) .form-section:hover {
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.section-header {
	display: flex;
	align-items: center;
	margin-bottom: 8px;
	padding-bottom: 8px;
	border-bottom: 2px solid var(--primary-color, #1976d2);
	position: relative;
}

.section-header::after {
	content: "";
	position: absolute;
	bottom: -2px;
	left: 0;
	width: 40px;
	height: 2px;
	background: linear-gradient(90deg, var(--primary-color, #1976d2), transparent);
}

.section-icon {
	margin-right: 10px;
	color: var(--primary-color, #1976d2);
	background: rgba(25, 118, 210, 0.1);
	padding: 6px;
	border-radius: 8px;
}

:deep([data-theme="dark"]) .section-icon,
:deep(.v-theme--dark) .section-icon {
	background: rgba(144, 202, 249, 0.1);
}

.section-title {
	font-weight: 600;
	font-size: 0.85rem;
	color: var(--text-primary);
	text-transform: uppercase;
	letter-spacing: 0.5px;
}

@media (max-width: 600px) {
	.form-section {
		margin-top: 8px;
		padding: 8px;
	}

	.form-row {
		gap: 6px;
		margin-bottom: 6px;
	}

	.section-header {
		margin-bottom: 6px;
		padding-bottom: 6px;
	}

	.form-field {
		min-width: 140px;
	}

	.section-title {
		font-size: 0.8rem;
	}
}

/* Change price button styling */
.change-price-btn {
	margin-top: 8px;
	border-radius: 8px !important;
	text-transform: none !important;
	font-weight: 500 !important;
	transition: all 0.3s ease !important;
}

.change-price-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}

/* Enhanced form field styling */
.form-field :deep(.v-field) {
	border-radius: 8px !important;
	transition: all 0.3s ease !important;
}

.form-field :deep(.v-field:hover) {
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.form-field :deep(.v-field--focused) {
	box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
}

/* Currency and amount display with enhanced Arabic number support */
.currency-display {
	display: flex;
	align-items: center;
	justify-content: flex;
}
.action-buttons {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 6px;
}

.currency-symbol {
	opacity: 0.7;
	margin-right: 2px;
	font-size: 0.85em;
	font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.amount-value {
	font-weight: 500;
	text-align: left;
	/* Enhanced Arabic number font stack for maximum clarity */
	font-family:
		"SF Pro Display", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans Arabic", "Tahoma",
		sans-serif;
	/* Force lining numbers for consistent height and alignment */
	font-variant-numeric: lining-nums tabular-nums;
	/* Additional OpenType features for better Arabic number rendering */
	font-feature-settings:
		"tnum" 1,
		"lnum" 1,
		"kern" 1;
	/* Ensure crisp rendering */
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
	/* Better number spacing */
	letter-spacing: 0.02em;
}

/* Center the actions vertically + horizontally inside the actions column cell */
.actions-cell {
	display: flex;
	align-items: center;
	justify-content: center; /* center horizontally */
	height: 100%;
	padding: 6px 0;
}

/* inner center wrapper to control spacing */
.actions-center {
	display: flex;
	gap: 8px;
	align-items: center;
	justify-content: center;
}

/* Unified action button look */
.action-btn {
	width: 38px !important; /* square for circular look */
	height: 38px !important;
	min-width: 38px !important;
	padding: 0 !important;
	border-radius: 10px !important; /* slightly rounded */
	display: inline-flex !important;
	align-items: center;
	justify-content: center;
	box-shadow: 0 6px 14px rgba(16, 24, 40, 0.06);
	transition:
		transform 0.12s ease,
		box-shadow 0.12s ease;
}

/* Icon size inside the button */
.action-btn .v-icon {
	font-size: 18px !important;
}

/* Colors: delete, minus, plus */
.action-delete {
	background: linear-gradient(180deg, #fff5f5, #ffecec) !important;
	color: #b71c1c !important;
	border: 1px solid rgba(183, 28, 28, 0.08) !important;
}

.action-minus {
	background: linear-gradient(180deg, #fffaf0, #fff2db) !important;
	color: #ef6c00 !important;
	border: 1px solid rgba(239, 108, 0, 0.08) !important;
}

.action-plus {
	background: linear-gradient(180deg, #f2fff4, #e6f6e9) !important;
	color: #1b5e20 !important;
	border: 1px solid rgba(27, 94, 32, 0.08) !important;
}

/* Hover & focus */
.action-btn:hover:not(:disabled),
.action-btn:focus-visible {
	transform: translateY(-3px);
	box-shadow: 0 10px 20px rgba(16, 24, 40, 0.12);
	outline: none;
}

/* Disabled state */
.action-btn:disabled {
	opacity: 0.45 !important;
	transform: none !important;
	box-shadow: none !important;
	cursor: not-allowed;
}

/* Make column header alignment consistent (optional; keeps header centered over buttons) */
.modern-items-table :deep(th) {
	/* existing rules remain — make sure actions header is centered */
	text-align: center;
}

/* On small screens reduce gaps but keep tappable sizes */
@media (max-width: 600px) {
	.actions-center {
		gap: 6px;
	}
	.action-btn {
		width: 44px !important;
		height: 44px !important;
		min-width: 44px !important;
	}
}

/* Enhanced negative number styling for Arabic context */
.negative-number {
	color: #d32f2f !important;
	font-weight: 600;
	/* Same enhanced font stack for negative numbers */
	font-family:
		"SF Pro Display", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans Arabic", "Tahoma",
		sans-serif;
	font-variant-numeric: lining-nums tabular-nums;
	font-feature-settings:
		"tnum" 1,
		"lnum" 1,
		"kern" 1;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
}

/* Enhanced form fields for Arabic number input */
.form-field :deep(.v-field) input,
.form-field :deep(.v-field) textarea {
	/* Enhanced Arabic number font stack for input fields */
	font-family:
		"SF Pro Display", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans Arabic", "Tahoma",
		sans-serif;
	font-variant-numeric: lining-nums tabular-nums;
	font-feature-settings:
		"tnum" 1,
		"lnum" 1,
		"kern" 1;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
	letter-spacing: 0.01em;
}

/* Qty control: minus - qty - plus (centered) */
.qty-control {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	padding: 2px 4px;
	height: 100%;
	/* ensure it doesn't push layout */
	box-sizing: border-box;
}

/* Buttons around qty */
.qty-btn {
	width: 34px !important;
	height: 34px !important;
	min-width: 34px !important;
	padding: 0 !important;
	border-radius: 8px !important;
	display: inline-flex !important;
	align-items: center;
	justify-content: center;
	box-shadow: 0 6px 14px rgba(16, 24, 40, 0.06);
	transition:
		transform 0.12s ease,
		box-shadow 0.12s ease;
}

/* Slight color hints (non-invasive) */
.qty-decrease {
	background: linear-gradient(180deg, #fff8f8, #fff0f0) !important;
	color: #d32f2f !important;
	border: 1px solid rgba(211, 47, 47, 0.06) !important;
}
.qty-decrease:disabled {
	opacity: 0.5 !important;
}

.qty-increase {
	background: linear-gradient(180deg, #f5fffa, #ecfff2) !important;
	color: #1b7029 !important;
	border: 1px solid rgba(27, 112, 41, 0.06) !important;
}
.qty-increase:disabled {
	opacity: 0.5 !important;
}

/* Icon size */
.qty-btn .v-icon {
	font-size: 18px !important;
}

/* Qty numeric display */
.qty-value {
	min-width: 48px;
	text-align: center;
	font-weight: 600;
	padding: 2px 6px;
	border-radius: 6px;
	background: transparent;
	font-variant-numeric: lining-nums tabular-nums;
}

/* Negative number styling (inherits your .negative-number rules) */
.qty-control.negative-number .qty-value {
	color: #d32f2f;
}

/* Hover/focus affordance */
.qty-btn:hover:not(:disabled),
.qty-btn:focus-visible {
	transform: translateY(-2px);
	box-shadow: 0 10px 20px rgba(16, 24, 40, 0.12);
	outline: none;
}

/* Ensure header alignment for the qty column stays centered */
.modern-items-table :deep(th) {
	/* keep your existing rules; these won't override them badly
     but ensure center alignment for qty header as well */
	text-align: center;
}

/* Responsive tweaks - keep tap targets comfortable */
@media (max-width: 600px) {
	.qty-btn {
		width: 44px !important;
		height: 44px !important;
		min-width: 44px !important;
	}
	.qty-value {
		min-width: 56px;
		font-size: 0.95rem;
	}
}

/* Enhanced Arabic support for all numeric displays in the table */
.modern-items-table :deep(td),
.modern-items-table :deep(th) {
	font-family:
		"SF Pro Display", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans Arabic", "Tahoma",
		sans-serif;
	font-variant-numeric: lining-nums tabular-nums;
	font-feature-settings:
		"tnum" 1,
		"lnum" 1,
		"kern" 1;
	-webkit-font-smoothing: antialiased;
	-moz-osx-font-smoothing: grayscale;
}

/* center header label text for all columns */
.modern-items-table :deep(thead tr th .v-data-table-header__content) {
	display: flex;
	justify-content: center;
	align-items: center;
	text-align: center;
}

/* Drag and drop styles */
.draggable-row {
	transition: all 0.2s ease;
	cursor: move;
}

.draggable-row:hover {
	background-color: rgba(0, 0, 0, 0.02);
}

:deep([data-theme="dark"]) .draggable-row:hover,
:deep(.v-theme--dark) .draggable-row:hover {
	background-color: rgba(255, 255, 255, 0.05);
}

.drag-handle-cell {
	width: 40px;
	text-align: center;
	padding: 8px 4px;
}

.drag-handle {
	cursor: grab;
	opacity: 0.6;
	transition: opacity 0.2s ease;
}

.drag-handle:hover {
	opacity: 1;
}

.drag-handle:active {
	cursor: grabbing;
}

.drag-source {
	opacity: 0.5;
	background-color: rgba(25, 118, 210, 0.1) !important;
}

.drag-over {
	background-color: rgba(25, 118, 210, 0.2) !important;
	border-top: 2px solid #1976d2;
	transform: translateY(-1px);
}

.drag-active .draggable-row:not(.drag-source):not(.drag-over) {
	opacity: 0.7;
}

/* Dark theme drag styles */
:deep([data-theme="dark"]) .drag-source,
:deep(.v-theme--dark) .drag-source {
	background-color: rgba(144, 202, 249, 0.1) !important;
}

:deep([data-theme="dark"]) .drag-over,
:deep(.v-theme--dark) .drag-over {
	background-color: rgba(144, 202, 249, 0.2) !important;
	border-top: 2px solid #90caf9;
}

/* Expanded row styling */
.expanded-row {
	background-color: var(--surface-secondary);
}
</style>
