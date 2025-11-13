<template>
	<v-row justify="center">
		<v-dialog v-model="vehicleDialog" max-width="500px" persistent>
			<v-card>
				<v-card-title class="d-flex align-center">
					<span v-if="vehicle_id" class="text-h5 text-primary">{{ __("Update Vehicle") }}</span>
					<span v-else class="text-h5 text-primary">{{ __("Add Vehicle") }}</span>
					<v-spacer></v-spacer>
				</v-card-title>
				<v-card-text class="pa-0">
					<v-container>
						<v-row>
							<v-col cols="12">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Vehicle No') + ' *'"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="vehicle_no"
									:readonly="!!vehicle_id"
								></v-text-field>
							</v-col>

							<v-col cols="12">
								<v-autocomplete
									density="compact"
									color="primary"
									:label="frappe._('Customer Name') + ' *'"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="customer"
									:items="customer_list"
									item-title="customer_name"
									item-value="name"
									:loading="loading_customers"
									@update:search="search_customers"
								>
								<template #no-data>
									<div class="pa-2 text-center text-caption text-medium-emphasis">
										{{ __("No customers found. Start typing to search.") }}
									</div>
								</template>
								</v-autocomplete>
							</v-col>

							<v-col cols="6">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Make')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="make"
								></v-text-field>
							</v-col>

							<v-col cols="6">
								<v-autocomplete
									density="compact"
									color="primary"
									:label="frappe._('Model No')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="model"
									:items="model_list"
									:loading="loading_models"
									@update:search="search_models"
									clearable
								>
								<template #no-data>
									<div class="pa-2 text-center text-caption text-medium-emphasis">
										{{ __("No models found. Type to enter a new one.") }}
									</div>
								</template>
								</v-autocomplete>
							</v-col>

							<v-col cols="6">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Chasis No')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="chasis_no"
								></v-text-field>
							</v-col>

							<v-col cols="6">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Color')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="color"
								></v-text-field>
							</v-col>
							<v-col cols="12">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Registration Number')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="registration_number"
								></v-text-field>
							</v-col>
							<v-col cols="12">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Mobile No')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="mobile_no"
								></v-text-field>
							</v-col>

						</v-row>
					</v-container>
				</v-card-text>
				<v-card-actions>
					<v-spacer></v-spacer>
					<v-btn color="grey-darken-1" variant="text" @click="close_dialog">
						{{ __("Cancel") }}
					</v-btn>
					<v-btn color="primary" variant="tonal" :loading="loading" @click="save_vehicle" :disabled="!is_valid">
						{{ __("Save") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
/* global frappe __ */
export default {
	data: () => ({
		vehicleDialog: false,
		loading: false,
		vehicle_id: null,
		vehicle_no: "",
		customer: "", 
		customer_list: [],
		loading_customers: false,
		
		// New Data Properties for Model List
		loading_models: false,
		model_list: [], 

		make: "",
		model: "", // Holds the selected or typed model name
		mobile_no: "",
		chasis_no: "", 
        color: "", 
        registration_number: "",
	}),

	computed: {
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
		is_valid() {
			return this.vehicle_no && this.customer; 
		}
	},

	methods: {
		reset_dialog() {
			this.vehicle_id = null;
			this.vehicle_no = "";
			this.customer = "";
            this.loading = false;
			this.make = "";
			this.model = "";
			this.mobile_no = "";
			this.customer_list = []; 
			this.chasis_no = "";
            this.color = "";
            this.registration_number = "";
			this.model_list = []; // Reset model list
		},

		close_dialog() {
			this.vehicleDialog = false;
			this.reset_dialog();
		},

		// --- Customer Search Logic (from previous step) ---
		async search_customers(search_term = "") {
			this.loading_customers = true;
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.customers.search_customers",
					args: { search_term },
				});

				if (res.message) {
					this.customer_list = res.message;
				}
			} catch (err) {
				console.error("Customer search failed:", err);
				this.customer_list = [];
			} finally {
				this.loading_customers = false;
			}
		},
		
		// --- Model Search Logic (New) ---
		async search_models(search_term = "") {
			this.loading_models = true;
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.get_vehicle_models", 
					args: { search_term },
				});

				if (res.message) {
					this.model_list = res.message;
				}
			} catch (err) {
				console.error("Model search failed:", err);
				this.model_list = [];
			} finally {
				this.loading_models = false;
			}
		},

		async open_dialog(payload) {
			this.reset_dialog();
			
			// Load initial data for Customer and Model
			await Promise.all([
				this.search_customers(),
				this.search_models() // Call new function to load models
			]);
            
			if (payload.name) { // Editing an existing vehicle
				this.vehicle_id = payload.name;
				this.vehicle_no = payload.vehicle_no;
				this.customer = payload.customer;
				this.make = payload.make || "";
				this.model = payload.model || "";
				this.mobile_no = payload.mobile_no || "";
				this.chasis_no = payload.chasis_no || "";
                this.color = payload.color || "";
                this.registration_number = payload.registration_number || "";
                
                // Ensure the selected customer is available in the list
                if (this.customer && !this.customer_list.find(c => c.name === this.customer)) {
                     const cust_doc = await frappe.call({
                        method: "frappe.client.get",
                        args: { doctype: "Customer", name: this.customer },
                     });
                     if (cust_doc) {
                        this.customer_list.push({
                            name: cust_doc.name, 
                            customer_name: cust_doc.customer_name
                        });
                     }
                }
			} else if (payload.customer) { 
				this.customer = payload.customer;
                this.vehicle_no = payload.vehicle_no || ''; 
			}
            
			this.vehicleDialog = true;
		},

		async save_vehicle() {
			// Basic validation
			if (!this.vehicle_no || !this.customer) {
				frappe.show_alert({
					message: this.__("Please fill in all mandatory fields."),
					indicator: "orange",
				});
				return;
			}
			this.loading = true;
			try {
				const args = {
					// MANDATORY FIELDS
					vehicle_no: this.vehicle_no,
					customer: this.customer,

					// --- CRITICAL CHANGE: Ensure all Python arguments are passed ---
					// Use '|| null' to handle optional fields that might be blank strings
					model: this.model || null,
					make: this.make || null,
					chasis_no: this.chasis_no || null,
					color: this.color || null,
					registration_number: this.registration_number || null,
					mobile_no: this.mobile_no || null,

					// CONTROL FIELDS
					method: this.vehicle_id ? "update" : "create",
					vehicle_id: this.vehicle_id,
				};

				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.create_vehicle",
					args: args,
				});

				if (res.message) {
					frappe.show_alert({
						message: this.__("Vehicle saved successfully!"),
						indicator: "green",
					});
					this.close_dialog();
					this.eventBus.emit("add_vehicle_to_list", res.message);
					this.eventBus.emit("set_vehicle", res.message.name);
				}
			} catch (err) {
				console.error("Vehicle save failed:", err);
				frappe.show_alert({
					message: this.__("Failed to save vehicle. Check server logs for details."),
					indicator: "red",
				});
			} finally {
				this.loading = false;
			}
		},
	},

	created() {
		this.eventBus.on("open_update_vehicle", this.open_dialog); 
	},
    beforeUnmount() {
        this.eventBus.off("open_update_vehicle", this.open_dialog);
    }
};
</script>

<style scoped>
/* Dark mode input styling for Vuetify components */
:deep([data-theme="dark"]) .dark-field,
:deep(.v-theme--dark) .dark-field,
::v-deep([data-theme="dark"]) .dark-field,
::v-deep(.v-theme--dark) .dark-field {
	background-color: #1e1e1e !important;
}

/* Style the actual input field and label inside the dark-field wrapper to be white in dark mode */
:deep([data-theme="dark"]) .dark-field :deep(.v-field__input),
:deep(.v-theme--dark) .dark-field :deep(.v-field__input),
:deep([data-theme="dark"]) .dark-field :deep(input),
:deep(.v-theme--dark) .dark-field :deep(input),
:deep([data-theme="dark"]) .dark-field :deep(.v-label),
:deep(.v-theme--dark) .dark-field :deep(.v-label),
::v-deep([data-theme="dark"]) .dark-field .v-field__input,
::v-deep(.v-theme--dark) .dark-field .v-field__input,
::v-deep([data-theme="dark"]) .dark-field input,
::v-deep(.v-theme--dark) .dark-field input,
::v-deep([data-theme="dark"]) .dark-field .v-label,
::v-deep(.v-theme--dark) .dark-field .v-label {
	color: white !important;
}
</style>
