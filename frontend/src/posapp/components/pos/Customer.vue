<template>
	<div class="customer-vehicle-row" style="display: flex; gap: 12px; align-items: flex-start">
		<div style="flex: 1 1 0">
			<Skeleton v-if="loadingVehicles" height="58" class="w-100" />

			<v-autocomplete
				v-else-if="vehicles.length > 1"
				ref="vehicleDropdown"
				class="vehicle-autocomplete sleek-field"
				density="compact"
				clearable
				variant="solo"
				:label="frappe._('Vehicle No')"
				v-model="selectedVehicle"
				:items="vehicles"
				item-title="vehicle_no"
				item-value="name"
				hide-details
				:disabled="loadingVehicles"
				@update:modelValue="onVehicleSelect"
				@update:search="onVehicleSearch"
				:virtual-scroll="true"
				:virtual-scroll-item-height="58"
			>
				<template #prepend-inner>
					<v-tooltip text="Edit vehicle">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="edit_vehicle"
								>mdi-car-edit</v-icon
							>
						</template>
					</v-tooltip>
				</template>
				<template #append-inner>
					<v-tooltip text="Add vehicle">
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
				<template #item="{ props, item }">
					<v-list-item v-bind="props">
						<v-list-item-title>{{ item.raw.customer_name }}</v-list-item-title>
						<v-list-item-subtitle v-if="item.raw.customer_name !== item.raw.name">
							<div>ID: {{ item.raw.name }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.mobile_no">
							<div>Mobile: {{ item.raw.mobile_no }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.vehicle_no">
							<div>Vehicle: {{ item.raw.vehicle_no }}</div>
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

			<v-text-field
				v-else-if="vehicles.length === 1 && vehicles[0].name"
				readonly
				dense
				variant="solo"
				:label="frappe._('Vehicle No')"
				v-model="vehicle_no"
			>
				<template #prepend-inner>
					<v-tooltip text="Edit vehicle">
						<template #activator="{ props }">
							<v-icon
								v-bind="props"
								class="icon-button"
								@mousedown.prevent.stop
								@click.stop="edit_vehicle"
								>mdi-car-edit</v-icon
							>
						</template>
					</v-tooltip>
				</template>
				<template #append-inner>
					<v-tooltip text="Add vehicle">
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
			</v-text-field>

			<v-text-field
				v-else
				v-model="vehicle_no"
				dense
				variant="solo"
				:label="frappe._('Vehicle No')"
				placeholder="Enter vehicle no and press Enter"
				@keydown.enter.prevent="onVehicleNoEnter"
				hide-details
			>
				<template #append-inner>
					<v-tooltip text="Add vehicle">
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
			</v-text-field>
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
				:label="frappe._('Customer')"
				v-model="internalCustomer"
				:items="filteredCustomers"
				item-title="customer_name"
				item-value="name"
				:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
				:no-data-text="
					isCustomerBackgroundLoading ? __('Loading customer data...') : __('Customers not found')
				"
				hide-details
				:customFilter="() => true"
				:disabled="effectiveReadonly || loadingCustomers"
				:menu-props="{ closeOnContentClick: false }"
				@update:menu="onCustomerMenuToggle"
				@update:modelValue="onCustomerChange"
				@update:search="onCustomerSearch"
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
					<v-list-item v-bind="props">
						<v-list-item-title>{{ item.raw.customer_name }}</v-list-item-title>
						<v-list-item-subtitle v-if="item.raw.customer_name !== item.raw.name">
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
	height: 58px;
	box-sizing: border-box;
	border-radius: 12px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
	transition: box-shadow 0.3s ease;
	background-color: #fff;
}

.customer-autocomplete:hover,
.vehicle-autocomplete:hover,
.v-text-field:hover {
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

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
	font-size: 20px;
	opacity: 0.7;
	transition: all 0.2s ease;
}

.icon-button:hover {
	opacity: 1;
	color: var(--v-theme-primary);
}
</style>

<script>
/* global frappe __ */
// import UpdateCustomer from "./UpdateCustomer.vue";
// import UpdateVehicle from "./UpdateVehicle.vue";
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
		customers_loaded: false,
		searchTerm: "",
		page: 0,
		pageSize: 200,
		hasMore: true,
		nextCustomerStart: null,
		searchDebounce: null,
		isCustomerBackgroundLoading: false,
		pendingCustomerSearch: null,
		loadProgress: 0,
		totalCustomerCount: 0,
		loadedCustomerCount: 0,
		// Vehicle data
		vehicles: [],
		selectedVehicle: null,
		vehicle_no: "",
		loadingVehicles: false,
	}),

	components: {
		// UpdateCustomer,
		// UpdateVehicle,
		Skeleton,
	},

	computed: {
		isDarkTheme() {
			return this.$theme.current === "dark";
		},

		filteredCustomers() {
			return this.isCustomerBackgroundLoading ? [] : this.customers;
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
		// --- Customer Methods ---
		onCustomerMenuToggle(isOpen) {
			this.isMenuOpen = isOpen;
			if (isOpen) {
				this.internalCustomer = null;
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
				const dropdown = this.$refs.customerDropdown?.$el?.querySelector(
					".v-overlay__content .v-select-list",
				);
				if (dropdown) {
					dropdown.removeEventListener("scroll", this.onCustomerScroll);
				}
				if (this.tempSelectedCustomer) {
					this.internalCustomer = this.tempSelectedCustomer;
					this.customer = this.tempSelectedCustomer;
					this.eventBus.emit("update_customer", this.customer);
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

		onCustomerChange(val) {
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
				this.customer = val;
				this.eventBus.emit("update_customer", val);
				this.fetchVehiclesForCustomer(val);
				this.selectedVehicle = null;
			}

			if (!val) {
				this.customer = null;
				this.internalCustomer = null;
				this.vehicles = [];
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.eventBus.emit("update_customer", null);
				this.eventBus.emit("vehicle_selected", null);
			}
		},

		onCustomerSearch(val) {
			if (this.isCustomerBackgroundLoading) {
				this.pendingCustomerSearch = val;
				return;
			}
			this.searchDebounce(val);
		},

		handleEnter(event) {
			const inputText = event.target.value?.toLowerCase() || "";
			const matched = this.customers.find((cust) => {
				return (
					cust.customer_name?.toLowerCase().includes(inputText) ||
					cust.name?.toLowerCase().includes(inputText) ||
					cust.mobile_no?.toLowerCase().includes(inputText)
				);
			});

			if (matched) {
				this.tempSelectedCustomer = matched.name;
				this.internalCustomer = matched.name;
				this.customer = matched.name;
				this.eventBus.emit("update_customer", matched.name);
				this.fetchVehiclesForCustomer(matched.name);
				this.selectedVehicle = null;
				this.isMenuOpen = false;
				event.target.blur();
			}
		},

		async searchVehiclesByNumber(term, append = false) {
		/**
		 * Search vehicles in local IndexedDB first, then server fallback.
		 * Similar to searchCustomers() but for vehicles.
		 */
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
				const all = await db.table("vehicles").toArray();

				const filtered = all.filter((v) => {
					try {
						return (
							(v.vehicle_no && v.vehicle_no.toString().toLowerCase().includes(q)) ||
							(v.make && v.make.toString().toLowerCase().includes(q)) ||
							(v.model && v.model.toString().toLowerCase().includes(q)) ||
							(v.customer_name && v.customer_name.toString().toLowerCase().includes(q))
						);
					} catch (err) {
						return false;
					}
				});

				// Server fallback for vehicle search
				let serverResults = [];
				if ((!filtered || filtered.length === 0) && term) {
					try {
						const resp = await frappe.call({
							method: "posawesome.posawesome.api.vehicles.search_vehicles",
							args: {
								search_term: term,
								limit: this.pageSize || 50,
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

	onVehicleSearch: _.debounce(function (val) {
		/**
		 * Debounced vehicle search - called when user types in vehicle field.
		 * Updates the dropdown list and searches by vehicle number/make/model.
		 */
		this.vehicleSearchTerm = val || "";
		this.vehiclePage = 0;
		this.vehicleSearchResults = [];
		this.vehicleHasMore = true;

		if (val) {
			this.searchVehiclesByNumber(this.vehicleSearchTerm);
		}
	}, 500),

	onVehicleSelect(val) {
		/**
		 * Called when user selects a vehicle from the dropdown.
		 * Updates vehicle info and associated customer if needed.
		 */
		if (!val) {
			this.selectedVehicle = null;
			this.vehicle_no = "";
			this.eventBus.emit("vehicle_selected", null);
			return;
		}

		const vehicle = (this.vehicles || []).find((v) => v.name === val);
		if (vehicle) {
			this.selectedVehicle = val;
			this.vehicle_no = vehicle.vehicle_no || "";
			this.eventBus.emit("vehicle_selected", vehicle.name);

			// Set customer if not already set
			if (!this.customer && vehicle.customer) {
				this.customer = vehicle.customer;
				this.internalCustomer = vehicle.customer;
				this.eventBus.emit("update_customer", vehicle.customer);
			}
		}
	},

	async onVehicleNoEnter() {
		/**
		 * Called when user presses Enter in the vehicle number input field.
		 * Searches for vehicle and auto-loads associated customer.
		 */
		const vehicleNo = (this.vehicle_no || "").trim();
		if (!vehicleNo) return;

		this.loadingVehicles = true;
		try {
			let customerName = null;
			let vehicleData = null;

			// 1. Local Lookup
			try {
				await checkDbHealth();
				if (!db.isOpen()) await db.open();
				const local = await db
					.table("vehicles")
					.where("vehicle_no")
					.equals(vehicleNo)
					.first();
				if (local) {
					customerName = local.customer;
					vehicleData = {
						name: local.name,
						vehicle_no: local.vehicle_no,
						make: local.make || "",
						model: local.model || "",
						customer_name: local.customer_name,
					};
				}
			} catch (e) {
				console.warn("Local vehicle lookup error", e);
			}

			// 2. Server Lookup if no local match or online
			if (!customerName && navigator.onLine) {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.get_vehicles_by_search",
					args: { search_term: vehicleNo },
				});
				const payload = res?.message || {};
				if (payload.customer && payload.customer.name) {
					customerName = payload.customer.name;
				}
				if (payload.vehicle) {
					vehicleData = payload.vehicle;
				}
			}

			// Final update logic
			if (customerName) {
				this.customer = customerName;
				this.internalCustomer = customerName;
				this.eventBus.emit("update_customer", customerName);

				if (vehicleData) {
					this.selectedVehicle = vehicleData.name;
					this.eventBus.emit("vehicle_selected", vehicleData.name);
					await this.fetchVehiclesForCustomer(customerName);

					// Highlight the selected vehicle
					const existingVehicle = this.vehicles.find((v) => v.name === vehicleData.name);
					if (existingVehicle) {
						this.selectedVehicle = vehicleData.name;
					}
				} else {
					this.selectedVehicle = null;
					this.eventBus.emit("vehicle_selected", null);
				}
			} else {
				frappe.show_alert({
					message: __("No customer found for vehicle: " + vehicleNo),
					indicator: "red",
				});
				this.selectedVehicle = null;
				this.eventBus.emit("vehicle_selected", null);
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

		async searchCustomerByMobile(mobile) {
			// normalize
			const mobile_no = (mobile || "").toString().trim();
			if (!mobile_no) {
				this.customerNotFound = false;
				return;
			}

			// show loading UI if you want
			this.searchingCustomer = true;
			this.customerNotFound = false;

			try {
				// frappe.call style (ERPNext frontend)
				frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_by_mobile",
					args: { mobile_no },
					callback: (r) => {
						const msg = r?.message ?? null;
						if (msg) {
							// populate invoice_doc (adapt field names you use)
							this.invoice_doc.customer = msg.name || msg.customer_name || "";
							this.invoice_doc.customer_name = msg.customer_name || msg.name || "";
							this.invoice_doc.mobile_no = msg.mobile_no || mobile_no;
							// clear not-found state
							this.customerNotFound = false;
						} else {
							// nothing returned -> not found
							this.customerNotFound = true;
							// optional: clear any previous customer selection
							this.invoice_doc.customer = null;
							this.invoice_doc.customer_name = null;
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
				await checkDbHealth();
				if (!db.isOpen()) await db.open();

				// If this is a "new" term (user typed new text), and page wasn't reset elsewhere,
				// ensure page starts at 0 for fresh results.
				// (Your searchDebounce already sets this.page = 0, but this is a safety net.)
				if (term && this.searchTerm !== term) {
					this.page = 0;
				}

				let results = [];

				// If there's a search term, do a robust "contains" search in local IndexedDB.
				// If no term, fall back to paginated read of the customers table.
				if (term) {
					const q = term.toString().toLowerCase();

					// Load all local customers (we filter in-memory for reliable substring search).
					// Note: for very large datasets this is slower; we have a server fallback below.
					const all = await db.table("customers").toArray();

					const filtered = all.filter((c) => {
						try {
							return (
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

					// If nothing found locally, call server fallback (server does LIKE '%term%')
					let serverResults = [];
					if ((!filtered || filtered.length === 0) && term) {
						try {
							const resp = await frappe.call({
								method: "posawesome.posawesome.api.customers.search_customers",
								args: {
									search_term: term,
									pos_profile:
										this.pos_profile && this.pos_profile.pos_profile
											? this.pos_profile.pos_profile
											: null,
									limit: this.pageSize || 20,
								},
							});
							if (resp && resp.message && resp.message.length) {
								serverResults = (resp.message || []).map((c) => ({
									name: c.name,
									customer_name: c.customer_name,
									mobile_no: c.mobile_no || "",
									email_id: c.email_id || "",
									vehicle_no: c.vehicle_no || "",
									tax_id: c.tax_id || "",
								}));
							}
						} catch (err) {
							// swallow server error, fallback to local behavior (empty results)
							console.error("Server fallback search failed:", err);
						}
					}

					// Choose data source: prefer server results if present, otherwise use local filtered + pagination
					let slice = [];
					if (serverResults && serverResults.length) {
						// server returned limited results, use those directly
						slice = serverResults;
					} else {
						const startIndex = (this.page || 0) * this.pageSize;
						slice = filtered.slice(startIndex, startIndex + this.pageSize);
					}

					// Normalize the shape that the UI expects
					results = slice.map((r) => ({
						name: r.name,
						customer_name: r.customer_name,
						mobile_no: r.mobile_no || "",
						email_id: r.email_id || "",
						vehicle_no: r.vehicle_no || "",
						tax_id: r.tax_id || "",
					}));
				} else {
					// No search term — just read the paginated table rows
					const collection = db.table("customers");
					results = await collection
						.offset((this.page || 0) * this.pageSize)
						.limit(this.pageSize)
						.toArray();
				}

				// assign results to component state (append vs replace)
				if (append) {
					this.customers.push(...results);
				} else {
					this.customers = results;
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
			if (this.loadingCustomers) return;
			const count = await this.searchCustomers(this.searchTerm, true);
			if (count === this.pageSize) return;
			if (this.nextCustomerStart) {
				await this.backgroundLoadCustomers(this.nextCustomerStart, getCustomersLastSync());
				await this.searchCustomers(this.searchTerm, true);
			}
		},

		async backgroundLoadCustomers(startAfter, syncSince) {
			const limit = this.pageSize;
			this.isCustomerBackgroundLoading = true;
			try {
				let cursor = startAfter;
				while (cursor) {
					const rows = await this.fetchCustomerPage(cursor, syncSince, limit);
					await setCustomerStorage(rows);
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
					if (serverCount > localCount) {
						const syncSince = getCustomersLastSync();
						const rows = await this.fetchCustomerPage(null, syncSince, this.pageSize);
						await setCustomerStorage(rows);
						this.loadedCustomerCount += rows.length;
						if (this.totalCustomerCount) {
							this.loadProgress = Math.round(
								(this.loadedCustomerCount / this.totalCustomerCount) * 100,
							);
							this.eventBus.emit("data-load-progress", {
								name: "customers",
								progress: this.loadProgress,
							});
						}
						const startAfter =
							rows.length === this.pageSize ? rows[rows.length - 1]?.name || null : null;
						if (startAfter) {
							this.backgroundLoadCustomers(startAfter, syncSince);
						} else {
							setCustomersLastSync(new Date().toISOString());
							this.loadProgress = 100;
							this.eventBus.emit("data-load-progress", { name: "customers", progress: 100 });
							this.eventBus.emit("data-loaded", "customers");
						}
						await this.searchCustomers(this.searchTerm);
					} else if (serverCount < localCount) {
						await clearCustomerStorage();
						setCustomersLastSync(null);
						this.customers = [];
						await this.get_customer_names();
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
				await setCustomerStorage(rows);
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
				this.nextCustomerStart =
					rows.length === this.pageSize ? rows[rows.length - 1]?.name || null : null;
				if (this.nextCustomerStart) {
					this.backgroundLoadCustomers(this.nextCustomerStart, syncSince);
				} else {
					setCustomersLastSync(new Date().toISOString());
					this.loadProgress = 100;
					this.eventBus.emit("data-load-progress", { name: "customers", progress: 100 });
					this.eventBus.emit("data-loaded", "customers");
				}
				this.customers_loaded = true;
			} catch (err) {
				console.error("Failed to fetch customers:", err);
			} finally {
				this.loadingCustomers = false;
				await this.searchCustomers(this.searchTerm);
			}
		},

		new_customer() {
			// Ensure UpdateCustomer is ready to handle vehicle data passed back
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

				// Try to get vehicles for this customer (server method used in parent component)
				let vehicles = [];
				try {
					const vResp = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer",
						args: { customer_name: cust_name },
					});
					vehicles = vResp?.message || [];
				} catch (e) {
					// swallow — not critical, we'll still open the dialog
					console.warn("Failed to fetch vehicles for customer", e);
				}

				// Attach vehicles (even if empty) so the dialog can decide to show fields
				payload.vehicles = vehicles;

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
			// Accepts the shape produced by the UpdateCustomer dialog (plain JS objects)
			// Calls backend update endpoint and then emits add_customer_to_list with response.
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.update_customer_api",
					args: {
						customer: customerPayload,
						vehicle: vehiclePayload,
						pos_profile_doc: this.pos_profile ? this.pos_profile.pos_profile || this.pos_profile : "{}",
					},
				});

				const msg = res?.message || null;
				if (!msg || !msg.customer) {
					frappe.msgprint({ message: __("Failed to update customer"), indicator: "red" });
					return null;
				}

				// Update the frontend list via existing listener expectations
				this.eventBus.emit("add_customer_to_list", { customer: msg.customer, vehicle: msg.vehicle });
				// Close the dialog (UpdateCustomer component should react to eventBus or handle itself)
				this.eventBus.emit("close_update_customer");
				return msg;
			} catch (err) {
				console.error("submitUpdatedCustomer error:", err);
				frappe.msgprint({ message: __("Error updating customer"), indicator: "red" });
				return null;
			}
		},

		// --- Vehicle Methods ---
		async fetchVehiclesForCustomer(customerName) {
			if (!customerName) {
				this.vehicles = [];
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.eventBus.emit("vehicle_selected", null);
				return;
			}

			this.loadingVehicles = true;
			try {
				let fetchedVehicles = [];
				this.vehicle_no = "";

				// 1. Offline lookup
				try {
					await checkDbHealth();
					if (!db.isOpen()) await db.open();
					const local = await db.table("vehicles").where("customer").equals(customerName).toArray();
					if (local && local.length) {
						fetchedVehicles = local.map((r) => ({
							name: r.name || r.id,
							vehicle_no: r.vehicle_no,
							model: r.model,
							make: r.make,
							mobile_no: r.mobile_no,
							customer_name: r.customer_name,
							customer: r.customer,
						}));
					}
				} catch (e) {
					console.warn("Local vehicle lookup failed", e);
				}

				// 2. Server lookup if offline lookup failed or if online
				if (!fetchedVehicles.length || navigator.onLine) {
					const res = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer",
						args: { customer_name: customerName },
					});
					const serverVehicles = res?.message || [];

					// Merge/Deduplicate server results with local results
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
								customer: v.customer,
							});
						}
					}
				}

				this.vehicles = fetchedVehicles;
				this.selectedVehicle = null;

				if (this.vehicles.length === 1) {
					// Automatically select the single vehicle
					this.selectedVehicle = this.vehicles[0].name;
					this.eventBus.emit("vehicle_selected", this.selectedVehicle);
					this.vehicle_no = this.vehicles[0].vehicle_no;
				} else if (this.vehicles.length > 1) {
					// Add placeholder only if multiple vehicles exist
					this.vehicles.unshift({ name: null, vehicle_no: frappe._("Select Vehicle...") });
				} else {
					// No vehicles, clear selection
					this.eventBus.emit("vehicle_selected", null);
				}
			} catch (err) {
				console.error("Failed to fetch vehicles:", err);
				this.vehicles = [];
			} finally {
				this.loadingVehicles = false;
			}
		},

		onVehicleSelect(val) {
			if (!val) {
				this.selectedVehicle = null;
				this.vehicle_no = "";
				this.eventBus.emit("vehicle_selected", null);
				return;
			}

			const vehicle = (this.vehicles || []).find((v) => v.name === val);
			if (vehicle) {
				this.selectedVehicle = val;
				this.vehicle_no = vehicle.vehicle_no || "";
				this.eventBus.emit("vehicle_selected", vehicle.name);

				// Set customer if not already set
				if (!this.customer && vehicle.customer) {
					this.customer = vehicle.customer;
					this.internalCustomer = vehicle.customer;
					this.eventBus.emit("update_customer", vehicle.customer);
				}
			}
		},

		onVehicleSearch: _.debounce(function (val) {
			// Search logic here if needed
		}, 300),

		async onVehicleNoEnter() {
			const vehicleNo = (this.vehicle_no || "").trim();
			if (!vehicleNo) return;

			this.loadingVehicles = true;
			try {
				let customerName = null;
				let vehicleName = null;

				// 1. Local Lookup
				try {
					await checkDbHealth();
					if (!db.isOpen()) await db.open();
					const local = await db.table("vehicles").where("vehicle_no").equals(vehicleNo).first();
					if (local) {
						customerName = local.customer;
						vehicleName = local.name;
					}
				} catch (e) {
					console.warn("Local vehicle lookup error", e);
				}

				// 2. Server Lookup if no local match or online
				if (!customerName && navigator.onLine) {
					const res = await frappe.call({
						method: "posawesome.posawesome.api.vehicles.get_customer_by_vehicle",
						args: { vehicle_no: vehicleNo },
					});
					const payload = res?.message || {};
					if (payload.customer && payload.customer.name) {
						customerName = payload.customer.name;
					}
					if (payload.vehicle && payload.vehicle.name) {
						vehicleName = payload.vehicle.name;
					}
				}

				// Final update logic
				if (customerName) {
					this.customer = customerName;
					this.internalCustomer = customerName;
					this.eventBus.emit("update_customer", customerName);

					if (vehicleName) {
						this.selectedVehicle = vehicleName;
						this.eventBus.emit("vehicle_selected", vehicleName);
						this.fetchVehiclesForCustomer(customerName);
					} else {
						this.selectedVehicle = null;
						this.eventBus.emit("vehicle_selected", null);
					}

					// Add vehicle to list if not present
					if (vehicleName) {
						const existingVehicle = this.vehicles.find((v) => v.name === vehicleName);
						if (!existingVehicle) {
							this.vehicles.push({
								name: vehicleName,
								vehicle_no: vehicleNo,
								model: "",
								make: "",
								customer_name: this.internalCustomer,
								customer: customerName,
								mobile_no: "",
							});
						}
					}
				} else {
					frappe.show_alert({ message: __("No customer found for vehicle"), indicator: "red" });
					this.selectedVehicle = null;
					this.eventBus.emit("vehicle_selected", null);
				}
			} catch (err) {
				console.error("Failed to lookup customer by vehicle:", err);
				frappe.show_alert({ message: __("Error looking up vehicle"), indicator: "red" });
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
			// FIX: Always emit the event to open the dialog.
			// The UpdateVehicle dialog should handle the case of a missing customer.
			// If the user is on the text-input field, we can pass the vehicle_no they typed.
			const payload = {
				customer: this.customer,
				vehicle_no: this.vehicles.length === 0 ? this.vehicle_no : null,
			};

			// This emits the event to open the vehicle creation form
			this.eventBus.emit("open_update_vehicle", payload);
		},
	},

	created() {
		memoryInitPromise.then(async () => {
			await this.searchCustomers("");
			this.effectiveReadonly = this.readonly && navigator.onLine;
		});

		this.eventBus.on("load_invoice_customer", async (customerName) => {
			console.log("[Customer] load_invoice_customer event received:", customerName);

			if (!customerName) {
				this.customer = null;
				this.internalCustomer = null;
				this.vehicles = [];
				this.selectedVehicle = null;
				return;
			}

			// Set the customer directly
			this.customer = customerName;
			this.internalCustomer = customerName;

			console.log("[Customer] Customer set to:", customerName);

			// Fetch vehicles for this customer
			await this.fetchVehiclesForCustomer(customerName);

			this.$nextTick(() => {
				this.$forceUpdate();
			});
		});
		this.searchDebounce = _.debounce(async (val) => {
			this.searchTerm = val || "";
			this.page = 0;
			this.customers = [];
			this.hasMore = true;
			await this.searchCustomers(this.searchTerm);

			// FETCH VEHICLES DIRECTLY WHEN CUSTOMER SEARCH CHANGES
			if (val) {
				const matched = this.customers.find((cust) => {
					return (
						cust.customer_name?.toLowerCase().includes(val.toLowerCase()) ||
						cust.name?.toLowerCase().includes(val.toLowerCase()) ||
						cust.mobile_no?.toLowerCase().includes(val.toLowerCase())
					);
				});

				if (matched) {
					this.customer = matched.name;
					this.internalCustomer = matched.name;
					this.eventBus.emit("update_customer", matched.name);
					await this.fetchVehiclesForCustomer(matched.name);
					this.selectedVehicle = null;
				}
			}
		}, 500);

		this.effectiveReadonly = this.readonly && navigator.onLine;

		this.$nextTick(() => {
			if (!window._customerListenersRegistered) {
				this.eventBus.on("register_pos_profile", async (pos_profile) => {
					await memoryInitPromise;
					this.pos_profile = pos_profile;
					await this.get_customer_names();
					if (this.customer) {
						this.fetchVehiclesForCustomer(this.customer);
					}
				});

				this.eventBus.on("payments_register_pos_profile", async (pos_profile) => {
					await memoryInitPromise;
					this.pos_profile = pos_profile;
					await this.get_customer_names();
					if (this.customer) {
						this.fetchVehiclesForCustomer(this.customer);
					}
				});

				this.eventBus.on("set_customer", (customer) => {
					this.customer = customer;
					this.internalCustomer = customer;
					this.fetchVehiclesForCustomer(customer);
				});

				// MODIFIED: Handle both customer and vehicle data from UpdateCustomer.vue
				this.eventBus.on("add_customer_to_list", async (data) => {
					// Assume data can be a customer object OR { customer: {...}, vehicle: {...} }
					const customer = data.customer || data;
					const vehicle = data.vehicle || null;

					const index = this.customers.findIndex((c) => c.name === customer.name);
					if (index !== -1) {
						this.customers.splice(index, 1, customer);
					} else {
						this.customers.push(customer);
					}
					await setCustomerStorage([customer]);
					this.customer = customer.name;
					this.internalCustomer = customer.name;
					this.eventBus.emit("update_customer", customer.name);

					if (vehicle && vehicle.vehicle_no) {
						// If a vehicle was created, update the vehicle list directly
						this.eventBus.emit("add_vehicle_to_list", vehicle);
						this.selectedVehicle = vehicle.name;
						this.eventBus.emit("vehicle_selected", vehicle.name);
					} else {
						// Otherwise, fetch existing vehicles
						this.fetchVehiclesForCustomer(customer.name);
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
				});

				this.eventBus.on("add_vehicle_to_list", (vehicle) => {
					if (vehicle.customer === this.customer) {
						// Remove placeholder and old entry if updating
						this.vehicles = this.vehicles.filter((v) => v.name && v.name !== vehicle.name);
						this.vehicles.push({
							name: vehicle.name,
							vehicle_no: vehicle.vehicle_no,
							model: vehicle.model || "",
							make: vehicle.make || "",
							mobile_no: vehicle.mobile_no || "",
							customer_name: vehicle.customer_name,
							customer: vehicle.customer,
						});

						if (this.vehicles.length === 1) {
							// Case: New vehicle is the only vehicle
							this.selectedVehicle = vehicle.name;
							this.eventBus.emit("vehicle_selected", vehicle.name);
						} else {
							// Case: Vehicle added to a list with other vehicles (re-add placeholder)
							this.vehicles.unshift({ name: null, vehicle_no: frappe._("Select Vehicle...") });
							this.selectedVehicle = vehicle.name;
							this.eventBus.emit("vehicle_selected", vehicle.name);
						}
					}
				});

				this.eventBus.on("set_vehicle", (vehicle_name) => {
					this.selectedVehicle = vehicle_name;
					this.onVehicleSelect(vehicle_name);
				});

				this.eventBus.on("set_customer_from_vehicle", (customer) => {
					if (customer && customer.name) {
						this.customer = customer.name;
						this.internalCustomer = customer.name;
						this.eventBus.emit("update_customer", customer.name);
						this.fetchVehiclesForCustomer(customer.name);
					}
				});
				window._customerListenersRegistered = true;
			}
		});

		// Initial Vehicle Load
		if (this.customer) {
			this.fetchVehiclesForCustomer(this.customer);
		}
	},
};
</script>
