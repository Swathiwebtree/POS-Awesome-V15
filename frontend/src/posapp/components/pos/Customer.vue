<template>
	<div class="customer-vehicle-row" style="display: flex; gap: 12px; align-items: flex-start">
		<div style="flex: 1 1 0">
			<!-- VEHICLE INPUT -->

			<v-autocomplete
				ref="vehicleDropdown"
				class="vehicle-autocomplete sleek-field"
				density="compact"
				variant="solo"
				clearable
				:loading="loadingVehicles"
				:items="vehicleItems"
				item-title="vehicle_no"
				item-value="name"
				:label="__('Vehicle No')"
				v-model="selectedVehicle"
				v-model:search="vehicleSearchText"
				:no-filter="true"
				:custom-filter="vehicleFilter"
				hide-details
				@update:menu="onVehicleMenuToggle"
				@update:search="onVehicleSearch"
				@update:modelValue="onVehicleSelect"
				@keydown.enter="handleVehicleEnter"
				:menu-props="{ maxWidth: '80vw' }"
			>
				<template #selection="{ item }">
					<span>
						{{ item?.raw?.vehicle_no || item?.raw?.name || "" }}
					</span>
				</template>

				<template #item="{ props, item }">
					<!-- `props` already contains title/subtitle used by v-list-item; avoid rendering twice -->
					<v-list-item
						v-bind="props"
						:title="item?.raw?.vehicle_no || item?.raw?.name || ''"
						:subtitle="''"
					/>
				</template>

				<template #prepend-inner>
					<v-tooltip text="Edit vehicle">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="edit_vehicle"
								>mdi-car-wrench</v-icon
							>
						</template>
					</v-tooltip>
				</template>

				<template #append-inner>
					<v-progress-circular
						v-if="loadingVehicles"
						indeterminate
						size="20"
						width="2"
						color="primary"
					/>

					<v-tooltip v-else text="Add new vehicle">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="new_vehicle"
								>mdi-plus</v-icon
							>
						</template>
					</v-tooltip>
				</template>
			</v-autocomplete>
		</div>

		<div style="flex: 1 1 0">
			<Skeleton v-if="loadingCustomers" height="58" class="w-100" />
			<v-autocomplete
				v-else
				ref="customerDropdown"
				class="customer-autocomplete sleek-field"
				density="compact"
				clearable
				variant="solo"
				color="#4169E1"
				:label="frappe._('Customer / Mobile No')"
				v-model="internalCustomer"
				:items="filteredCustomers"
				:item-title="getCustomerDisplayName"
				item-value="name"
				:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
				:no-data-text="
					isCustomerBackgroundLoading && !customers.length
						? __('Loading customer data...')
						: __('Customers not found')
				"
				hide-details
				:customFilter="() => true"
				:disabled="effectiveReadonly || loadingCustomers"
				:menu-props="{ closeOnContentClick: false, maxWidth: '80vw' }"
				:loading="customerSearchLoading"
				@update:menu="onCustomerMenuToggle"
				@update:modelValue="onCustomerChange"
				@update:search="onCustomerSearch"
				@click:clear="onCustomerExplicitClear"
				@keydown.enter="handleEnter"
				:virtual-scroll="true"
				:virtual-scroll-item-height="58"
			>
				<template #prepend-inner>
					<v-tooltip text="Edit customer">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="edit_customer"
								>mdi-account-edit</v-icon
							>
						</template>
					</v-tooltip>
				</template>

				<template #append-inner>
					<v-tooltip text="Add new customer">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="new_customer"
								>mdi-plus</v-icon
							>
						</template>
					</v-tooltip>
				</template>

				<template #item="{ props, item }">
					<v-list-item
						v-bind="props"
						:title="item.raw.custom_display_name || item.raw.customer_name || item.raw.name"
						:subtitle="''"
					>
						<v-list-item-subtitle v-if="item.raw.name">
							<div>ID: {{ item.raw.name }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.mobile_no">
							<div>Mobile: {{ item.raw.mobile_no }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.tax_id">
							<div>TAX ID: {{ item.raw.tax_id }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.email_id">
							<div>Email: {{ item.raw.email_id }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.primary_address">
							<div>Primary Address: {{ item.raw.primary_address }}</div>
						</v-list-item-subtitle>
					</v-list-item>
				</template>
			</v-autocomplete>
		</div>

		<!-- <div class="mt-4">
                        <UpdateCustomer />
                        <UpdateVehicle />
                </div> -->
	</div>
</template>

<style scoped>
.customer-vehicle-row {
	align-items: flex-start;
}

.customer-autocomplete,
.vehicle-autocomplete,
.v-text-field {
	height: 48px;
	box-sizing: border-box;
	border-radius: 10px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
	transition: box-shadow 0.3s ease;
	background-color: #fff;
}

/* .customer-autocomplete:hover,
.vehicle-autocomplete:hover,
.v-text-field:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
} */

/* Dark mode styling for all inputs */
:deep([data-theme="dark"]) .customer-autocomplete,
:deep(.v-theme--dark) .customer-autocomplete,
:deep([data-theme="dark"]) .vehicle-autocomplete,
:deep(.v-theme--dark) .vehicle-autocomplete,
:deep([data-theme="dark"]) .v-text-field,
:deep(.v-theme--dark) .v-text-field {
	background-color: #1e1e1e !important;
}

:deep([data-theme="dark"]) .v-field__input,
:deep(.v-theme--dark) .v-field__input,
:deep([data-theme="dark"]) input,
:deep(.v-theme--dark) input,
:deep([data-theme="dark"]) .v-label,
:deep(.v-theme--dark) .v-label {
	color: #fff !important;
}

.icon-button {
	cursor: pointer;
	font-size: 22px;
	opacity: 0.7;
	transition: all 0.2s ease;
	color: #000000;
}

.icon-button:hover {
	opacity: 1;
	color: var(--v-theme-primary);
}

:deep(.vehicle-autocomplete .v-field__prepend-inner),
:deep(.customer-autocomplete .v-field__prepend-inner),
:deep(.vehicle-autocomplete .v-field__append-inner),
:deep(.customer-autocomplete .v-field__append-inner) {
	position: relative;
	z-index: 30;
	pointer-events: auto !important;
}

:deep(.vehicle-autocomplete .v-field__prepend-inner .icon-button),
:deep(.customer-autocomplete .v-field__prepend-inner .icon-button),
:deep(.vehicle-autocomplete .v-field__append-inner .icon-button),
:deep(.customer-autocomplete .v-field__append-inner .icon-button) {
	pointer-events: auto !important;
}

:deep(.vehicle-autocomplete .v-field__input),
:deep(.customer-autocomplete .v-field__input) {
	position: relative;
	z-index: 1;
}

/* Input background */
.vehicle-autocomplete .v-field,
.customer-autocomplete .v-field {
	background-color: #ffffff !important;
	border: 1.5px solid #b8c1cc !important;
}

/* Reduce overlay wash so border stays visible */
:deep(.vehicle-autocomplete .v-field__overlay),
:deep(.customer-autocomplete .v-field__overlay) {
	opacity: 0.02 !important;
}

/* Stronger border on hover */
:deep(.vehicle-autocomplete .v-field:hover),
:deep(.customer-autocomplete .v-field:hover) {
	border-color: #080808 !important;
}

/* Clear focused border ring */
:deep(.vehicle-autocomplete .v-field.v-field--focused),
:deep(.customer-autocomplete .v-field.v-field--focused) {
	border-color: #080808 !important;
}

/* Dark theme border visibility */
:deep(.v-theme--dark .vehicle-autocomplete .v-field),
:deep(.v-theme--dark .customer-autocomplete .v-field) {
	border-color: #080808 !important;
}

:deep(.v-theme--dark .vehicle-autocomplete .v-field:hover),
:deep(.v-theme--dark .customer-autocomplete .v-field:hover) {
	border-color: #080808 !important;
}

:deep(.v-theme--dark .vehicle-autocomplete .v-field.v-field--focused),
:deep(.v-theme--dark .customer-autocomplete .v-field.v-field--focused) {
	border-color: #080808 !important;
}

/* Input text */
.v-field__input input {
	color: #1f2937 !important; /* dark gray */
	font-weight: 500;
	font-size: 13px;
}

/* Placeholder */
.v-field__input input::placeholder {
	color: #6b7280; /* medium gray */
	opacity: 1;
	font-size: 12px;
}

:deep(.vehicle-autocomplete .v-field__input),
:deep(.customer-autocomplete .v-field__input),
:deep(.vehicle-autocomplete .v-field__input input),
:deep(.customer-autocomplete .v-field__input input) {
	min-height: 32px;
}

:deep(.vehicle-autocomplete .v-label),
:deep(.customer-autocomplete .v-label) {
	font-size: 12px;
}
.v-card,
.job-orders,
.search-items {
	background: #ffffff;
	border: 1px solid #e5e7eb;
}
header,
.app-header {
	color: #111827;
}

header .v-icon {
	color: #374151;
	opacity: 1;
}
.v-field--focused {
	border-color: #080808 !important;
}
/*  Fix disabled autocomplete background + opacity */
:deep(.v-input--disabled) {
	opacity: 1 !important; /* remove faded look */
}

:deep(.v-input--disabled .v-field) {
	background-color: #ffffff !important;
}

:deep(.v-input--disabled .v-field__input),
:deep(.v-input--disabled input),
:deep(.v-input--disabled .v-label) {
	color: #1f2937 !important;
}

/*height for vehicle & customer fields */
:deep(.vehicle-autocomplete .v-field),
:deep(.customer-autocomplete .v-field) {
	min-height: 50px !important;
	height: 50px !important;
	align-items: stretch !important;
}

/* Keep label and selected value separated (prevent overlap) */
:deep(.vehicle-autocomplete .v-field__input),
:deep(.customer-autocomplete .v-field__input) {
	min-height: 50px !important;
	padding-top: 18px !important;
	padding-bottom: 6px !important;
}

:deep(.vehicle-autocomplete .v-label.v-field-label),
:deep(.customer-autocomplete .v-label.v-field-label) {
	top: 12px !important;
}

:deep(.vehicle-autocomplete .v-label.v-field-label--floating),
:deep(.customer-autocomplete .v-label.v-field-label--floating) {
	transform: translateY(-9px) scale(0.75) !important;
}

/* Empty state: keep label centered when nothing is selected */
:deep(.customer-autocomplete .v-field:not(.v-field--dirty):not(.v-field--focused) .v-field__input) {
	padding-top: 0 !important;
	padding-bottom: 0 !important;
}

:deep(.customer-autocomplete .v-field:not(.v-field--dirty):not(.v-field--focused) .v-label.v-field-label) {
	top: 50% !important;
	transform: translateY(-50%) !important;
}

:deep(.vehicle-autocomplete .v-field:not(.v-field--dirty):not(.v-field--focused) .v-field__input) {
	padding-top: 0 !important;
	padding-bottom: 0 !important;
}

:deep(.vehicle-autocomplete .v-field:not(.v-field--dirty):not(.v-field--focused) .v-label.v-field-label) {
	top: 50% !important;
	transform: translateY(-50%) !important;
}

/* Final override: keep border clearly visible even before click/focus */
:deep(.customer-autocomplete .v-field),
:deep(.vehicle-autocomplete .v-field) {
	border: 1px solid #121416 !important;
	background-color: #fff !important;
}

:deep(.customer-autocomplete .v-field__overlay),
:deep(.vehicle-autocomplete .v-field__overlay) {
	opacity: 0 !important;
}

:deep(.customer-autocomplete .v-field.v-field--focused),
:deep(.vehicle-autocomplete .v-field.v-field--focused) {
	border-color: #121416 !important;
}
</style>

<script>
/* global frappe __ */
import Skeleton from "../ui/Skeleton.vue";
import {
	db,
	checkDbHealth,
	setCustomerStorage,
	memoryInitPromise,
	getCustomersLastSync,
	setCustomersLastSync,
	getCustomerStorageCount,
	clearCustomerStorage,
	isOffline,
} from "../../../offline/index.js";
import _ from "lodash";

export default {
	props: {
		pos_profile: Object,
	},

	data: () => ({
		pos_profile: "",
		customers: [],
		customer: "",
		internalCustomer: null,
		tempSelectedCustomer: null,
		isMenuOpen: false,
		readonly: false,
		effectiveReadonly: false,
		customer_info: {},
		loadingCustomers: false,
		customerSearchLoading: false,
		customers_loaded: false,
		searchTerm: "",
		page: 0,
		pageSize: 100,
		hasMore: true,
		nextCustomerStart: null,
		searchDebounce: null,
		isCustomerBackgroundLoading: false,
		pendingCustomerSearch: null,
		loadProgress: 0,
		totalCustomerCount: 0,
		loadedCustomerCount: 0,
		_skipNextCustomerSearch: false,
		// Vehicle data
		vehicles: [],
		selectedVehicle: null,
		vehicle_no: "",
		vehicleSearchText: "",
		loadingVehicles: false,
		selected_customer_is_corporate: false,

		// vehicle search state
		vehicleSearchTerm: "",
		vehiclePage: 0,
		vehicleSearchResults: [],
		vehicleHasMore: false,
		vehicleFetchInFlight: false,
		lastVehicleFetchKey: "",
		lastVehicleFetchAt: 0,
		latestVehicleSearchRequestId: 0,
		activeVehicleSearchRequestId: 0,
		latestCustomerSearchRequestId: 0,
		activeCustomerSearchRequestId: 0,
		jobOrderVehicleNo: null,
		jobOrderCustomer: null,
		pendingDraftVehicleNo: null,
		jobOrderLoading: false,
		jobOrderLockUntil: 0,

		// invoice doc placeholder used in some methods (should be provided by parent normally)
		invoice_doc: {},

		// Guard to prevent duplicate load_invoice_customer event processing
		_lastLoadInvoiceCustomerPayload: null,
		_loadInvoiceCustomerInProgress: false,
		ignoreCustomerClearUntil: 0,
		allowCustomerClear: false,
		resetSearchOnCustomerMenuOpen: false,
	}),

	components: {
		Skeleton,
	},

	computed: {
		isDarkTheme() {
			return this.$theme.current === "dark";
		},

		filteredCustomers() {
			return this.customers;
		},
		vehicleItems() {
			// Always show the full customer vehicle list in the dropdown.
			if (this.vehicles.length) return this.vehicles;

			return [];
		},
	},

	watch: {
		readonly(val) {
			this.effectiveReadonly = val && navigator.onLine;
		},
		customers_loaded(val) {
			if (val) {
				this.eventBus.emit("customers_loaded");
			}
		},
	},

	methods: {
		hasVehicleStore() {
			return Array.isArray(db?.tables) && db.tables.some((table) => table?.name === "vehicles");
		},

		sanitizeVehicleNo(val) {
			if (!val) return "";
			return String(val)
				.replace(/[^A-Za-z0-9-]/g, "")
				.slice(0, 8);
		},
		vehicleFilter() {
			return true;
		},
		async loadAllVehicles() {
			this.loadingVehicles = true;
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.get_all_vehicles",
					args: { limit: 500 },
				});

				this.vehicles = this._dedupeVehicleRows(res.message || []);
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.vehicleSearchText = "";

				console.log("[Vehicle] Loaded all vehicles:", this.vehicles.length);
			} catch (err) {
				console.error("Failed to load all vehicles", err);
				this.vehicles = [];
			} finally {
				this.loadingVehicles = false;
			}
		},

		onVehicleMenuToggle(isOpen) {
			if (isOpen) {
				// If no customer is selected, show "all vehicles" list for the dropdown.
				// This is fetched lazily on menu open to avoid loading on every page load.
				if (
					!this.customer &&
					!this.vehicleSearchTerm &&
					!this.loadingVehicles &&
					(!this.vehicles || !this.vehicles.length)
				) {
					this.loadAllVehicles();
				}

				this.$nextTick(() => {
					const dropdown = this.$refs.vehicleDropdown?.$el?.querySelector(
						".v-overlay__content .v-select-list",
					);
					if (dropdown) {
						dropdown.scrollTop = 0;
					}
				});
			}
		},
		getCustomerDisplayName(item) {
			if (!item) return "";
			const row = item.raw || item;
			return row.custom_display_name || row.customer_name || row.name || "";
		},
		// --- Helper to normalize customer rows --
		_normalizeCustomerRow(r) {
			// Ensure we always have is_corporate boolean present in each customer row
			if (!r) return r;
			// Accept either is_corporate or is_company from server/local storage
			const isCorporate = !!(r.is_corporate || r.is_company);
			const customerName = r.customer_name || r.name || "";
			const customDisplayName = r.custom_display_name || customerName || r.name || "";
			return {
				...r,
				customer_name: customerName,
				custom_display_name: customDisplayName,
				is_corporate: isCorporate,
				is_company: r.is_company || isCorporate,
			};
		},
		_normalizeVehicleRow(r) {
			if (!r) return r;
			return {
				...r,
				name: String(r.name || "").trim(),
				vehicle_no: String(r.vehicle_no || "").trim(),
				customer: String(r.customer || "").trim(),
				customer_name: String(r.customer_name || r.customer || "").trim(),
				custom_display_name: String(
					r.custom_display_name || r.customer_name || r.customer || "",
				).trim(),
				mobile_no: r.mobile_no || "",
			};
		},
		_dedupeVehicleRows(rows = []) {
			const seen = new Set();
			return (rows || [])
				.map((r) => this._normalizeVehicleRow(r))
				.filter((r) => {
					if (!r) return false;
					const key = `${String(r.name || "").toLowerCase()}::${String(
						r.vehicle_no || "",
					).toLowerCase()}`;
					if (!key.trim() || seen.has(key)) return false;
					seen.add(key);
					return true;
				});
		},
		clearVehicleSearchText() {
			this.vehicleSearchText = "";
			this.vehicleSearchTerm = "";
			this.vehicleSearchResults = [];
		},

		_upsertCustomerInList(customerId, customerDisplayName = "", extra = {}) {
			const id = (customerId || "").toString().trim();
			if (!id) return null;

			const displayName = (customerDisplayName || "").toString().trim() || id;
			const idx = this.customers.findIndex((c) => c.name === id);
			const customerName = (extra.customer_name || "").toString().trim() || id;

			if (idx === -1) {
				const inserted = this._normalizeCustomerRow({
					name: id,
					customer_name: customerName,
					custom_display_name: displayName,
					mobile_no: extra.mobile_no || "",
					email_id: extra.email_id || "",
					tax_id: extra.tax_id || "",
					vehicle_no: extra.vehicle_no || "",
					is_corporate: !!(extra.is_corporate || extra.is_company),
				});
				this.customers.unshift(inserted);
				return inserted;
			}

			const existing = this.customers[idx] || {};
			const resolvedCustomerName =
				(extra.customer_name || existing.customer_name || existing.name || id).toString().trim() ||
				id;
			const resolvedDisplayName =
				(
					extra.custom_display_name ||
					existing.custom_display_name ||
					displayName ||
					resolvedCustomerName ||
					id
				)
					.toString()
					.trim() || resolvedCustomerName;

			const merged = this._normalizeCustomerRow({
				...existing,
				customer_name: resolvedCustomerName,
				custom_display_name: resolvedDisplayName,
				mobile_no: existing.mobile_no || extra.mobile_no || "",
				email_id: existing.email_id || extra.email_id || "",
				tax_id: existing.tax_id || extra.tax_id || "",
				vehicle_no: existing.vehicle_no || extra.vehicle_no || "",
				is_corporate:
					existing.is_corporate !== undefined
						? !!existing.is_corporate
						: !!(extra.is_corporate || extra.is_company),
			});

			this.customers.splice(idx, 1, merged);
			return merged;
		},
		normalizeCustomerValue(value) {
			if (value && typeof value === "object") {
				const candidate = value.name || value.customer || value.customer_name || "";
				return String(candidate || "").trim();
			}
			return String(value || "").trim();
		},
		_resolveCustomerIdFromInput(val) {
			const input = String(val || "").trim();
			if (!input) return input;

			// If it's already a known Customer.name, keep it.
			if ((this.customers || []).some((c) => c && c.name === input)) {
				return input;
			}

			// If user typed a display value (customer_name/custom_display_name), map it back to Customer.name when unique.
			const needle = input.toLowerCase();
			const matches = (this.customers || []).filter((c) => {
				if (!c) return false;
				const byCustomerName =
					String(c.customer_name || "")
						.trim()
						.toLowerCase() === needle;
				const byDisplayName =
					String(c.custom_display_name || "")
						.trim()
						.toLowerCase() === needle;
				return byCustomerName || byDisplayName;
			});

			if (matches.length === 1) {
				return matches[0].name;
			}

			return input;
		},
		_findCustomerMatchFromInput(val) {
			const input = String(val || "")
				.trim()
				.toLowerCase();
			if (!input) return null;

			const candidates = this.customers || [];

			const exactMatch = candidates.find((c) => {
				if (!c) return false;
				return [c.name, c.customer_name, c.custom_display_name, c.mobile_no].some(
					(field) =>
						String(field || "")
							.trim()
							.toLowerCase() === input,
				);
			});
			if (exactMatch) return exactMatch;

			const partialMatches = candidates.filter((c) => {
				if (!c) return false;
				return [c.custom_display_name, c.customer_name, c.name, c.mobile_no].some((field) =>
					String(field || "")
						.trim()
						.toLowerCase()
						.includes(input),
				);
			});

			if (partialMatches.length === 1) {
				return partialMatches[0];
			}

			if (!partialMatches.length) {
				return null;
			}

			return (
				partialMatches.find((c) =>
					String(c.name || "")
						.trim()
						.toLowerCase()
						.startsWith(input),
				) || partialMatches[0]
			);
		},
		cancelPendingCustomerSearch() {
			if (this.searchDebounce && this.searchDebounce.cancel) {
				this.searchDebounce.cancel();
			}
			this._skipNextCustomerSearch = true;
		},
		releasePendingCustomerSearch(delay = 600) {
			setTimeout(() => {
				this._skipNextCustomerSearch = false;
			}, delay);
		},
		applyProgrammaticCustomerSelection(customer, extra = {}) {
			const customerName = this.normalizeCustomerValue(customer);
			if (!customerName) return;

			this.cancelPendingCustomerSearch();
			this._upsertCustomerInList(
				customerName,
				extra.custom_display_name || extra.customer_name || customerName,
				{
					customer_name: extra.customer_name || customerName,
					custom_display_name: extra.custom_display_name || extra.customer_name || customerName,
					mobile_no: extra.mobile_no || "",
					email_id: extra.email_id || "",
					tax_id: extra.tax_id || "",
					vehicle_no: extra.vehicle_no || "",
					is_corporate: !!(extra.is_corporate || extra.is_company),
				},
			);

			this.customer = customerName;
			this.internalCustomer = customerName;
			this.allowCustomerClear = false;
			this.ignoreCustomerClearUntil = Date.now() + 1500;
			this.releasePendingCustomerSearch();
			return customerName;
		},
		onCustomerExplicitClear() {
			this.allowCustomerClear = true;
		},

		// --- Customer Methods ---
		onCustomerMenuToggle(isOpen) {
			this.isMenuOpen = isOpen;
			if (isOpen) {
				// Keep current selection visible when opening dropdown.
				// Clearing model here causes the selected customer text to disappear.
				this.internalCustomer = this.customer || this.internalCustomer || null;
				this.resetSearchOnCustomerMenuOpen = true;
				// Always show full customer list on dropdown open (even when a customer is selected).
				if (this.searchDebounce && this.searchDebounce.cancel) {
					this.searchDebounce.cancel();
				}
				this.searchTerm = "";
				this.page = 0;
				this.hasMore = true;
				this.searchCustomers("");
				this.$nextTick(() => {
					setTimeout(() => {
						const dropdown = this.$refs.customerDropdown?.$el?.querySelector(
							".v-overlay__content .v-select-list",
						);
						if (dropdown) {
							dropdown.scrollTop = 0;
							dropdown.addEventListener("scroll", this.onCustomerScroll);
						}
					}, 50);
				});
			} else {
				this.resetSearchOnCustomerMenuOpen = false;
				const dropdown = this.$refs.customerDropdown?.$el?.querySelector(
					".v-overlay__content .v-select-list",
				);
				if (dropdown) {
					dropdown.removeEventListener("scroll", this.onCustomerScroll);
				}
				if (this.tempSelectedCustomer) {
					const selected = this.normalizeCustomerValue(this.tempSelectedCustomer);
					this.internalCustomer = selected;
					this.customer = selected;
					this.eventBus.emit("update_customer", this.customer);
					if (!(this.jobOrderCustomer && this.jobOrderVehicleNo)) {
						this.fetchVehiclesForCustomer(this.customer);
					}
				} else if (this.customer) {
					this.internalCustomer = this.customer;
				}
				this.tempSelectedCustomer = null;
			}
		},

		onCustomerScroll(e) {
			const el = e.target;
			if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
				this.loadMoreCustomers();
			}
		},

		async fetchAndEmitCustomerDetails(customerName, opts = {}) {
			if (!customerName) {
				return;
			}

			try {
				const { preferVehicleNo = null } = opts;
				let customerNameString = customerName;

				if (typeof customerName === "object" && customerName !== null) {
					customerNameString =
						customerName.customer || customerName.customer_name || customerName.name;
				}

				customerNameString = String(customerNameString).trim();
				if (!customerNameString) return;

				// ✅ CHANGE THIS LINE - Use extracted string instead of object
				const response = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_info",
					args: {
						customer: customerNameString, // ✅ NOW it's always just a string!
					},
				});

				if (response && response.message) {
					const customerData = response.message;
					this.customer_info = customerData || {};

					const mobile = customerData.mobile_no || "";
					const vehicleNo = preferVehicleNo ? String(preferVehicleNo).trim() : "";

					const isCorporate = !!(customerData.is_corporate || customerData.is_company);
					this.selected_customer_is_corporate = isCorporate;
					this._upsertCustomerInList(
						customerData.name || customerNameString,
						customerData.custom_display_name || customerData.customer_name || customerNameString,
						{
							customer_name: customerData.customer_name || customerNameString,
							custom_display_name:
								customerData.custom_display_name ||
								customerData.customer_name ||
								customerNameString,
							mobile_no: mobile,
							email_id: customerData.email_id || "",
							tax_id: customerData.tax_id || "",
							vehicle_no: vehicleNo || "",
							is_corporate: isCorporate,
						},
					);

					this.eventBus.emit("update_customer_details", {
						...(mobile ? { contact_mobile: mobile } : {}),
						...(vehicleNo ? { custom_vehicle_no: vehicleNo } : {}),
						...(customerData.mobile_no ||
						customerData.tel_mobile ||
						customerData.contact_mobile ||
						""
							? {
									vehicle_mobile_no:
										customerData.mobile_no ||
										customerData.tel_mobile ||
										customerData.contact_mobile ||
										"",
								}
							: {}),
						...(customerData.custom_vehicle_make || customerData.make
							? {
									custom_vehicle_make:
										customerData.custom_vehicle_make || customerData.make || "",
								}
							: {}),
						...(customerData.custom_vehicle_model || customerData.model
							? {
									custom_vehicle_model:
										customerData.custom_vehicle_model || customerData.model || "",
								}
							: {}),
						is_corporate: isCorporate,
					});
				}
			} catch (error) {
				console.error("[Customer] Failed to fetch customer details:", error);
			}
		},

		onCustomerChange(val) {
			val = this.normalizeCustomerValue(val);
			val = this._resolveCustomerIdFromInput(val);
			// When loading from a draft, internalCustomer is set programmatically
			// which may trigger this. Skip to avoid showing false "already selected" error.
			if (this._skipNextCustomerSearch) {
				return;
			}
			if (val && this.jobOrderCustomer && val !== this.jobOrderCustomer) {
				this.jobOrderCustomer = null;
				this.jobOrderVehicleNo = null;
				this.jobOrderLoading = false;
				this.jobOrderLockUntil = 0;
			}
			if (this.jobOrderLoading && val && val === this.jobOrderCustomer) {
				this.customer = val;
				this.internalCustomer = val;
				this.eventBus.emit("update_customer", val);
				return;
			}
			if (val && val === this.customer) {
				this.internalCustomer = this.customer;
				this.eventBus.emit("show_message", {
					title: __("Customer already selected"),
					color: "error",
				});
				return;
			}

			this.tempSelectedCustomer = val;

			if (!this.isMenuOpen && val) {
				if (val !== this.customer) {
					this.selectedVehicle = null;
					this.vehicle_no = "";
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", null);
					this.eventBus.emit("clear_vehicle_discounts");
					this.eventBus.emit("update_customer_details", {
						contact_mobile: "",
						custom_vehicle_no: "",
						custom_vehicle_make: "",
						custom_vehicle_model: "",
						vehicle_mobile_no: "",
						is_corporate: !!this.selected_customer_is_corporate,
					});
				}
				this.customer = val;
				this.internalCustomer = val;
				this.eventBus.emit("update_customer", val);
				this.fetchAndEmitCustomerDetails(val);
				if (!(this.jobOrderCustomer && this.jobOrderVehicleNo)) {
					this.fetchVehiclesForCustomer(val);
				}
			}

			if (!val) {
				if (this.customer && !this.allowCustomerClear) {
					this.internalCustomer = this.customer;
					return;
				}
				if (
					this.customer &&
					!this.allowCustomerClear &&
					Date.now() < (this.ignoreCustomerClearUntil || 0)
				) {
					this.internalCustomer = this.customer;
					return;
				}
				this.allowCustomerClear = false;
				this.customer = null;
				this.internalCustomer = null;
				this.vehicles = [];
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.jobOrderCustomer = null;
				this.jobOrderVehicleNo = null;
				this.jobOrderLoading = false;
				this.jobOrderLockUntil = 0;
				this.eventBus.emit("update_customer", null);
				this.eventBus.emit("vehicle_selected", null);
				this.eventBus.emit("update_customer_details", {
					contact_mobile: "",
					custom_vehicle_no: "",
					custom_vehicle_make: "",
					custom_vehicle_model: "",
					vehicle_mobile_no: "",
					is_corporate: false,
				});
				this.selected_customer_is_corporate = false;

				// EMIT EMPTY CUSTOMER DETAILS
				this.eventBus.emit("clear_vehicle_discounts");
			}
		},

		onCustomerSearch(val) {
			// Skip search when loading from a draft to prevent the debounced
			// search from clearing this.customers[] and blanking the autocomplete
			if (this._skipNextCustomerSearch) {
				return;
			}

			// First search event on menu open may contain selected value;
			// reset it so dropdown shows full customer list.
			if (this.isMenuOpen && this.resetSearchOnCustomerMenuOpen) {
				this.resetSearchOnCustomerMenuOpen = false;
				const selected = (this.customers || []).find((c) => c && c.name === this.customer) || {};
				const current = String(val || "")
					.trim()
					.toLowerCase();
				const selectedTokens = [
					String(this.customer || "")
						.trim()
						.toLowerCase(),
					String(selected.customer_name || "")
						.trim()
						.toLowerCase(),
					String(selected.custom_display_name || "")
						.trim()
						.toLowerCase(),
				].filter(Boolean);
				if (!current || selectedTokens.includes(current)) {
					this.searchDebounce("");
					return;
				}
			}
			this.searchDebounce(val);
		},

		handleEnter(event) {
			event?.preventDefault?.();
			event?.stopPropagation?.();

			const inputText = event?.target?.value || this.searchTerm || this.internalCustomer || "";
			const matched = this._findCustomerMatchFromInput(inputText);

			if (matched) {
				this.tempSelectedCustomer = matched.name;
				this.applyProgrammaticCustomerSelection(matched.name, matched);
				this.eventBus.emit("update_customer", matched.name);
				this.fetchAndEmitCustomerDetails(matched.name);
				this.fetchVehiclesForCustomer(matched.name);
				this.selectedVehicle = null;
				this.isMenuOpen = false;
				event?.target?.blur?.();
			}
		},

		async searchVehiclesByNumber(term, append = false) {
			try {
				await checkDbHealth();
				if (!db.isOpen()) await db.open();

				if (term && this.vehicleSearchTerm !== term) {
					this.vehiclePage = 0;
				}

				let results = [];

				if (term) {
					const q = term.toString().toLowerCase();

					// Load all local vehicles and filter
					const all = this.hasVehicleStore() ? await db.table("vehicles").toArray() : [];

					const filtered = all.filter((v) => {
						try {
							return (
								(v.vehicle_no && v.vehicle_no.toString().toLowerCase().includes(q)) ||
								(v.make && v.make.toString().toLowerCase().includes(q)) ||
								(v.model && v.model.toString().toLowerCase().includes(q)) ||
								(v.customer_name && v.customer_name.toString().toLowerCase().includes(q))
							);
						} catch {
							return false;
						}
					});

					// Server fallback for vehicle search
					let serverResults = [];
					if ((!filtered || filtered.length === 0) && term) {
						try {
							const resp = await frappe.call({
								method: "posawesome.posawesome.api.customers.get_vehicles_by_search",
								args: {
									search_term: term,
									limit: this.pageSize || 50,
									customer: this.customer || null,
								},
							});
							if (resp && resp.message && resp.message.length) {
								serverResults = (resp.message || []).map((v) => ({
									name: v.name,
									vehicle_no: v.vehicle_no,
									make: v.make || "",
									model: v.model || "",
									customer: v.customer || "",
									customer_name: v.customer_name || "",
									custom_display_name:
										v.custom_display_name || v.customer_name || v.customer || "",
									mobile_no: v.mobile_no || "",
									odometer: v.odometer || 0,
								}));
							}
						} catch (err) {
							console.error("Server vehicle search failed:", err);
						}
					}

					// Choose data source
					let slice = [];
					if (serverResults && serverResults.length) {
						slice = serverResults;
					} else {
						const startIndex = (this.vehiclePage || 0) * this.pageSize;
						slice = filtered.slice(startIndex, startIndex + this.pageSize);
					}

					results = slice.map((r) => ({
						name: r.name,
						vehicle_no: r.vehicle_no,
						make: r.make || "",
						model: r.model || "",
						customer: r.customer || "",
						customer_name: r.customer_name || "",
						custom_display_name: r.custom_display_name || r.customer_name || r.customer || "",
						mobile_no: r.mobile_no || "",
						odometer: r.odometer || 0,
					}));
				}

				if (append) {
					this.vehicleSearchResults.push(...results);
				} else {
					this.vehicleSearchResults = results;
				}

				this.vehicleHasMore = results.length === this.pageSize;
				if (this.vehicleHasMore) {
					this.vehiclePage = (this.vehiclePage || 0) + 1;
				}

				return results.length;
			} catch (e) {
				console.error("Failed to search vehicles", e);
				return 0;
			}
		},

		onVehicleSearch: _.debounce(async function (val) {
			const cleaned = this.sanitizeVehicleNo(val);
			const term = (cleaned || "").trim().toLowerCase();
			this.vehicleSearchTerm = term;
			this.latestVehicleSearchRequestId += 1;
			const requestId = this.latestVehicleSearchRequestId;
			this.activeVehicleSearchRequestId = requestId;

			if (!term || term.length < 2) {
				this.vehicleSearchResults = [];
				this.loadingVehicles = false;
				return;
			}

			this.loadingVehicles = true;

			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_vehicles_by_search",
					args: {
						search_term: term,
						customer: this.customer || null,
						limit: 20,
					},
				});

				if (requestId !== this.activeVehicleSearchRequestId) return;
				this.vehicleSearchResults = [];

				this.vehicleSearchResults = (res.message || []).map((v) => ({
					name: v.name,
					vehicle_no: v.vehicle_no,
					customer: v.customer,
					customer_name: v.customer_name || "",
					custom_display_name: v.custom_display_name || v.customer_name || v.customer || "",
					mobile_no: v.mobile_no || "",
				}));
			} catch (e) {
				if (requestId !== this.activeVehicleSearchRequestId) return;
				console.error("Vehicle search failed", e);
				this.vehicleSearchResults = [];
			} finally {
				if (requestId === this.activeVehicleSearchRequestId) {
					this.loadingVehicles = false;
				}
			}
		}, 300),

		async onVehicleNoEnter() {
			const vehicleNo = this.sanitizeVehicleNo(this.vehicle_no);
			this.vehicle_no = vehicleNo;
			if (!vehicleNo) return;

			this.loadingVehicles = true;
			try {
				let customerName = null;
				let customerDisplayName = "";
				let customerMobileNo = "";
				let vehicleData = null;

				// 1. Local Lookup
				try {
					await checkDbHealth();
					if (!db.isOpen()) await db.open();
					const local = this.hasVehicleStore()
						? await db.table("vehicles").where("vehicle_no").equals(vehicleNo).first()
						: null;
					if (local) {
						customerName = local.customer;
						customerDisplayName = local.custom_display_name || local.customer_name || "";
						customerMobileNo = local.mobile_no || "";
						vehicleData = {
							name: local.name,
							vehicle_no: local.vehicle_no,
							make: local.make || "",
							model: local.model || "",
							customer_name: local.customer_name,
							custom_display_name:
								local.custom_display_name || local.customer_name || local.customer,
						};
					}
				} catch (e) {
					console.warn("Local vehicle lookup error", e);
				}

				// 2. Server Lookup if no local match or online
				if (!customerName && navigator.onLine) {
					const res = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_vehicles_by_search",
						args: { search_term: vehicleNo, customer: this.customer || null },
					});
					const payload = res?.message || {};
					if (payload.customer && payload.customer.name) {
						customerName = payload.customer.name;
						customerDisplayName = payload.customer.customer_name || customerDisplayName;
						customerMobileNo = payload.customer.mobile_no || customerMobileNo;
					}
					if (payload.vehicle) {
						vehicleData = payload.vehicle;
					}
				}

				// Final update logic
				if (customerName) {
					this._upsertCustomerInList(
						customerName,
						customerDisplayName ||
							vehicleData?.custom_display_name ||
							vehicleData?.customer_name ||
							customerName,
						{
							customer_name: vehicleData?.customer_name || customerName,
							custom_display_name:
								customerDisplayName ||
								vehicleData?.custom_display_name ||
								vehicleData?.customer_name ||
								customerName,
							mobile_no: customerMobileNo || vehicleData?.mobile_no || "",
							vehicle_no: vehicleData?.vehicle_no || vehicleNo,
						},
					);

					this.customer = customerName;
					this.internalCustomer = customerName;
					this.eventBus.emit("update_customer", customerName);

					if (vehicleData) {
						this.selectedVehicle = vehicleData.name;
						this.eventBus.emit("vehicle_selected", vehicleData.name);
						this.eventBus.emit(
							"set_custom_vehicle_no",
							vehicleData.vehicle_no || vehicleNo || "",
						);
						await this.fetchVehiclesForCustomer(customerName);

						// Highlight the selected vehicle
						const existingVehicle = this.vehicles.find((v) => v.name === vehicleData.name);
						if (existingVehicle) {
							this.selectedVehicle = vehicleData.name;
						}

						this.eventBus.emit("apply_vehicle_discount", {
							customer: customerName,
							vehicle_no: vehicleData.vehicle_no,
						});
					} else {
						this.selectedVehicle = null;
						this.eventBus.emit("vehicle_selected", null);
						this.eventBus.emit("set_custom_vehicle_no", "");
					}

					// ensure we fetch and emit the corporate flag as well
					await this.fetchAndEmitCustomerDetails(customerName, {
						preferVehicleNo: vehicleData?.vehicle_no || vehicleNo,
					});
				} else {
					frappe.show_alert({
						message: __("No customer found for vehicle: " + vehicleNo),
						indicator: "red",
					});
					this.selectedVehicle = null;
					this.eventBus.emit("vehicle_selected", null);
					this.eventBus.emit("set_custom_vehicle_no", "");
				}
			} catch (err) {
				console.error("Failed to lookup customer by vehicle:", err);
				frappe.show_alert({
					message: __("Error looking up vehicle"),
					indicator: "red",
				});
			} finally {
				this.loadingVehicles = false;
			}
		},

		edit_vehicle() {
			const vehicle_to_edit =
				this.vehicles.find((v) => v.name === this.selectedVehicle) ||
				(this.vehicles.length === 1 && this.vehicles[0].name ? this.vehicles[0] : null);

			if (vehicle_to_edit) {
				this.eventBus.emit("open_update_vehicle", vehicle_to_edit);
			} else {
				frappe.msgprint(__("Please select a vehicle or add one first."), __("Error"));
			}
		},

		new_vehicle() {
			const payload = {
				customer: this.customer,
				vehicle_no: this.vehicles.length === 0 ? this.vehicle_no : null,
			};

			this.eventBus.emit("open_update_vehicle", payload);
		},

		async searchCustomerByMobile(mobile) {
			// normalize
			const mobile_no = (mobile || "").toString().trim();
			if (!mobile_no) {
				this.customerNotFound = false;
				return;
			}

			this.searchingCustomer = true;
			this.customerNotFound = false;

			try {
				frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_by_mobile",
					args: { mobile_no },
					callback: (r) => {
						const msg = r?.message ?? null;
						if (msg) {
							this.invoice_doc.customer = msg.name || msg.customer_name || "";
							this.invoice_doc.customer_name = msg.customer_name || msg.name || "";
							this.invoice_doc.mobile_no = msg.mobile_no || mobile_no;
							this.customerNotFound = false;

							// If the server returned a summary with is_corporate included, use it.
							if (msg.is_corporate !== undefined || msg.is_company !== undefined) {
								const isCorp = !!(msg.is_corporate || msg.is_company);
								this.selected_customer_is_corporate = isCorp;
								this.eventBus.emit("update_customer_details", {
									contact_mobile: msg.mobile_no || "",
									custom_vehicle_no: msg.vehicle_no || "",
									custom_vehicle_make: msg.custom_vehicle_make || msg.make || "",
									custom_vehicle_model: msg.custom_vehicle_model || msg.model || "",
									is_corporate: isCorp,
								});
								// If we only got summary and need full info for vehicles, fetch it
								if (msg.name) {
									this.fetchAndEmitCustomerDetails(msg.name);
								}
							} else if (msg.name) {
								// If server returned only a reference, fetch full details
								this.fetchAndEmitCustomerDetails(msg.name);
							}
						}
						this.searchingCustomer = false;
					},
					error: (err) => {
						console.error("searchCustomerByMobile error:", err);
						this.customerNotFound = true;
						this.searchingCustomer = false;
					},
				});
			} catch (e) {
				console.error(e);
				this.customerNotFound = true;
				this.searchingCustomer = false;
			}
		},

		async searchCustomers(term, append = false) {
			try {
				const trimmedTerm = String(term || "").trim();
				const selectedCustomerName = String(this.customer || "").trim();
				const selectedCustomerSnapshot =
					(this.customers || []).find((c) => c && c.name === selectedCustomerName) || null;
				await checkDbHealth();
				if (!db.isOpen()) await db.open();

				if (term && this.searchTerm !== term) {
					this.page = 0;
				}

				let results = [];

				if (trimmedTerm && trimmedTerm.length < 2) {
					results = [];
				} else if (trimmedTerm) {
					const q = trimmedTerm.toLowerCase();

					// Load the local customer cache first, then merge live server matches.
					const all = await db.table("customers").toArray();

					const filtered = all.filter((c) => {
						try {
							return (
								(c.custom_display_name &&
									c.custom_display_name.toString().toLowerCase().includes(q)) ||
								(c.customer_name && c.customer_name.toString().toLowerCase().includes(q)) ||
								(c.name && c.name.toString().toLowerCase().includes(q)) ||
								(c.mobile_no && c.mobile_no.toString().toLowerCase().includes(q)) ||
								(c.email_id && c.email_id.toString().toLowerCase().includes(q)) ||
								(c.tax_id && c.tax_id.toString().toLowerCase().includes(q)) ||
								(c.vehicle_no && c.vehicle_no.toString().toLowerCase().includes(q))
							);
						} catch (err) {
							return false;
						}
					});

					// Always query the server for typed searches so the POS can search across
					// the full customer dataset without preloading all records.
					let serverResults = [];
					if (trimmedTerm && navigator.onLine) {
						try {
							const resp = await frappe.call({
								method: "posawesome.posawesome.api.customers.search_customers",
								args: {
									search_term: trimmedTerm,
									pos_profile:
										this.pos_profile && this.pos_profile.pos_profile
											? this.pos_profile.pos_profile
											: null,
									limit: this.pageSize || 100,
								},
							});
							if (resp && resp.message && resp.message.length) {
								serverResults = (resp.message || []).map((c) => ({
									name: c.name,
									customer_name: c.customer_name,
									custom_display_name: c.custom_display_name || c.customer_name || c.name,
									mobile_no: c.mobile_no || "",
									email_id: c.email_id || "",
									vehicle_no: c.vehicle_no || "",
									tax_id: c.tax_id || "",
									is_corporate: !!(c.is_corporate || c.is_company),
								}));
							}
						} catch (err) {
							console.error("Server fallback search failed:", err);
						}
					}

					const merged = [];
					const seen = new Set();
					const pushUnique = (row) => {
						const norm = this._normalizeCustomerRow(row);
						const key = String(norm?.name || "")
							.trim()
							.toLowerCase();
						if (!key || seen.has(key)) return;
						seen.add(key);
						merged.push(norm);
					};
					(serverResults || []).forEach(pushUnique);
					(filtered || []).forEach(pushUnique);

					let slice = merged;
					if (!serverResults.length) {
						const startIndex = (this.page || 0) * this.pageSize;
						slice = merged.slice(startIndex, startIndex + this.pageSize);
					}

					// Normalize the shape that the UI expects (and ensure is_corporate exists)
					results = slice.map((r) => {
						const norm = this._normalizeCustomerRow(r);
						return {
							name: norm.name,
							customer_name: norm.customer_name,
							custom_display_name: norm.custom_display_name,
							mobile_no: norm.mobile_no || "",
							email_id: norm.email_id || "",
							vehicle_no: norm.vehicle_no || "",
							tax_id: norm.tax_id || "",
							is_corporate: !!norm.is_corporate,
						};
					});
				} else {
					// No search term — just read the paginated table rows
					const collection = db.table("customers");
					results = await collection
						.offset((this.page || 0) * this.pageSize)
						.limit(this.pageSize)
						.toArray();

					// Normalize any rows from local DB (may not have is_corporate)
					results = (results || []).map((r) => {
						const norm = this._normalizeCustomerRow(r);
						return {
							...norm,
						};
					});
				}

				// assign results to component state (append vs replace)
				if (append) {
					this.customers.push(...results);
				} else {
					this.customers = results;
					// Keep currently selected customer in the list so v-autocomplete
					// does not blank out after background refresh/page reload.
					if (
						selectedCustomerName &&
						!this.customers.some((c) => c && c.name === selectedCustomerName)
					) {
						const fallback = selectedCustomerSnapshot
							? this._normalizeCustomerRow(selectedCustomerSnapshot)
							: this._normalizeCustomerRow({
									name: selectedCustomerName,
									customer_name: selectedCustomerName,
									custom_display_name: selectedCustomerName,
								});
						this.customers.unshift(fallback);
					}
				}

				// set pagination flags
				this.hasMore = results.length === this.pageSize;
				if (this.hasMore) {
					this.page = (this.page || 0) + 1;
				}

				return results.length;
			} catch (e) {
				console.error("Failed to search customers", e);
				return 0;
			}
		},

		async loadMoreCustomers() {
			if (this.loadingCustomers || this.isCustomerBackgroundLoading) return;
			const count = await this.searchCustomers(this.searchTerm, true);
			if (count === this.pageSize) return;
		},

		async backgroundLoadCustomers(startAfter, syncSince) {
			const limit = this.pageSize;
			this.isCustomerBackgroundLoading = true;
			try {
				let cursor = startAfter;
				while (cursor) {
					const rows = await this.fetchCustomerPage(cursor, syncSince, limit);
					// normalize rows before storing
					const normalized = (rows || []).map((r) => ({
						...r,
						is_corporate: !!(r.is_corporate || r.is_company),
					}));
					await setCustomerStorage(normalized);
					this.loadedCustomerCount += rows.length;
					if (this.totalCustomerCount) {
						const progress = Math.min(
							99,
							Math.round((this.loadedCustomerCount / this.totalCustomerCount) * 100),
						);
						this.loadProgress = progress;
						this.eventBus.emit("data-load-progress", { name: "customers", progress });
					}
					if (rows.length === limit) {
						cursor = rows[rows.length - 1]?.name || null;
						this.nextCustomerStart = cursor;
					} else {
						cursor = null;
						this.nextCustomerStart = null;
						setCustomersLastSync(new Date().toISOString());
						this.loadProgress = 100;
						this.eventBus.emit("data-load-progress", { name: "customers", progress: 100 });
						this.eventBus.emit("data-loaded", "customers");
					}
				}
			} catch (err) {
				console.error("Failed to background load customers", err);
			} finally {
				this.isCustomerBackgroundLoading = false;
				if (this.pendingCustomerSearch !== null) {
					this.searchDebounce(this.pendingCustomerSearch);
					if (this.searchDebounce.flush) {
						this.searchDebounce.flush();
					}
					this.pendingCustomerSearch = null;
				}
			}
		},

		async verifyServerCustomerCount() {
			if (isOffline()) return;
			try {
				const localCount = await getCustomerStorageCount();
				const res = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customers_count",
					args: { pos_profile: this.pos_profile.pos_profile },
				});
				const serverCount = res.message || 0;
				if (typeof serverCount === "number") {
					this.totalCustomerCount = serverCount;
					this.loadedCustomerCount = localCount;
					this.loadProgress = serverCount ? Math.round((localCount / serverCount) * 100) : 0;
					this.eventBus.emit("data-load-progress", {
						name: "customers",
						progress: this.loadProgress,
					});
					if (serverCount < localCount) {
						await clearCustomerStorage();
						setCustomersLastSync(null);
						this.customers = [];
						await this.get_customer_names();
					} else {
						await this.searchCustomers(this.searchTerm);
					}
				}
			} catch (err) {
				console.error("Error verifying customer count:", err);
			}
		},

		fetchCustomerPage(startAfter, modifiedAfter, limit) {
			return new Promise((resolve, reject) => {
				frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_names",
					args: {
						pos_profile: this.pos_profile.pos_profile,
						modified_after: modifiedAfter,
						limit,
						start_after: startAfter,
					},
					callback: (r) => resolve(r.message || []),
					error: (err) => {
						console.error("Failed to fetch customers", err);
						reject(err);
					},
				});
			});
		},

		async get_customer_names() {
			const localCount = await getCustomerStorageCount();
			if (localCount > 0) {
				this.customers_loaded = true;
				await this.searchCustomers(this.searchTerm);
				await this.verifyServerCustomerCount();
				return;
			}
			const syncSince = getCustomersLastSync();
			this.loadProgress = 0;
			this.eventBus.emit("data-load-progress", { name: "customers", progress: 0 });
			this.loadingCustomers = true;
			try {
				try {
					const countRes = await frappe.call({
						method: "posawesome.posawesome.api.customers.get_customers_count",
						args: { pos_profile: this.pos_profile.pos_profile },
					});
					this.totalCustomerCount = countRes.message || 0;
				} catch (e) {
					console.error("Failed to fetch customer count", e);
					this.totalCustomerCount = 0;
				}

				const rows = await this.fetchCustomerPage(null, syncSince, this.pageSize);
				// normalize rows before storing them locally
				const normalized = (rows || []).map((r) => ({
					...r,
					is_corporate: !!(r.is_corporate || r.is_company),
				}));
				await setCustomerStorage(normalized);
				this.loadedCustomerCount = rows.length;
				if (this.totalCustomerCount) {
					this.loadProgress = Math.round(
						(this.loadedCustomerCount / this.totalCustomerCount) * 100,
					);
					this.eventBus.emit("data-load-progress", {
						name: "customers",
						progress: this.loadProgress,
					});
				}
				this.nextCustomerStart = null;
				setCustomersLastSync(new Date().toISOString());
				this.loadProgress = 100;
				this.eventBus.emit("data-load-progress", { name: "customers", progress: 100 });
				this.eventBus.emit("data-loaded", "customers");
				this.customers_loaded = true;
			} catch (err) {
				console.error("Failed to fetch customers:", err);
			} finally {
				this.loadingCustomers = false;
				await this.searchCustomers(this.searchTerm);
			}
		},

		new_customer() {
			this.eventBus.emit("open_update_customer", { withVehicle: true });
		},

		async edit_customer() {
			try {
				const cust_name = this.customer || this.internalCustomer || this.tempSelectedCustomer;
				if (!cust_name) {
					frappe.msgprint(__("Please select a customer to edit."), __("Error"));
					return;
				}

				// Get customer details
				const resp = await frappe.call({
					method: "posawesome.posawesome.api.get_customer_info",
					args: { customer: cust_name },
				});

				const payload = resp?.message || null;
				if (!payload) {
					frappe.msgprint(__("Failed to fetch customer details."), __("Error"));
					return;
				}

				// Try to get vehicles for this customer
				let vehicles = [];
				try {
					const vResp = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer",
						args: { customer_name: cust_name },
					});
					vehicles = vResp?.message || [];
					const selectedVehicleRow =
						(this.vehicles || []).find((v) => v.name === this.selectedVehicle) || null;
					const currentVehicleNo = (selectedVehicleRow?.vehicle_no || this.vehicle_no || "").trim();
					if (currentVehicleNo && vehicles.length > 1) {
						const idx = vehicles.findIndex(
							(v) => (v.vehicle_no || "").trim() === currentVehicleNo,
						);
						if (idx > 0) {
							const selectedVehicle = vehicles.splice(idx, 1)[0];
							vehicles.unshift(selectedVehicle);
						}
					}
				} catch (e) {
					console.warn("Failed to fetch vehicles for customer", e);
				}

				payload.vehicles = vehicles;
				const selectedVehicleRow =
					(this.vehicles || []).find((v) => v.name === this.selectedVehicle) || null;
				const preferredVehicleNo = (
					selectedVehicleRow?.vehicle_no ||
					this.vehicle_no ||
					payload.custom_vehicle_no ||
					payload.vehicle_no ||
					""
				).trim();
				if (preferredVehicleNo) {
					payload.custom_vehicle_no = preferredVehicleNo;
					payload.vehicle_no = preferredVehicleNo;
				}

				this.eventBus.emit("open_update_customer", {
					customer: payload,
					withVehicle: true,
				});
			} catch (err) {
				console.error("edit_customer error:", err);
				frappe.msgprint({ message: __("Unable to open edit dialog"), indicator: "red" });
			}
		},

		async submitUpdatedCustomer(customerPayload, vehiclePayload = null) {
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.update_customer_api",
					args: {
						customer: customerPayload,
						vehicle: vehiclePayload,
						pos_profile_doc: this.pos_profile
							? this.pos_profile.pos_profile || this.pos_profile
							: "{}",
					},
				});

				const msg = res?.message || null;
				if (!msg || !msg.customer) {
					frappe.msgprint({ message: __("Failed to update customer"), indicator: "red" });
					return null;
				}

				this.eventBus.emit("add_customer_to_list", { customer: msg.customer, vehicle: msg.vehicle });
				this.eventBus.emit("close_update_customer");
				return msg;
			} catch (err) {
				console.error("submitUpdatedCustomer error:", err);
				frappe.msgprint({ message: __("Error updating customer"), indicator: "red" });
				return null;
			}
		},

		// --- Vehicle Methods ---
		async fetchVehiclesForCustomer(customerName, vehicleNo = null, options = {}) {
			const allowDefaultSelection = options.allowDefaultSelection !== false;
			const preserveExistingSelection = options.preserveExistingSelection !== false;
			console.log("[Vehicle] fetchVehiclesForCustomer", {
				customerName,
				vehicleNo,
				allowDefaultSelection,
				preserveExistingSelection,
				jobOrderCustomer: this.jobOrderCustomer,
				jobOrderVehicleNo: this.jobOrderVehicleNo,
				jobOrderLoading: this.jobOrderLoading,
			});
			if (!customerName) {
				this.vehicles = [];
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.jobOrderVehicleNo = null;
				this.jobOrderCustomer = null;
				this.jobOrderLoading = false;
				this.jobOrderLockUntil = 0;
				this.eventBus.emit("vehicle_selected", null);
				return;
			}

			const now = Date.now();
			if (
				this.jobOrderCustomer === customerName &&
				this.jobOrderLockUntil &&
				now < this.jobOrderLockUntil
			) {
				if (!vehicleNo) {
					console.log("[Vehicle] blocked: jobOrder lock without vehicleNo");
					return;
				}
				if (this.jobOrderVehicleNo && vehicleNo !== this.jobOrderVehicleNo) {
					console.log("[Vehicle] blocked: jobOrder lock vehicleNo mismatch", {
						vehicleNo,
						jobOrderVehicleNo: this.jobOrderVehicleNo,
					});
					return;
				}
			}
			if (this.jobOrderVehicleNo && this.jobOrderCustomer === customerName && !vehicleNo) {
				// Only allow job-order vehicle fetch when a job order is active.
				console.log("[Vehicle] blocked: jobOrder active missing vehicleNo");
				return;
			}
			if (
				this.jobOrderVehicleNo &&
				this.jobOrderCustomer === customerName &&
				vehicleNo &&
				vehicleNo !== this.jobOrderVehicleNo
			) {
				console.log("[Vehicle] blocked: jobOrder active vehicleNo mismatch", {
					vehicleNo,
					jobOrderVehicleNo: this.jobOrderVehicleNo,
				});
				return;
			}

			const fetchKey = `${customerName}::${vehicleNo || ""}`;
			if (this.vehicleFetchInFlight && fetchKey === this.lastVehicleFetchKey) {
				console.log("[Vehicle] skipped: in-flight", { fetchKey });
				return;
			}
			if (fetchKey === this.lastVehicleFetchKey && now - this.lastVehicleFetchAt < 500) {
				console.log("[Vehicle] skipped: debounce", {
					fetchKey,
					ageMs: now - this.lastVehicleFetchAt,
				});
				return;
			}

			this.vehicleFetchInFlight = true;
			this.lastVehicleFetchKey = fetchKey;
			this.lastVehicleFetchAt = now;

			this.loadingVehicles = true;
			try {
				let fetchedVehicles = [];

				// 1. Offline lookup
				try {
					await checkDbHealth();
					if (!db.isOpen()) await db.open();
					const local = this.hasVehicleStore()
						? await db.table("vehicles").where("customer").equals(customerName).toArray()
						: [];
					if (local && local.length) {
						fetchedVehicles = local.map((r) => ({
							name: r.name || r.id,
							vehicle_no: r.vehicle_no,
							model: r.model,
							make: r.make,
							mobile_no: r.mobile_no,
							customer_name: r.customer_name,
							custom_display_name: r.custom_display_name || r.customer_name || r.customer,
							customer: r.customer,
						}));
					}
				} catch (e) {
					console.warn("Local vehicle lookup failed", e);
				}

				// 2. Server lookup if offline lookup failed or if online
				if (!fetchedVehicles.length || navigator.onLine) {
					console.log("[Vehicle] server call", { customerName, vehicleNo });
					const res = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer",
						args: { customer_name: customerName },
					});
					const serverVehicles = res?.message || [];

					const localNames = new Set(fetchedVehicles.map((v) => v.name));
					for (const v of serverVehicles) {
						if (!localNames.has(v.name)) {
							fetchedVehicles.push({
								name: v.name,
								vehicle_no: v.vehicle_no,
								model: v.model,
								make: v.make,
								mobile_no: v.mobile_no,
								customer_name: v.customer_name,
								custom_display_name: v.custom_display_name || v.customer_name || v.customer,
								customer: v.customer,
							});
						}
					}
				}

				this.vehicles = this._dedupeVehicleRows(fetchedVehicles);
				console.log("[Vehicle] fetch complete", {
					customerName,
					vehicleNo,
					count: fetchedVehicles.length,
				});
				const currentSelectedVehicleName = this.selectedVehicle;
				const currentSelectedVehicleNo = this.vehicle_no;
				const requestedVehicleNo = String(vehicleNo || "")
					.trim()
					.toLowerCase();
				const selectedVehicle = currentSelectedVehicleName
					? this.vehicles.find((v) => v.name === currentSelectedVehicleName)
					: null;
				const selectedVehicleByNo = currentSelectedVehicleNo
					? this.vehicles.find(
							(v) =>
								String(v.vehicle_no || "")
									.trim()
									.toLowerCase() ===
								String(currentSelectedVehicleNo || "")
									.trim()
									.toLowerCase(),
						)
					: null;
				const requestedVehicle = requestedVehicleNo
					? this.vehicles.find(
							(v) =>
								String(v.vehicle_no || "")
									.trim()
									.toLowerCase() === requestedVehicleNo,
						)
					: null;
				const selectedVehicleMatchesCustomer =
					!!selectedVehicle &&
					String(selectedVehicle.customer || "").trim() === String(customerName || "").trim();
				const selectedVehicleByNoMatchesCustomer =
					!!selectedVehicleByNo &&
					String(selectedVehicleByNo.customer || "").trim() === String(customerName || "").trim();

				const nextVehicle =
					requestedVehicle ||
					(preserveExistingSelection && selectedVehicleMatchesCustomer ? selectedVehicle : null) ||
					(preserveExistingSelection && selectedVehicleByNoMatchesCustomer
						? selectedVehicleByNo
						: null);

				if (nextVehicle) {
					this.selectedVehicle = nextVehicle.name;
					this.vehicle_no = nextVehicle.vehicle_no || "";
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", nextVehicle.name);
					this.eventBus.emit("update_customer_details", {
						contact_mobile: this.customer_info?.mobile_no || "",
						custom_vehicle_no: this.vehicle_no || "",
						vehicle_mobile_no:
							nextVehicle.mobile_no ||
							nextVehicle.tel_mobile ||
							this.customer_info?.mobile_no ||
							"",
						custom_vehicle_make:
							nextVehicle.custom_vehicle_make ||
							nextVehicle.make ||
							nextVehicle.vehicle_make ||
							"",
						custom_vehicle_model:
							nextVehicle.custom_vehicle_model ||
							nextVehicle.model ||
							nextVehicle.vehicle_model ||
							nextVehicle.model_no ||
							"",
						is_corporate: !!this.selected_customer_is_corporate,
					});
				} else if (allowDefaultSelection && this.vehicles.length === 1 && !currentSelectedVehicleNo) {
					this.selectedVehicle = this.vehicles[0].name;
					this.vehicle_no = this.vehicles[0].vehicle_no;
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", this.selectedVehicle);
					this.eventBus.emit("update_customer_details", {
						contact_mobile: this.customer_info?.mobile_no || "",
						custom_vehicle_no: this.vehicle_no || "",
						vehicle_mobile_no:
							this.vehicles[0].mobile_no ||
							this.vehicles[0].tel_mobile ||
							this.customer_info?.mobile_no ||
							"",
						custom_vehicle_make:
							this.vehicles[0].custom_vehicle_make ||
							this.vehicles[0].make ||
							this.vehicles[0].vehicle_make ||
							"",
						custom_vehicle_model:
							this.vehicles[0].custom_vehicle_model ||
							this.vehicles[0].model ||
							this.vehicles[0].vehicle_model ||
							this.vehicles[0].model_no ||
							"",
						is_corporate: !!this.selected_customer_is_corporate,
					});

					this.eventBus.emit("apply_vehicle_discount", {
						customer: customerName,
						vehicle_no: this.vehicles[0].vehicle_no,
					});
				} else if (!vehicleNo || this.vehicles.length === 0) {
					// Keep an already-selected vehicle when this refresh returns empty.
					// This avoids a stale async response from clearing a valid selection.
					if (preserveExistingSelection && currentSelectedVehicleName && currentSelectedVehicleNo) {
						this.vehicleSearchText = "";
						this.vehicleSearchTerm = "";
						this.vehicleSearchResults = [];
						return;
					}
					this.selectedVehicle = null;
					this.vehicle_no = "";
					this.vehicleSearchText = "";
					this.vehicleSearchTerm = "";
					this.vehicleSearchResults = [];
					this.eventBus.emit("vehicle_selected", null);
					this.eventBus.emit("clear_vehicle_discounts");
				} else {
					this.selectedVehicle = null;
					this.vehicle_no = "";
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", null);
					this.eventBus.emit("clear_vehicle_discounts");
				}
			} catch (err) {
				console.error("Failed to fetch vehicles:", err);
				this.vehicles = [];
			} finally {
				this.loadingVehicles = false;
				this.vehicleFetchInFlight = false;
			}
		},

		onVehicleSelect(val) {
			if (!val) {
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.clearVehicleSearchText();

				this.eventBus.emit("vehicle_selected", null);
				this.eventBus.emit("set_custom_vehicle_no", "");
				this.eventBus.emit("clear_vehicle_discounts");
				return;
			}

			const vehicle = (this.vehicleItems || []).find((v) => v.name === val);
			if (!vehicle) return;

			this.clearVehicleSearchText();
			this.selectedVehicle = val;
			this.vehicle_no = vehicle.vehicle_no || "";
			this.eventBus.emit("set_custom_vehicle_no", this.vehicle_no || "");
			this._upsertCustomerInList(
				vehicle.customer,
				vehicle.custom_display_name || vehicle.customer_name || vehicle.customer,
				{
					customer_name: vehicle.customer_name || vehicle.customer,
					custom_display_name:
						vehicle.custom_display_name || vehicle.customer_name || vehicle.customer,
					mobile_no: vehicle.mobile_no || "",
					vehicle_no: vehicle.vehicle_no || "",
				},
			);

			this.eventBus.emit("vehicle_selected", vehicle.name);
			this.eventBus.emit("update_customer_details", {
				contact_mobile: this.customer_info?.mobile_no || "",
				custom_vehicle_no: vehicle.vehicle_no || "",
				vehicle_mobile_no:
					vehicle.mobile_no || vehicle.tel_mobile || this.customer_info?.mobile_no || "",
				custom_vehicle_make:
					vehicle.custom_vehicle_make || vehicle.make || vehicle.vehicle_make || "",
				custom_vehicle_model:
					vehicle.custom_vehicle_model ||
					vehicle.model ||
					vehicle.vehicle_model ||
					vehicle.model_no ||
					"",
				is_corporate: !!this.selected_customer_is_corporate,
			});

			if (!this.customer) {
				if (vehicle.customer) {
					this.customer = vehicle.customer;
					this.internalCustomer = vehicle.customer;

					this.eventBus.emit("update_customer", vehicle.customer);
					this.fetchAndEmitCustomerDetails(vehicle.customer, {
						preferVehicleNo: vehicle.vehicle_no || "",
					});

					// load vehicles ONLY ONCE after auto-customer set
					this.fetchVehiclesForCustomer(vehicle.customer, vehicle.vehicle_no);
				}
			} else {
				if (vehicle.customer && vehicle.customer !== this.customer) {
					frappe.show_alert({
						message: __("This vehicle belongs to another customer"),
						indicator: "orange",
					});
					return;
				}
			}

			this.eventBus.emit("apply_vehicle_discount", {
				customer: this.customer || vehicle.customer,
				vehicle_no: vehicle.vehicle_no,
			});

			// Keep only selected vehicle visible in the field after selection;
			// do not leave the dropdown list open.
			this.$nextTick(() => {
				this.$refs.vehicleDropdown?.blur?.();
			});
		},

		async handleVehicleEnter(event) {
			event?.preventDefault?.();
			event?.stopPropagation?.();

			const typedVehicleNo = this.sanitizeVehicleNo(event?.target?.value || this.vehicle_no || "");
			if (typedVehicleNo) {
				this.vehicle_no = typedVehicleNo;
			}

			this.clearVehicleSearchText();
			await this.onVehicleNoEnter();
			event?.target?.blur?.();
		},
	},

	created() {
		memoryInitPromise.then(async () => {
			await this.searchCustomers("");
			this.effectiveReadonly = this.readonly && navigator.onLine;
		});

		// Create a debounced handler to prevent duplicate processing of the same load_invoice_customer event
		const debouncedLoadInvoiceCustomer = _.debounce(async (payload) => {
			console.log("[Customer] 🚨 DEBUG load_invoice_customer TRIGGERED =================");
			console.log("[Customer] Input payload:", {
				payload: payload,
				customer: payload?.customer,
				custom_vehicle_no: payload?.custom_vehicle_no,
				contact_mobile: payload?.contact_mobile,
				custom_service_employee: payload?.custom_service_employee,
				timestamp: Date.now(),
				payload_keys: payload ? Object.keys(payload) : [],
			});
			// Guard: If already processing a request, skip duplicate
			if (this._loadInvoiceCustomerInProgress) {
				console.log("[Customer] load_invoice_customer skipped: already in progress");
				return;
			}

			// Guard: Check if this is the same payload as the last one processed
			const payloadKey = JSON.stringify({
				customer: payload?.customer,
				custom_vehicle_no: payload?.custom_vehicle_no,
			});
			if (
				this._lastLoadInvoiceCustomerPayload === payloadKey &&
				(this.customer === payload?.customer || this.internalCustomer === payload?.customer)
			) {
				console.log("[Customer] load_invoice_customer skipped: duplicate payload", payload);
				return;
			}

			this._lastLoadInvoiceCustomerPayload = payloadKey;
			this._loadInvoiceCustomerInProgress = true;

			try {
				console.log("[Customer] load_invoice_customer", payload);
				if (!payload || !payload.customer) {
					this.customer = null;
					this.internalCustomer = null;
					this.selectedVehicle = null;
					return;
				}

				const customerName = this.normalizeCustomerValue(payload.customer);
				if (!customerName) {
					this.customer = null;
					this.internalCustomer = null;
					this.selectedVehicle = null;
					return;
				}
				const requestedVehicleNo = String(
					payload.custom_vehicle_no ||
						payload.vehicle_no ||
						payload.vehicle_number ||
						payload.custom_vehicle_number ||
						this.pendingDraftVehicleNo ||
						"",
				).trim();
				const hasExplicitVehicleField =
					Object.prototype.hasOwnProperty.call(payload, "custom_vehicle_no") ||
					Object.prototype.hasOwnProperty.call(payload, "vehicle_no") ||
					Object.prototype.hasOwnProperty.call(payload, "vehicle_number") ||
					Object.prototype.hasOwnProperty.call(payload, "custom_vehicle_number");
				const jobVehicleNo = requestedVehicleNo || null;
				const hasVehiclePayload = !!requestedVehicleNo;
				const hasMobilePayload = !!String(payload.contact_mobile || "").trim();
				const sameCustomer = this.jobOrderCustomer === customerName || this.customer === customerName;

				if (
					!hasVehiclePayload &&
					!hasMobilePayload &&
					sameCustomer &&
					this.jobOrderVehicleNo &&
					!hasExplicitVehicleField
				) {
					console.log("[Customer] load_invoice_customer skipped: empty payload for same customer", {
						customerName,
						jobOrderVehicleNo: this.jobOrderVehicleNo,
					});
					return;
				}

				if (jobVehicleNo) {
					this.jobOrderCustomer = customerName;
					this.jobOrderVehicleNo = jobVehicleNo;
					this.jobOrderLoading = true;
					this.jobOrderLockUntil = Date.now() + 5000;
				} else {
					this.jobOrderCustomer = null;
					this.jobOrderVehicleNo = null;
					this.jobOrderLoading = false;
					this.jobOrderLockUntil = 0;
				}

				// Prevent the debounced search from firing after we set internalCustomer.
				// When internalCustomer changes, Vuetify's v-autocomplete fires @update:search
				// which triggers searchDebounce. After 500ms, the debounce clears this.customers = []
				// which causes the autocomplete to lose the customer display.
				// Cancel any pending debounce and set a flag to skip the next search trigger.
				this.cancelPendingCustomerSearch();

				// Set customer state
				this.customer = customerName;
				this.internalCustomer = customerName;
				this.vehicleSearchText = "";

				// Emit update_customer so Invoice.vue stays in sync
				this.eventBus.emit("update_customer", customerName);

				// Ensure the customer exists in the autocomplete items list
				// so Vuetify can display it. If not present, inject a temporary entry.
				const existsInList = this.customers.some((c) => c.name === customerName);
				if (!existsInList) {
					this.customers.unshift({
						name: customerName,
						customer_name: payload.customer_name || customerName,
						custom_display_name:
							payload.custom_display_name || payload.customer_name || customerName,
						mobile_no: "",
						email_id: "",
						vehicle_no: "",
						tax_id: "",
						is_corporate: false,
					});
				}

				// Load customer details (mobile, corporate flag, etc.)
				const allowVehicleFallback =
					typeof payload.allow_vehicle_fallback === "boolean"
						? payload.allow_vehicle_fallback
						: !jobVehicleNo && !hasExplicitVehicleField;

				await this.fetchAndEmitCustomerDetails(customerName, {
					preferVehicleNo: jobVehicleNo || "",
					allowVehicleFallback,
				});

				// Load vehicles
				console.log("[Customer] load_invoice_customer vehicles", {
					customerName,
					jobVehicleNo,
				});
				await this.fetchVehiclesForCustomer(customerName, jobVehicleNo, {
					allowDefaultSelection: allowVehicleFallback,
					preserveExistingSelection: allowVehicleFallback,
				});
				this.jobOrderLoading = false;

				// Auto-select vehicle if present in draft
				if (requestedVehicleNo) {
					const normalizedRequestedVehicleNo = requestedVehicleNo.toLowerCase();
					let matchedVehicle = this.vehicles.find(
						(v) =>
							String(v.vehicle_no || "")
								.trim()
								.toLowerCase() === normalizedRequestedVehicleNo,
					);

					if (!matchedVehicle) {
						matchedVehicle = {
							name: `draft-vehicle::${customerName}::${requestedVehicleNo}`,
							vehicle_no: requestedVehicleNo,
							customer: customerName,
							customer_name: payload.customer_name || customerName,
							custom_display_name:
								payload.custom_display_name || payload.customer_name || customerName,
							mobile_no: payload.contact_mobile || "",
						};
						this.vehicles = this._dedupeVehicleRows([matchedVehicle, ...(this.vehicles || [])]);
					}

					this.selectedVehicle = matchedVehicle.name;
					this.vehicle_no = matchedVehicle.vehicle_no || requestedVehicleNo;
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", matchedVehicle.name);
					this.pendingDraftVehicleNo = null;
				} else if (hasExplicitVehicleField) {
					this.selectedVehicle = null;
					this.vehicle_no = "";
					this.vehicleSearchText = "";
					this.pendingDraftVehicleNo = null;
					this.eventBus.emit("vehicle_selected", null);
				}

				// Force Vue to re-render the autocomplete with the loaded customer
				this.$nextTick(() => {
					this.internalCustomer = customerName;
					this.releasePendingCustomerSearch();
				});
			} finally {
				this._loadInvoiceCustomerInProgress = false;
			}
		}, 300);

		this.eventBus.on("load_invoice_customer", (payload) => {
			debouncedLoadInvoiceCustomer(payload);
		});

		this.searchDebounce = _.debounce(async (val) => {
			const normalized = String(val || "").trim();
			this.latestCustomerSearchRequestId += 1;
			const requestId = this.latestCustomerSearchRequestId;
			this.activeCustomerSearchRequestId = requestId;
			this.searchTerm = normalized;
			this.page = 0;
			this.customers = [];
			this.hasMore = true;
			const shouldSearch = this.searchTerm.length === 0 || this.searchTerm.length >= 2;
			if (!shouldSearch) {
				this.customerSearchLoading = false;
				return;
			}

			this.customerSearchLoading = true;
			try {
				await this.searchCustomers(this.searchTerm);
				if (requestId !== this.activeCustomerSearchRequestId) return;
			} finally {
				if (requestId === this.activeCustomerSearchRequestId) {
					this.customerSearchLoading = false;
				}
			}

			// FETCH VEHICLES DIRECTLY WHEN CUSTOMER SEARCH CHANGES
			if (this.searchTerm && this.searchTerm.length >= 2) {
				const matched = this._findCustomerMatchFromInput(this.searchTerm);

				if (matched) {
					this.customer = matched.name;
					this.internalCustomer = matched.name;
					this.eventBus.emit("update_customer", matched.name);
					await this.fetchAndEmitCustomerDetails(matched.name);
					if (!(this.jobOrderCustomer && this.jobOrderVehicleNo)) {
						await this.fetchVehiclesForCustomer(matched.name);
					}
				}
			}
		}, 300);

		// ADD EVENT LISTENERS
		this.eventBus.on("clear_customer", () => {
			this.selectedCustomer = null;
			this.customer = "";
			this.internalCustomer = null;
			this.tempSelectedCustomer = null;
			this.jobOrderCustomer = null;
			this.jobOrderVehicleNo = null;
			this.jobOrderLoading = false;
			this.jobOrderLockUntil = 0;
		});

		this.eventBus.on("clear_vehicle_number", () => {
			this.selectedVehicle = null;
			this.vehicle_no = "";
			this.eventBus.emit("set_custom_vehicle_no", "");
		});

		this.eventBus.on("clear_all_fields", () => {
			this.selectedCustomer = null;
			this.customer = "";
			this.internalCustomer = null;
			this.tempSelectedCustomer = null;
			this.selectedVehicle = null;
			this.vehicle_no = "";
			this.vehicles = [];
			this.eventBus.emit("set_custom_vehicle_no", "");
			this.jobOrderCustomer = null;
			this.jobOrderVehicleNo = null;
			this.jobOrderLoading = false;
			this.jobOrderLockUntil = 0;
		});

		this.effectiveReadonly = this.readonly && navigator.onLine;

		this.$nextTick(() => {
			if (!window._customerListenersRegistered) {
				this.eventBus.on("register_pos_profile", async (pos_profile) => {
					await memoryInitPromise;
					this.pos_profile = pos_profile;
					await this.get_customer_names();
					if (this.customer) {
						const jobVehicleNo =
							this.jobOrderCustomer === this.customer ? this.jobOrderVehicleNo : null;
						this.fetchVehiclesForCustomer(this.customer, jobVehicleNo);
					}
				});

				this.eventBus.on("payments_register_pos_profile", async (pos_profile) => {
					await memoryInitPromise;
					this.pos_profile = pos_profile;
					await this.get_customer_names();
					if (this.customer) {
						const jobVehicleNo =
							this.jobOrderCustomer === this.customer ? this.jobOrderVehicleNo : null;
						this.fetchVehiclesForCustomer(this.customer, jobVehicleNo);
					}
				});

				this.eventBus.on("set_customer", (customer) => {
					const customerName = this.applyProgrammaticCustomerSelection(customer);
					if (!customerName) return;
					if (this.jobOrderCustomer && customerName !== this.jobOrderCustomer) {
						this.jobOrderCustomer = null;
						this.jobOrderVehicleNo = null;
						this.jobOrderLoading = false;
						this.jobOrderLockUntil = 0;
					}
					if (customerName !== this.customer) {
						this.selectedVehicle = null;
						this.vehicle_no = "";
						this.vehicleSearchText = "";
						this.eventBus.emit("vehicle_selected", null);
						this.eventBus.emit("clear_vehicle_discounts");
					}
					// During draft hydration, Invoice.vue/Customer.vue will explicitly decide
					// whether a vehicle should be restored. Do not auto-fetch here or the
					// previous vehicle can be preserved by fetchVehiclesForCustomer().
					if (this._loadInvoiceCustomerInProgress) {
						return;
					}
					if (this.jobOrderCustomer === customerName && this.jobOrderVehicleNo) {
						return;
					}
					this.fetchVehiclesForCustomer(customerName);
				});

				// Handle both customer and vehicle data from UpdateCustomer.vue
				this.eventBus.on("add_customer_to_list", async (data) => {
					const customer = data.customer || data;
					const vehicle = data.vehicle || null;
					const renamedFrom = String(customer.renamed_from || "").trim();

					const isCorporate = !!(customer.is_corporate || customer.is_company);
					const normalized = this._normalizeCustomerRow({
						...customer,
						is_corporate: isCorporate,
					});

					// If backend renamed the Customer ID, remove stale old key immediately.
					if (renamedFrom && renamedFrom !== normalized.name) {
						this.customers = (this.customers || []).filter((c) => c && c.name !== renamedFrom);
						try {
							await db.table("customers").delete(renamedFrom);
						} catch (e) {
							console.warn("Failed to delete renamed customer cache row", e);
						}
						if (this.customer === renamedFrom) this.customer = normalized.name;
						if (this.internalCustomer === renamedFrom) this.internalCustomer = normalized.name;
					}
					const upsertedCustomer = this._upsertCustomerInList(
						normalized.name,
						normalized.custom_display_name || normalized.customer_name || normalized.name,
						normalized,
					);

					// persist latest customer snapshot to local storage
					await setCustomerStorage([upsertedCustomer || normalized]);

					// select the new customer without letting autocomplete search clear it
					this.applyProgrammaticCustomerSelection(normalized.name, upsertedCustomer || normalized);
					this.selected_customer_is_corporate = isCorporate;

					// notify other components
					this.eventBus.emit("update_customer", normalized.name);
					this.eventBus.emit("update_customer_details", {
						contact_mobile: normalized.mobile_no || "",
						custom_vehicle_no: (vehicle && vehicle.vehicle_no) || "",
						vehicle_mobile_no: (vehicle && (vehicle.mobile_no || vehicle.tel_mobile)) || "",
						is_corporate: isCorporate,
					});

					if (vehicle && vehicle.vehicle_no) {
						// Always refresh from source of truth after customer update so
						// Update Vehicle dialog gets latest mobile/make/model values.
						const jobVehicleNo =
							this.jobOrderCustomer === normalized.name ? this.jobOrderVehicleNo : null;
						await this.fetchVehiclesForCustomer(normalized.name, jobVehicleNo);

						const refreshed = (this.vehicles || []).find(
							(v) => (v.vehicle_no || "").trim() === (vehicle.vehicle_no || "").trim(),
						);
						if (refreshed) {
							this.selectedVehicle = refreshed.name;
							this.vehicle_no = refreshed.vehicle_no;
							this.vehicleSearchText = "";
							this.eventBus.emit("vehicle_selected", refreshed.name);
						}
					} else {
						const jobVehicleNo =
							this.jobOrderCustomer === normalized.name ? this.jobOrderVehicleNo : null;
						await this.fetchVehiclesForCustomer(normalized.name, jobVehicleNo);
					}
				});

				this.eventBus.on("set_customer_readonly", (value) => {
					this.readonly = value;
				});

				this.eventBus.on("set_customer_info_to_edit", (data) => {
					this.customer_info = data;
				});

				this.eventBus.on("fetch_customer_details", async () => {
					await this.get_customer_names();
					if (this.customer) {
						this.applyProgrammaticCustomerSelection(this.customer);
					}
				});

				this.eventBus.on("add_vehicle_to_list", async (vehicle) => {
					if (!this.customer) return;

					const jobVehicleNo =
						this.jobOrderCustomer === this.customer ? this.jobOrderVehicleNo : null;
					await this.fetchVehiclesForCustomer(this.customer, jobVehicleNo);

					if (vehicle.customer === this.customer) {
						const refreshed = (this.vehicles || []).find(
							(v) =>
								(v.vehicle_no || "").trim() === (vehicle.vehicle_no || "").trim() ||
								v.name === vehicle.name,
						);
						if (refreshed) {
							this.selectedVehicle = refreshed.name;
							this.vehicle_no = refreshed.vehicle_no;
							this.vehicleSearchText = "";
							this.eventBus.emit("vehicle_selected", refreshed.name);
						} else {
							this.selectedVehicle = vehicle.name;
							this.vehicle_no = vehicle.vehicle_no;
							this.vehicleSearchText = "";
							this.eventBus.emit("vehicle_selected", vehicle.name);
						}
					}
				});

				this.eventBus.on("set_vehicle", (vehicle_name) => {
					this.selectedVehicle = vehicle_name;
					this.vehicleSearchText = "";
					this.onVehicleSelect(vehicle_name);
				});

				this.eventBus.on("set_custom_vehicle_no", (value) => {
					const normalized = this.sanitizeVehicleNo(String(value || "").trim());
					this.pendingDraftVehicleNo = normalized || null;
					if (!normalized || !this.customer) return;

					const q = normalized.toLowerCase();
					let matchedVehicle = (this.vehicles || []).find(
						(v) =>
							String(v.vehicle_no || "")
								.trim()
								.toLowerCase() === q,
					);

					if (!matchedVehicle) {
						const currentCustomer = this.customers.find((c) => c.name === this.customer) || {};
						matchedVehicle = {
							name: `draft-vehicle::${this.customer}::${normalized}`,
							vehicle_no: normalized,
							customer: this.customer,
							customer_name: currentCustomer.customer_name || this.customer,
							custom_display_name:
								currentCustomer.custom_display_name ||
								currentCustomer.customer_name ||
								this.customer,
							mobile_no: "",
						};
						this.vehicles = this._dedupeVehicleRows([matchedVehicle, ...(this.vehicles || [])]);
					}

					this.selectedVehicle = matchedVehicle.name;
					this.vehicle_no = matchedVehicle.vehicle_no || normalized;
					this.vehicleSearchText = "";
					this.eventBus.emit("vehicle_selected", matchedVehicle.name);
				});

				this.eventBus.on("set_customer_from_vehicle", (customer) => {
					if (customer && customer.name) {
						this._upsertCustomerInList(
							customer.name,
							customer.custom_display_name || customer.customer_name || customer.name,
							{
								customer_name: customer.customer_name || customer.name,
								custom_display_name:
									customer.custom_display_name || customer.customer_name || customer.name,
								mobile_no: customer.mobile_no || "",
								email_id: customer.email_id || "",
								tax_id: customer.tax_id || "",
							},
						);
						this.customer = customer.name;
						this.internalCustomer = customer.name;
						this.eventBus.emit("update_customer", customer.name);
						if (!(this.jobOrderCustomer && this.jobOrderVehicleNo)) {
							this.fetchVehiclesForCustomer(customer.name);
						}
					}
				});
				window._customerListenersRegistered = true;
			}
		});
	},
	beforeUnmount() {
		// Clean up event listeners
		this.eventBus.off("clear_customer");
		this.eventBus.off("clear_vehicle_number");
		this.eventBus.off("clear_all_fields");
		this.eventBus.off("load_invoice_customer");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("payments_register_pos_profile");
		this.eventBus.off("set_customer");
		this.eventBus.off("add_customer_to_list");
		this.eventBus.off("set_customer_readonly");
		this.eventBus.off("set_customer_info_to_edit");
		this.eventBus.off("fetch_customer_details");
		this.eventBus.off("add_vehicle_to_list");
		this.eventBus.off("set_vehicle");
		this.eventBus.off("set_custom_vehicle_no");
		this.eventBus.off("set_customer_from_vehicle");
	},
};
</script>
