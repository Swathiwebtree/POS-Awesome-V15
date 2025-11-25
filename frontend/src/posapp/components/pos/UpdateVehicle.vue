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
									clearable
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
					<v-btn
						color="primary"
						variant="tonal"
						:loading="loading"
						@click="save_vehicle"
						:disabled="!is_valid"
					>
						{{ __("Save") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
/* global frappe __ */
let _updateVehicleInstance = null;
let _updateVehicleListenerRegistered = false;

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
			return this.$theme && this.$theme.current === "dark";
		},
		is_valid() {
			return this.vehicle_no && this.customer;
		},
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

		// --- Customer Search Logic ---
		async search_customers(search_term = "") {
			// small debounce could be added if needed
			this.loading_customers = true;
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.customers.search_customers",
					args: { search_term },
				});

				if (res && res.message) {
					this.customer_list = res.message;
				} else {
					this.customer_list = [];
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

				if (res && res.message) {
					this.model_list = res.message;
				} else {
					this.model_list = [];
				}
			} catch (err) {
				console.error("Model search failed:", err);
				this.model_list = [];
			} finally {
				this.loading_models = false;
			}
		},

		// single entry point to open and populate the dialog
		async open_dialog(payload = {}) {
			this.reset_dialog();

			// pre-load lists (no-op if server returns quickly)
			await Promise.all([this.search_customers(), this.search_models()]);

			if (payload && payload.name) {
				// editing an existing vehicle
				this.vehicle_id = payload.name;
				this.vehicle_no = payload.vehicle_no || "";
				this.customer = payload.customer || "";
				this.make = payload.make || "";
				this.model = payload.model || "";
				this.mobile_no = payload.mobile_no || "";
				this.chasis_no = payload.chasis_no || "";
				this.color = payload.color || "";
				this.registration_number = payload.registration_number || "";

				// ensure chosen customer exists in the dropdown list
				if (this.customer && !this.customer_list.find((c) => c.name === this.customer)) {
					try {
						const cust_doc_res = await frappe.call({
							method: "frappe.client.get",
							args: { doctype: "Customer", name: this.customer },
						});
						if (cust_doc_res && cust_doc_res.message) {
							this.customer_list.push({
								name: cust_doc_res.message.name,
								customer_name: cust_doc_res.message.customer_name,
							});
						}
					} catch (e) {
						// ignore missing customer; still open dialog
						console.warn("Failed to fetch customer for dialog:", e);
					}
				}
			} else {
				// payload may include preselected customer or vehicle_no
				if (payload && payload.customer) this.customer = payload.customer;
				if (payload && payload.vehicle_no) this.vehicle_no = payload.vehicle_no;
			}

			this.vehicleDialog = true;
		},

		async save_vehicle() {
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
					vehicle_no: this.vehicle_no,
					customer: this.customer,
					model: this.model || null,
					make: this.make || null,
					chasis_no: this.chasis_no || null,
					color: this.color || null,
					registration_number: this.registration_number || null,
					mobile_no: this.mobile_no || null,
					method: this.vehicle_id ? "update" : "create",
					vehicle_id: this.vehicle_id,
				};

				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.create_vehicle",
					args,
				});

				if (res && res.message) {
					frappe.show_alert({
						message: this.__("Vehicle saved successfully!"),
						indicator: "green",
					});
					this.close_dialog();
					// notify other parts of the app
					try {
						this.eventBus?.emit("add_vehicle_to_list", res.message);
						this.eventBus?.emit("set_vehicle", res.message.name);
					} catch (e) {
						// ignore if eventBus missing
					}
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
		// singleton listener to avoid duplicate handlers across mounts
		_updateVehicleInstance = this;
		const bus = this.eventBus || window.eventBus || window.app_event_bus || null;

		const globalHandler = (payload) => {
			const data = payload && payload.detail ? payload.detail : payload;
			if (_updateVehicleInstance && typeof _updateVehicleInstance.open_dialog === "function") {
				_updateVehicleInstance.open_dialog(data || {});
			}
		};

		if (!_updateVehicleListenerRegistered) {
			if (bus && typeof bus.on === "function") {
				bus.on("open_update_vehicle", globalHandler);
			} else if (typeof window !== "undefined") {
				window.addEventListener("open_update_vehicle", globalHandler);
			}
			_updateVehicleListenerRegistered = true;
		}

		// Also register a local eventBus handler to support direct local emits
		// if (this.eventBus && typeof this.eventBus.on === "function") {
		//   this.eventBus.on("open_update_vehicle", (data) => {
		//     // forward into the canonical handler
		//     this.open_dialog(data && data.detail ? data.detail : data);
		//   });
		// } else {
		//   // DOM fallback (already registered above as globalHandler)
		//   // no-op
		// }
	},

	beforeUnmount() {
		// clear instance reference but leave the global listener in place for app lifetime
		_updateVehicleInstance = null;
		_updateVehicleListenerRegistered = false;

		// remove local eventBus handler if present
		if (this.eventBus && typeof this.eventBus.off === "function") {
			this.eventBus.off("open_update_vehicle", this.open_dialog);
		}
	},
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

/* Style the input and label inside the dark-field wrapper to be white in dark mode */
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
