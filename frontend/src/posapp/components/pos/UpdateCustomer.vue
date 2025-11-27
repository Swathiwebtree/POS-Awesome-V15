<template>
	<v-row justify="center">
		<v-dialog v-model="customerDialog" max-width="780px" persistent>
			<v-card>
				<!-- HEADER -->
				<v-card-title class="d-flex align-center py-4 px-6">
					<span class="text-h5 text-primary font-weight-bold">
						{{ customer_id ? __("Update Customer") : __("Create Customer") }}
					</span>
					<v-spacer></v-spacer>
				</v-card-title>

				<!-- BODY -->
				<v-card-text class="px-6 pb-6 pt-0">
					<v-container fluid>
						<!-- TWO COLUMN FORM -->
						<v-row dense>
							<!-- VEHICLE COLUMN -->
							<v-col cols="6" class="pr-4">
								<v-text-field
									v-model="vehicle_no"
									:label="__('Vehicle Number') + (isCreateWithVehicle ? ' *' : '')"
									density="comfortable"
									color="primary"
									hide-details="auto"
									:required="isCreateWithVehicle"
									class="mb-3"
								/>

								<v-text-field
									v-model="mobile_no"
									:label="__('Mobile No') + (isCreateWithVehicle ? ' *' : '')"
									density="comfortable"
									color="primary"
									hide-details="auto"
									class="mb-3"
								/>

								<v-text-field
									v-model="vehicle_model"
									:label="__('Model')"
									density="comfortable"
									color="primary"
									hide-details="auto"
									class="mb-3"
								/>

								<v-text-field
									v-model="vehicle_make"
									:label="__('Make')"
									density="comfortable"
									color="primary"
									hide-details="auto"
									class="mb-3"
								/>

								<v-text-field
									v-model="odometer"
									:label="__('Odometer')"
									density="comfortable"
									color="primary"
									hide-details="auto"
								/>
							</v-col>

							<!-- CUSTOMER COLUMN -->
							<v-col cols="6" class="pl-4">
								<v-text-field
									v-model="customer_name"
									:label="__('Customer Name') + ' *'"
									density="comfortable"
									color="primary"
									hide-details="auto"
									required
									class="mb-3"
								/>

								<v-autocomplete
									v-model="group"
									:items="groups"
									:label="__('Customer Group') + ' *'"
									density="comfortable"
									hide-details="auto"
									color="primary"
									class="mb-3"
									clearable
								/>

								<v-autocomplete
									v-model="territory"
									:items="territorys"
									:label="__('Territory') + ' *'"
									density="comfortable"
									hide-details="auto"
									color="primary"
									class="mb-3"
									clearable
								/>
							</v-col>
						</v-row>
					</v-container>
				</v-card-text>

				<!-- FOOTER BUTTONS -->
				<v-card-actions class="px-6 pb-4">
					<v-spacer></v-spacer>
					<v-btn color="error" theme="dark" @click="confirm_close">
						{{ __("Close") }}
					</v-btn>
					<v-btn color="success" theme="dark" @click="submit_dialog">
						{{ __("Submit") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- CLOSE CONFIRMATION -->
		<v-dialog v-model="confirmDialog" max-width="400px">
			<v-card>
				<v-card-title class="text-h6 font-weight-bold text-primary">
					{{ __("Confirm Close") }}
				</v-card-title>
				<v-card-text>
					{{ __("Are you sure you want to close? All entered data will be lost.") }}
				</v-card-text>
				<v-card-actions>
					<v-spacer></v-spacer>
					<v-btn color="primary" @click="confirmDialog = false">
						{{ __("Continue Editing") }}
					</v-btn>
					<v-btn color="error" @click="confirmClose">
						{{ __("Yes, Close") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import { isOffline, saveOfflineCustomer } from "../../../offline/index.js";

let _updateCustomerInstance = null;
let _updateCustomerListenerRegistered = false;

export default {
	data: () => ({
		customerDialog: false,
		confirmDialog: false,
		pos_profile: null,

		// Customer fields
		customer_id: "",
		customer_name: "",
		tax_id: "",
		mobile_no: "",
		address_line1: "",
		city: "",
		country: "Pakistan",
		email_id: "",
		referral_code: "",
		birthday: "",
		group: "",
		groups: [],
		territory: "",
		territorys: [],
		genders: [],
		customer_type: "Individual",
		gender: "",
		loyalty_points: null,
		loyalty_program: null,
		hideNonEssential: false,

		// Vehicle fields (visible in both create & update)
		vehicle_no: "",
		vehicle_make: "",
		vehicle_model: "",
		odometer: "",

		// control - if this was explicitly opened as create-with-vehicle
		isCreateWithVehicle: false,
	}),
	computed: {
		isDarkTheme() {
			return this.$theme && this.$theme.current === "dark";
		},
	},
	methods: {
		confirm_close() {
			// If any data entered, ask confirmation
			if (
				this.customer_name ||
				this.tax_id ||
				this.mobile_no ||
				this.address_line1 ||
				this.email_id ||
				this.referral_code ||
				this.birthday ||
				this.vehicle_no ||
				this.vehicle_make ||
				this.vehicle_model
			) {
				this.confirmDialog = true;
			} else {
				this.close_dialog();
			}
		},
		confirmClose() {
			this.confirmDialog = false;
			this.close_dialog();
		},
		close_dialog() {
			this.customerDialog = false;
			this.clear_customer();
		},
		clear_customer() {
			this.customer_name = "";
			this.tax_id = "";
			this.mobile_no = "";
			this.address_line1 = "";
			this.city = "";
			this.country = (this.pos_profile && this.pos_profile.posa_default_country) || "Pakistan";
			this.email_id = "";
			this.referral_code = "";
			this.birthday = "";
			this.group = frappe.defaults.get_user_default("Customer Group");
			this.territory = frappe.defaults.get_user_default("Territory");
			this.customer_id = "";
			this.customer_type = "Individual";
			this.gender = "";
			this.loyalty_points = null;
			this.loyalty_program = null;

			this.vehicle_no = "";
			this.vehicle_make = "";
			this.vehicle_model = "";
			this.odometer = "";

			this.isCreateWithVehicle = false;
		},

		/**
		 * handleOpen accepts either:
		 * - { withVehicle: true }  => blank create dialog (vehicle fields available)
		 * - { ...customerObject }  => full customer object (editing). payload should include name and optionally vehicles array
		 * - { customer: {...}, withVehicle: true } => wrapper shape
		 */
		handleOpen(data) {
			const wrapper = data && data.customer ? data : null;
			const payload = wrapper ? wrapper.customer : data || {};

			// Reset first
			this.clear_customer();
			this.customerDialog = true;

			// If wrapper explicitly said create-with-vehicle, remember that for validation
			this.isCreateWithVehicle = !!(wrapper && wrapper.withVehicle === true && !payload.name);

			// If payload has name -> editing existing customer, prefill all fields
			if (payload && payload.name) {
				// populate customer fields
				this.customer_id = payload.name;
				this.customer_name = payload.customer_name || "";
				this.tax_id = payload.tax_id || "";
				this.mobile_no = payload.mobile_no || "";
				this.address_line1 = payload.address_line1 || "";
				this.city = payload.city || "";
				this.country =
					payload.country ||
					(this.pos_profile && this.pos_profile.posa_default_country) ||
					"Pakistan";
				this.email_id = payload.email_id || "";
				this.referral_code = payload.referral_code || "";
				this.birthday = payload.birthday || "";
				this.group = payload.customer_group || "";
				this.territory = payload.territory || "";
				this.loyalty_points = payload.loyalty_points || null;
				this.loyalty_program = payload.loyalty_program || null;
				this.gender = payload.gender || "";

				// Prefill vehicle details if provided (take the first vehicle)
				if (payload.vehicles && payload.vehicles.length) {
					const v = payload.vehicles[0];
					this.vehicle_no = v.vehicle_no || "";
					this.vehicle_make = v.make || "";
					this.vehicle_model = v.model || "";
					this.odometer = v.odometer || "";
				}
			} else {
				// New customer: if caller asked for withVehicle then require vehicle fields during submit
				// we still show vehicle fields for create (and update) per your request
				// mark isCreateWithVehicle true only when wrapper.withVehicle === true
				this.isCreateWithVehicle = !!(wrapper && wrapper.withVehicle === true);
				this.country = (this.pos_profile && this.pos_profile.posa_default_country) || "Pakistan";
			}
		},

		getCustomerGroups() {
			if (this.groups.length > 0) return;
			const vm = this;
			frappe.db
				.get_list("Customer Group", {
					fields: ["name"],
					filters: { is_group: 0 },
					limit: 1000,
					order_by: "name",
				})
				.then((data) => {
					data.forEach((el) => vm.groups.push(el.name));
				})
				.catch((e) => console.error("Failed to load groups", e));
		},
		getCustomerTerritorys() {
			if (this.territorys.length > 0) return;
			const vm = this;
			frappe.db
				.get_list("Territory", {
					fields: ["name"],
					filters: { is_group: 0 },
					limit: 5000,
					order_by: "name",
				})
				.then((data) => {
					data.forEach((el) => vm.territorys.push(el.name));
				})
				.catch((e) => console.error("Failed to load territorys", e));
		},
		getGenders() {
			if (this.genders.length > 0) return;
			const vm = this;
			frappe.db
				.get_list("Gender", {
					fields: ["name"],
					page_length: 50,
				})
				.then((data) => data.forEach((el) => vm.genders.push(el.name)))
				.catch((e) => console.error("Failed to load genders", e));
		},

		// Submit create / update
		submit_dialog() {
			const vm = this;

			// Basic validation
			if (!this.customer_name) {
				frappe.throw(__("Customer Name is required"));
				return;
			}
			if (!this.group) {
				frappe.throw(__("Customer group is required"));
				return;
			}
			if (!this.territory) {
				frappe.throw(__("Customer territory is required"));
				return;
			}
			// If this was an explicit create-with-vehicle flow, require vehicle + mobile
			if (!this.customer_id && this.isCreateWithVehicle) {
				if (!this.vehicle_no) {
					frappe.throw(__("Vehicle # is required to create a new customer with a vehicle."));
					return;
				}
				if (!this.mobile_no) {
					frappe.throw(__("Mobile No. is required to link the vehicle."));
					return;
				}
			}

			// Format birthday to YYYY-MM-DD if necessary
			let formatted_birthday = null;
			if (this.birthday) {
				// handle ddmmyyyy, dd-mm-yyyy, dd/mm/yyyy or Date string
				try {
					if (/^\d{8}$/.test(this.birthday)) {
						const day = this.birthday.substring(0, 2);
						const month = this.birthday.substring(2, 4);
						const year = this.birthday.substring(4);
						formatted_birthday = `${year}-${month}-${day}`;
					} else if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(this.birthday)) {
						const parts = this.birthday.split("-");
						formatted_birthday = `${parts[2]}-${parts[1].padStart(2, "0")}-${parts[0].padStart(2, "0")}`;
					} else if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(this.birthday)) {
						const parts = this.birthday.split("/");
						formatted_birthday = `${parts[2]}-${parts[1].padStart(2, "0")}-${parts[0].padStart(2, "0")}`;
					} else {
						const d = new Date(this.birthday);
						if (!isNaN(d.getTime())) {
							formatted_birthday = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
						}
					}
				} catch (e) {
					console.error("birthday format error", e);
				}
			}

			const customerArgs = {
				customer_id: this.customer_id,
				customer_name: this.customer_name,
				tax_id: this.tax_id,
				mobile_no: this.mobile_no,
				address_line1: this.address_line1,
				city: this.city,
				country: this.country,
				email_id: this.email_id,
				referral_code: this.referral_code,
				birthday: formatted_birthday || this.birthday,
				customer_group: this.group,
				territory: this.territory,
				customer_type: this.customer_type,
				gender: this.gender,
				method: this.customer_id ? "update" : "create",
				vehicle_no: this.vehicle_no || "",
			};

			// Always include vehicle object (server will decide whether to create or update)
			const vehicleArgs = {
				vehicle_no: this.vehicle_no || "",
				make: this.vehicle_make || "",
				model: this.vehicle_model || "",
				mobile_no: this.mobile_no || "",
				odometer: this.odometer || "",
			};

			const apiArgs = {
				customer: JSON.stringify(customerArgs),
				vehicle: JSON.stringify(vehicleArgs),
				company: vm.pos_profile ? vm.pos_profile.company : undefined,
				pos_profile_doc: JSON.stringify(vm.pos_profile || {}),
			};

			// Offline handling
			if (isOffline()) {
				const offlineData = {
					customer: customerArgs,
					vehicle: vehicleArgs,
					method: customerArgs.method,
				};
				saveOfflineCustomer({ args: offlineData });
				vm.eventBus.emit("show_message", {
					title: __("Customer/Vehicle saved offline"),
					color: "warning",
				});

				customerArgs.name = this.customer_name;
				const emittedData = {
					customer: customerArgs,
					vehicle: vehicleArgs.vehicle_no ? { name: null, ...vehicleArgs } : null,
				};
				vm.eventBus.emit("add_customer_to_list", emittedData);
				vm.eventBus.emit("set_customer", customerArgs.name);
				vm.close_dialog();
				return;
			}

			// API call (single endpoint handles create & update)
			const apiMethod = "posawesome.posawesome.api.customers.create_customer_with_vehicle";

			frappe.call({
				method: apiMethod,
				args: apiArgs,
				callback: (r) => {
					if (!r.exc && r.message && r.message.customer) {
						const customerDoc = r.message.customer;
						const vehicleDoc = r.message.vehicle || null;
						const msg = this.customer_id
							? __("Customer updated successfully.")
							: __("Customer created successfully.");

						vm.eventBus.emit("show_message", { title: msg, color: "success" });
						frappe.utils.play_sound("submit");

						vm.eventBus.emit("add_customer_to_list", {
							customer: customerDoc,
							vehicle: vehicleDoc,
						});
						vm.eventBus.emit("set_customer", customerDoc.name);
						vm.eventBus.emit("fetch_customer_details");
						vm.close_dialog();
					} else {
						vm.eventBus.emit("show_message", {
							title: __("Customer operation failed"),
							color: "error",
						});
					}
				},
				error: (r) => {
					frappe.utils.play_sound("error");
					let errorMessage = __("Customer/Vehicle operation failed.");
					if (r && r._server_messages) {
						try {
							const messages = JSON.parse(r._server_messages);
							if (messages && messages.length > 0) {
								const parsed = JSON.parse(messages[0]);
								errorMessage = parsed.message || errorMessage;
							}
						} catch (e) {
							console.error("Error parsing server messages:", e);
						}
					} else if (r && r.message) {
						errorMessage = r.message;
					}
					vm.eventBus.emit("show_message", { title: errorMessage, color: "error" });
				},
			});
		},

		onDateSelect() {
			this.birthday_menu = false;
			if (this.birthday) {
				try {
					let dateObj;
					if (typeof this.birthday === "object") {
						dateObj = this.birthday;
					} else {
						dateObj = new Date(this.birthday);
					}
					if (!isNaN(dateObj.getTime())) {
						const year = dateObj.getFullYear();
						const month = String(dateObj.getMonth() + 1).padStart(2, "0");
						const day = String(dateObj.getDate()).padStart(2, "0");
						this.birthday = `${day}-${month}-${year}`;
					}
				} catch (error) {
					console.error("Error formatting date from picker:", error);
				}
			}
		},
	},
	created() {
		// restore hideNonEssential (if used elsewhere)
		if (typeof localStorage !== "undefined") {
			const saved = localStorage.getItem("posawesome_hide_non_essential_fields");
			if (saved !== null) this.hideNonEssential = JSON.parse(saved);
		}

		// keep instance reference for single global handler
		_updateCustomerInstance = this;
		const bus = this.eventBus || window.eventBus || window.app_event_bus || null;

		if (!_updateCustomerListenerRegistered) {
			const handler = (data) => {
				const payload = data && data.detail ? data.detail : data;
				if (_updateCustomerInstance && typeof _updateCustomerInstance.handleOpen === "function") {
					_updateCustomerInstance.handleOpen(payload);
				}
			};

			if (bus && typeof bus.on === "function") {
				bus.on("open_update_customer", handler);
			} else if (typeof window !== "undefined") {
				window.addEventListener("open_update_customer", handler);
			}
			_updateCustomerListenerRegistered = true;
		}

		// other event listeners
		if (this.eventBus && typeof this.eventBus.on === "function") {
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
				this.country = (this.pos_profile && this.pos_profile.posa_default_country) || "Pakistan";
			});
			this.eventBus.on("payments_register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
				this.country = (this.pos_profile && this.pos_profile.posa_default_country) || "Pakistan";
			});
		}

		// bootstrap lists & defaults
		this.getCustomerGroups();
		this.getCustomerTerritorys();
		this.getGenders();
		this.group = frappe.defaults.get_user_default("Customer Group");
		this.territory = frappe.defaults.get_user_default("Territory");
	},
	beforeUnmount() {
		_updateCustomerInstance = null;
		_updateCustomerListenerRegistered = false;
	},
};
</script>

<style scoped>
/* Dark mode input styling */
:deep([data-theme="dark"]) .dark-field,
:deep(.v-theme--dark) .dark-field,
::v-deep([data-theme="dark"]) .dark-field,
::v-deep(.v-theme--dark) .dark-field {
	background-color: #1e1e1e !important;
}

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
	color: #fff !important;
}

:deep([data-theme="dark"]) .dark-field :deep(.v-field__overlay),
:deep(.v-theme--dark) .dark-field :deep(.v-field__overlay),
::v-deep([data-theme="dark"]) .dark-field .v-field__overlay,
::v-deep(.v-theme--dark) .dark-field .v-field__overlay {
	background-color: #1e1e1e !important;
}
</style>
