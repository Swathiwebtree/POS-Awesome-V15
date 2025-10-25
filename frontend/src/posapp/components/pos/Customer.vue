<template>
	<div class="customer-vehicle-row" style="display:flex; gap:12px; align-items:flex-start;">
		<div style="flex: 1 1 0;">
			<Skeleton v-if="loadingCustomers" height="48" class="w-100" />
			<v-autocomplete v-else ref="customerDropdown" class="customer-autocomplete sleek-field" density="compact"
				clearable variant="solo" color="#4169E1" :label="frappe._('Customer')" v-model="internalCustomer"
				:items="filteredCustomers" item-title="customer_name" item-value="name"
				:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
				:no-data-text="isCustomerBackgroundLoading ? __('Loading customer data...') : __('Customers not found')"
				hide-details :customFilter="() => true" :disabled="effectiveReadonly || loadingCustomers"
				:menu-props="{ closeOnContentClick: false }" @update:menu="onCustomerMenuToggle"
				@update:modelValue="onCustomerChange" @update:search="onCustomerSearch" @keydown.enter="handleEnter"
				:virtual-scroll="true" :virtual-scroll-item-height="48">
				<template #prepend-inner>
					<v-tooltip text="Edit customer">
						<template #activator="{ props }">
							<v-icon v-bind="props" class="icon-button" @mousedown.prevent.stop
								@click.stop="edit_customer">mdi-account-edit</v-icon>
						</template>
					</v-tooltip>
				</template>

				<template #append-inner>
					<v-tooltip text="Add new customer">
						<template #activator="{ props }">
							<v-icon v-bind="props" class="icon-button" @mousedown.prevent.stop
								@click.stop="new_customer">mdi-plus</v-icon>
						</template>
					</v-tooltip>
				</template>

				<template #item="{ props, item }">
					<v-list-item v-bind="props">
						<v-list-item-title>{{ item.raw.customer_name }}</v-list-item-title>
						<v-list-item-subtitle v-if="item.raw.customer_name !== item.raw.name">
							<div>ID: {{ item.raw.name }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.tax_id">
							<div>TAX ID: {{ item.raw.tax_id }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.email_id">
							<div>Email: {{ item.raw.email_id }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.mobile_no">
							<div>Mobile No: {{ item.raw.mobile_no }}</div>
						</v-list-item-subtitle>
						<v-list-item-subtitle v-if="item.raw.primary_address">
							<div>Primary Address: {{ item.raw.primary_address }}</div>
						</v-list-item-subtitle>
					</v-list-item>
				</template>
			</v-autocomplete>
		</div>

		<div style="width: 280px; min-width: 220px;">
			<v-autocomplete v-if="vehicles && vehicles.length > 1" ref="vehicleDropdown"
				class="vehicle-autocomplete sleek-field" density="compact" clearable variant="solo"
				:label="frappe._('Vehicle No')" v-model="selectedVehicle" :items="vehicles" item-title="vehicle_no"
				item-value="name" hide-details :disabled="loadingVehicles" @update:modelValue="onVehicleSelect"
				@update:search="onVehicleSearch" :virtual-scroll="true" :virtual-scroll-item-height="48">
				<template #prepend-inner>
					<v-tooltip text="Edit vehicle">
						<template #activator="{ props }">
							<v-icon v-bind="props" class="icon-button" @mousedown.prevent.stop
								@click.stop="edit_vehicle">mdi-car-edit</v-icon>
						</template>
					</v-tooltip>
				</template>
				<template #append-inner>
					<v-tooltip text="Add vehicle">
						<template #activator="{ props }">
							<v-icon v-bind="props" class="icon-button" @mousedown.prevent.stop
								@click.stop="new_vehicle">mdi-plus</v-icon>
						</template>
					</v-tooltip>
				</template>
				<template #item="{ props, item }">
					<v-list-item v-bind="props">
						<v-list-item-title>{{ item.vehicle_no }}</v-list-item-title>
						<v-list-item-subtitle v-if="item.model">Model: {{ item.model }}</v-list-item-subtitle>
					</v-list-item>
				</template>
			</v-autocomplete>

			<v-text-field v-else-if="vehicles && vehicles.length === 1" readonly dense variant="solo"
				:label="frappe._('Vehicle No')" :value="vehicles[0].vehicle_no" hide-details />

			<v-text-field v-else v-model="vehicle_no" dense variant="solo" :label="frappe._('Vehicle No')"
				placeholder="Enter vehicle no and press Enter" @keydown.enter.prevent="onVehicleNoEnter" hide-details />
		</div>
	</div>
</template>

<style scoped>
.customer-input-wrapper {
	width: 100%;
	max-width: 100%;
	padding-right: 1.5rem;
	/* Elegant space at the right edge */
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	position: relative;
}

.customer-autocomplete {
	width: 100%;
	box-sizing: border-box;
	border-radius: 12px;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
	transition: box-shadow 0.3s ease;
	background-color: #fff;
}

.customer-autocomplete:hover {
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Dark mode styling */
:deep([data-theme="dark"]) .customer-autocomplete,
:deep(.v-theme--dark) .customer-autocomplete,
::v-deep([data-theme="dark"]) .customer-autocomplete,
::v-deep(.v-theme--dark) .customer-autocomplete {
	/* Use surface color for dark mode */
	background-color: #1e1e1e !important;
}

:deep([data-theme="dark"]) .customer-autocomplete :deep(.v-field__input),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-field__input),
:deep([data-theme="dark"]) .customer-autocomplete :deep(input),
:deep(.v-theme--dark) .customer-autocomplete :deep(input),
:deep([data-theme="dark"]) .customer-autocomplete :deep(.v-label),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-label),
::v-deep([data-theme="dark"]) .customer-autocomplete .v-field__input,
::v-deep(.v-theme--dark) .customer-autocomplete .v-field__input,
::v-deep([data-theme="dark"]) .customer-autocomplete input,
::v-deep(.v-theme--dark) .customer-autocomplete input,
::v-deep([data-theme="dark"]) .customer-autocomplete .v-label,
::v-deep(.v-theme--dark) .customer-autocomplete .v-label {
	color: #fff !important;
}

:deep([data-theme="dark"]) .customer-autocomplete :deep(.v-field__overlay),
:deep(.v-theme--dark) .customer-autocomplete :deep(.v-field__overlay),
::v-deep([data-theme="dark"]) .customer-autocomplete .v-field__overlay,
::v-deep(.v-theme--dark) .customer-autocomplete .v-field__overlay {
	background-color: #1e1e1e !important;
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
import UpdateCustomer from "./UpdateCustomer.vue";
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
        // Track background loading state and pending searches
        isCustomerBackgroundLoading: false,
        pendingCustomerSearch: null,
        loadProgress: 0,
        totalCustomerCount: 0,
        loadedCustomerCount: 0,
        vehicles: [], 
        selectedVehicle: null, 
        vehicle_no: "",
        loadingVehicles: false,
    }),

    components: {
        UpdateCustomer,
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
        // Called when dropdown opens or closes
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

        // Called when a customer is selected
        onCustomerChange(val) {
            // if user selects the same customer again, show a meaningful error
            if (val && val === this.customer) {
                // keep the current selection and notify the user
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
                // **NEW LOGIC: Fetch vehicles when customer changes**
                this.fetchVehiclesForCustomer(val);
                this.selectedVehicle = null; // Clear old vehicle selection
                // ----------------------------------------------------
            }
            
            if (!val) {
                // Customer cleared
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

        // Pressing Enter in input
        handleEnter(event) {
            const inputText = event.target.value?.toLowerCase() || "";

            const matched = this.customers.find((cust) => {
                return (
                    cust.customer_name?.toLowerCase().includes(inputText) ||
                    cust.name?.toLowerCase().includes(inputText)
                );
            });

            if (matched) {
                this.tempSelectedCustomer = matched.name;
                this.internalCustomer = matched.name;
                this.customer = matched.name;
                this.eventBus.emit("update_customer", matched.name);
                // **NEW LOGIC: Fetch vehicles when customer set by Enter**
                this.fetchVehiclesForCustomer(matched.name);
                this.selectedVehicle = null; // Clear old vehicle selection
                // ----------------------------------------------------
                this.isMenuOpen = false;

                event.target.blur();
            }
        },

        async searchCustomers(term, append = false) {
            try {
                await checkDbHealth();
                if (!db.isOpen()) await db.open();
                let collection = db.table("customers");
                if (term) {
                    collection = db
                        .table("customers")
                        .where("customer_name")
                        .startsWithIgnoreCase(term)
                        .or("mobile_no")
                        .startsWithIgnoreCase(term)
                        .or("email_id")
                        .startsWithIgnoreCase(term)
                        .or("tax_id")
                        .startsWithIgnoreCase(term)
                        .or("name")
                        .startsWithIgnoreCase(term);
                }
                const results = await collection
                    .offset(this.page * this.pageSize)
                    .limit(this.pageSize)
                    .toArray();
                if (append) {
                    this.customers.push(...results);
                } else {
                    this.customers = results;
                }
                this.hasMore = results.length === this.pageSize;
                if (this.hasMore) {
                    this.page += 1;
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
                // FIX: Ensure pos_profile is passed to the API call
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
                // Fetch total customer count for accurate progress
                try {
                    // FIX: Ensure pos_profile is passed to the API call
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
                    // Load remaining customers in the background
                    this.backgroundLoadCustomers(this.nextCustomerStart, syncSince);
                } else {
                    setCustomersLastSync(new Date().toISOString());
                    this.loadProgress = 100;
                    this.eventBus.emit("data-load-progress", { name: "customers", progress: 100 });
                    this.eventBus.emit("data-loaded", "customers");
                }
                await this.searchCustomers(this.searchTerm);
            } catch (err) {
                console.error("Failed to fetch customer names:", err);
                frappe.show_alert({ message: __("Failed to load customer names"), indicator: "red" });
            } finally {
                this.loadingCustomers = false;
                this.customers_loaded = true;
            }
        },
        
        // New Vehicle-related methods added to script for completeness
        async fetchVehiclesForCustomer(customerName){
            this.vehicles = []; 
            this.selectedVehicle = null;
            this.vehicle_no = "";
            if(!customerName) return; 
            
            this.loadingVehicles = true;
            try{
                let fetchedVehicles = [];

                // 1. Offline lookup
                try{ 
                    await checkDbHealth(); 
                    if(!db.isOpen()) await db.open(); 
                    const local = await db.table("vehicles").where("customer").equals(customerName).toArray(); 
                    if(local && local.length){ 
                        fetchedVehicles = local.map(r => ({
                            name: r.name || r.id, 
                            vehicle_no: r.vehicle_no, 
                            model: r.model, 
                            make: r.make, 
                            mobile_no: r.mobile_no
                        })); 
                    } 
                } catch(e){ 
                    console.warn("Local vehicle lookup failed", e); 
                }

                // 2. Server lookup if offline lookup failed or if online
                if (!fetchedVehicles.length || navigator.onLine) {
                    const res = await frappe.call({
                        method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer", 
                        args: {customer_name: customerName, limit: 200}
                    });
                    const serverVehicles = res?.message || [];
                    
                    // Merge/Deduplicate server results with local results
                    const localNames = new Set(fetchedVehicles.map(v => v.name));
                    for (const v of serverVehicles) {
                        if (!localNames.has(v.name)) {
                            fetchedVehicles.push({
                                name: v.name, 
                                vehicle_no: v.vehicle_no, 
                                model: v.model, 
                                make: v.make, 
                                mobile_no: v.mobile_no
                            });
                        }
                    }
                }
                
                this.vehicles = fetchedVehicles;

                if(this.vehicles.length === 1){ 
                    this.selectedVehicle = this.vehicles[0].name; 
                    this.vehicle_no = this.vehicles[0].vehicle_no;
                    this.eventBus.emit("vehicle_selected", this.vehicles[0].name); 
                }
            } catch(err){ 
                console.error("Failed to fetch vehicles for customer:", err); 
            }
            finally{ 
                this.loadingVehicles = false; 
            }
        },

        async onVehicleSelect(vehicleDocName){
            if(!vehicleDocName){ 
                this.selectedVehicle = null; 
                this.vehicle_no = "";
                this.eventBus.emit("vehicle_selected", null);
                return; 
            }

            const vehicle = (this.vehicles || []).find(v => v.name === vehicleDocName);
            if(vehicle){ 
                this.selectedVehicle = vehicleDocName; 
                this.vehicle_no = vehicle.vehicle_no || ""; 
                this.eventBus.emit("vehicle_selected", vehicle.name); 
                
                // If a vehicle is selected, set the customer if it's currently empty
                // or if the vehicle is linked to a different customer.
                // This logic is typically handled by the vehicle change event.
                if(!this.customer && vehicle.customer){ 
                     // Assuming 'vehicle' object contains 'customer' property if retrieved from offline/server.
                    this.customer = vehicle.customer; 
                    this.internalCustomer = vehicle.customer; 
                    this.eventBus.emit("update_customer", vehicle.customer); 
                }
            }
        },

        async onVehicleNoEnter(){
            const vehicleNo = (this.vehicle_no || "").trim(); 
            if(!vehicleNo) return;

            this.loadingVehicles = true;
            try{ 
                let customerName = null;
                let vehicleName = null;

                // 1. Local Lookup
                try{ 
                    await checkDbHealth(); 
                    if(!db.isOpen()) await db.open(); 
                    const local = await db.table("vehicles").where("vehicle_no").equals(vehicleNo).first(); 
                    if(local){ 
                        customerName = local.customer;
                        vehicleName = local.name;
                    } 
                } catch(e){ 
                    console.warn("Local vehicle lookup error", e); 
                }

                // 2. Server Lookup if no local match or online
                if (!customerName && navigator.onLine) {
                    const res = await frappe.call({ 
                        method: "posawesome.posawesome.api.customers.get_customer_by_vehicle", 
                        args: { vehicle_no: vehicleNo }
                    }); 
                    const payload = res?.message || {}; 
                    if(payload.customer && payload.customer.name){ 
                        customerName = payload.customer.name;
                    }
                    if(payload.vehicle && payload.vehicle.name){
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
                        // Also fetch the full list of vehicles for the newly set customer
                        this.fetchVehiclesForCustomer(customerName);
                    } else {
                        this.selectedVehicle = null;
                        this.eventBus.emit("vehicle_selected", null);
                    }

                    // Attempt to find the full vehicle object to fill the dropdown if needed
                    if(vehicleName) {
                         // Ensure vehicle is added to the vehicles list for selection
                         const existingVehicle = this.vehicles.find(v => v.name === vehicleName);
                         if (!existingVehicle) {
                             // Assuming we only have vehicle_no here, we can fetch vehicle details if necessary, 
                             // but for now, we rely on the `fetchVehiclesForCustomer` call.
                             // For immediate display, we can temporarily add it
                             this.vehicles.push({ name: vehicleName, vehicle_no: vehicleNo, model: '', make: '' });
                         }
                    }

                } else {
                    frappe.show_alert({message: __("No customer found for vehicle"), indicator: "red"});
                    this.selectedVehicle = null;
                    this.eventBus.emit("vehicle_selected", null);
                }

            } catch(err){ 
                console.error("Failed to lookup customer by vehicle:", err); 
                frappe.show_alert({message: __("Error looking up vehicle"), indicator: "red"}); 
            } finally {
                this.loadingVehicles = false;
            }
        },

        async onVehicleSearch(searchText){ /* optional: implement server search if vehicles not loaded */ },

        // CRUD functions for completeness
        new_customer() { this.eventBus.emit("open_update_customer", null); },
        edit_customer() { this.eventBus.emit("open_update_customer", this.customer_info); },
        new_vehicle() { this.eventBus.emit("open_vehicle_modal", this.customer ? { customer: this.customer } : null); }, // Pass current customer
        edit_vehicle() { this.eventBus.emit("open_vehicle_modal", { vehicle: this.selectedVehicle }); },

        // Event Bus registration for completeness
        registerEventBus() {
            this.eventBus.on("register_pos_profile", async pos_profile => { 
                this.pos_profile = pos_profile; 
                await this.get_customer_names(); 
                if (this.customer) {
                    this.fetchVehiclesForCustomer(this.customer);
                }
            });
            this.eventBus.on("payments_register_pos_profile", async pos_profile => { 
                this.pos_profile = pos_profile; 
                await this.get_customer_names(); 
                if (this.customer) {
                    this.fetchVehiclesForCustomer(this.customer);
                }
            });
            this.eventBus.on("set_customer", customer => { 
                this.customer = customer; 
                this.internalCustomer = customer; 
                this.fetchVehiclesForCustomer(customer); // Call fetch vehicles
            });
            this.eventBus.on("add_customer_to_list", async customer => { 
                const index = this.customers.findIndex(c=>c.name===customer.name); 
                if(index!==-1){
                    this.customers.splice(index,1,customer);
                } else {
                    this.customers.push(customer);
                } 
                await setCustomerStorage([customer]); 
                this.customer=customer.name; 
                this.internalCustomer=customer.name; 
                this.eventBus.emit("update_customer",customer.name); 
                this.fetchVehiclesForCustomer(customer.name); // Call fetch vehicles
            });
            this.eventBus.on("set_customer_readonly", value => { this.readonly = value; });
            this.eventBus.on("set_customer_info_to_edit", data => { this.customer_info = data; });
            this.eventBus.on("fetch_customer_details", async ()=> { await this.get_customer_names(); });
            this.eventBus.on("set_customer_from_vehicle", customer => { 
                if(customer && customer.name){ 
                    this.customer = customer.name; 
                    this.internalCustomer = customer.name; 
                    this.eventBus.emit("update_customer",customer.name); 
                    this.fetchVehiclesForCustomer(customer.name); 
                } 
            });
            this.eventBus.on("set_vehicle", vehicleName => { 
                if(vehicleName){ 
                    this.selectedVehicle=vehicleName; 
                    this.onVehicleSelect(vehicleName); 
                } 
            });
        },
    },

    created() {
        this.searchDebounce = _.debounce(async val => {
            this.searchTerm = val || "";
            this.page = 0;
            this.customers = [];
            this.hasMore = true;
            await this.searchCustomers(this.searchTerm);
        }, 300);

        this.effectiveReadonly = this.readonly && navigator.onLine;

        // Use a global promise (assuming `memoryInitPromise` is available globally as in the original code)
        if (typeof memoryInitPromise !== 'undefined') {
            memoryInitPromise.then(async () => {
                await this.get_customer_names(); // Use get_customer_names instead of direct search
                this.effectiveReadonly = this.readonly && navigator.onLine;
            });
        } else {
            // Fallback if memoryInitPromise is not defined
            this.get_customer_names();
        }

        this.registerEventBus();
        
        // **Initial Vehicle Load:** If customer is already set, load vehicles on initial load
        if (this.customer) {
            this.fetchVehiclesForCustomer(this.customer);
        }
    },
};
</script>