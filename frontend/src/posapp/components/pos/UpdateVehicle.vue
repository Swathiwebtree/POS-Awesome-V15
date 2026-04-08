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
									hide-details="auto"
									class="dark-field"
									v-model="vehicle_no"
									:error="!!vehicle_no_error"
									:error-messages="vehicle_no_error"
									@update:modelValue="onVehicleNoInput"
									@blur="onVehicleNoBlur"
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
									:item-title="getCustomerDisplayLabel"
									item-value="name"
									:loading="loading_customers"
									@update:search="search_customers"
									clearable
								>
									<template #item="{ props, item }">
										<v-list-item v-bind="props">
											<v-list-item-title>
												{{ getCustomerDisplayLabel(item.raw) }}
											</v-list-item-title>
											<v-list-item-subtitle v-if="item.raw.mobile_no">
												{{ item.raw.mobile_no }}
											</v-list-item-subtitle>
										</v-list-item>
									</template>

									<template #selection="{ item }">
										<span>{{ getCustomerDisplayLabel(item.raw) }}</span>
									</template>

									<template #no-data>
										<div class="pa-2 text-center text-caption text-medium-emphasis">
											{{ __("No customers found. Start typing to search.") }}
										</div>
									</template>
								</v-autocomplete>
							</v-col>

							<v-col cols="6">
								<v-autocomplete
									density="compact"
									color="primary"
									:label="frappe._('Make') + ' *'"
									v-model="make"
									:items="make_list"
									:loading="loading_makes"
									@update:search="onMakeSearch"
									hide-details
									clearable
								>
									<template #no-data>
										<div class="pa-2 text-center text-caption text-medium-emphasis">
											{{ __("No makes found. Type to add a new one.") }}
										</div>
									</template>
								</v-autocomplete>
							</v-col>

							<v-col cols="6">
								<v-text-field
									density="compact"
									color="primary"
									:label="frappe._('Model No') + ' *'"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									class="dark-field"
									v-model="model"
								/>
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
									:label="frappe._('Mobile No') + ' *'"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details="auto"
									class="dark-field"
									v-model="mobile_no"
									:maxlength="currentMobileRuleLength"
									type="tel"
									inputmode="numeric"
									:error="!!mobile_no_error"
									:error-messages="mobile_no_error"
									@update:modelValue="onMobileInput"
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
import {
	GCC_PHONE_RULES,
	resolveGccIso,
	toGccE164,
	toGccNationalDigits,
	validateGccNational,
} from "../../utils/phone";
let _updateVehicleInstance = null;
let _updateVehicleListenerRegistered = false;

export default {
	data: () => ({
		vehicleDialog: false,
		loading: false,
		vehicle_id: null,
		vehicle_no: "",
		vehicle_no_error: "",
		customer: "",
		customer_list: [],
		loading_customers: false,

		// New Data Properties for Model List
		loading_makes: false,
		make_list: [],

		make: "",
		model: "", // Holds the selected or typed model name
		mobile_no: "",
		mobile_no_error: "",
		chasis_no: "",
		color: "",
		registration_number: "",
		isPrefilling: false,
		suppressMakeSearch: false,
		selected_country_iso: "BH",
		gcc_rules: GCC_PHONE_RULES,
		gcc_country_aliases: {
			BH: "BH",
			Bahrain: "BH",
			BAHRAIN: "BH",
			KW: "KW",
			Kuwait: "KW",
			KUWAIT: "KW",
			OM: "OM",
			Oman: "OM",
			OMAN: "OM",
			QA: "QA",
			Qatar: "QA",
			QATAR: "QA",
			SA: "SA",
			"Saudi Arabia": "SA",
			"SAUDI ARABIA": "SA",
			AE: "AE",
			UAE: "AE",
			"United Arab Emirates": "AE",
			"UNITED ARAB EMIRATES": "AE",
		},
	}),

	computed: {
		isDarkTheme() {
			return this.$theme && this.$theme.current === "dark";
		},
		currentMobileRuleLength() {
			return this.getCurrentMobileRule().len;
		},
		is_valid() {
			return this.vehicle_no && this.customer;
		},
	},

	watch: {
		async customer(newCustomer) {
			if (this.isPrefilling) {
				return;
			}
			if (!newCustomer) {
				this.mobile_no = "";
				this.selected_country_iso = "BH";
				return;
			}

			try {
				const res = await frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Customer",
						name: newCustomer,
					},
				});

				if (res?.message) {
					const customerMobile =
						res.message.mobile_no || res.message.mobile_number || res.message.phone || "";
					this.selected_country_iso = this.getGccIsoFromCountry(res.message.country);

					// Preserve explicit vehicle mobile in edit mode. Only auto-fill
					// from customer when mobile is currently empty.
					if (!this.mobile_no) {
						this.mobile_no = customerMobile;
						this.normalizeMobileForDisplay();
					}
				}
			} catch (e) {
				console.warn("Failed to fetch customer mobile:", e);
			}
		},
		vehicle_no(newVal) {
			if (!this.isPrefilling) {
				this.validateVehicleNo(newVal);
			}
		},
	},

	methods: {
		onMobileInput(val) {
			const national = toGccNationalDigits(val, this.selected_country_iso, "BH");
			if (national !== this.mobile_no) {
				this.mobile_no = national;
			}
			const result = validateGccNational(this.mobile_no, this.selected_country_iso, "BH");
			if (result.isEmpty) {
				this.mobile_no_error = "";
				return;
			}
			this.mobile_no_error = result.isTooShort ? this.__("Mobile number is too short") : "";
		},
		onVehicleNoInput(val) {
			if (val == null) {
				this.vehicle_no = "";
				this.vehicle_no_error = "";
				return;
			}
			const raw = String(val);
			let cleaned = raw.replace(/[^A-Za-z0-9-]/g, "");
			this.validateVehicleNo(raw, cleaned);
			if (cleaned.length > 8) {
				this.vehicle_no_error = this.__("Only 8 characters required");
				cleaned = cleaned.slice(0, 8);
			}
			if (cleaned !== this.vehicle_no) this.vehicle_no = cleaned;
		},
		onVehicleNoBlur() {
			// Clear inline error when focus leaves the field.
			// Submit validation will still block invalid values.
			this.vehicle_no_error = "";
		},
		normalizeMobileForDisplay() {
			const national = toGccNationalDigits(this.mobile_no, this.selected_country_iso, "BH");
			const canonical = toGccE164(national, this.selected_country_iso, "BH");
			if (!canonical) {
				this.mobile_no = "";
				this.mobile_no_error = "";
				return;
			}
			this.mobile_no = national;
			const result = validateGccNational(this.mobile_no, this.selected_country_iso, "BH");
			this.mobile_no_error = result.isTooShort ? this.__("Mobile number is too short") : "";
		},
		normalizeMobileForSave() {
			return toGccE164(this.mobile_no, this.selected_country_iso, "BH");
		},
		getGccIsoFromCountry(countryValue) {
			return resolveGccIso(countryValue, "BH");
		},
		getCurrentMobileRule() {
			return this.gcc_rules[this.selected_country_iso] || this.gcc_rules.BH;
		},
		validateVehicleNo(rawVal, cleanedVal = null) {
			const raw = String(rawVal || "");
			const cleaned = typeof cleanedVal === "string" ? cleanedVal : raw.replace(/[^A-Za-z0-9-]/g, "");
			if (!raw) {
				this.vehicle_no_error = "";
				return;
			}
			if (raw !== cleaned) {
				if (cleaned.length > 8) {
					this.vehicle_no_error = this.__("Only 8 characters required");
				} else {
					this.vehicle_no_error = this.__(
						"Vehicle Number can contain only letters, numbers, and '-'",
					);
				}
				return;
			}
			if (!/^[A-Za-z0-9-]{1,8}$/.test(cleaned)) {
				this.vehicle_no_error = this.__("Vehicle Number can contain only letters, numbers, and '-'");
				return;
			}
			this.vehicle_no_error = "";
		},
		getCustomerDisplayLabel(customer) {
			if (!customer) return "";
			return customer.custom_display_name || customer.customer_name || customer.name || "";
		},

		async ensureCustomerInList(customerName) {
			if (!customerName) return null;

			const existing = this.customer_list.find((c) => c.name === customerName);
			if (existing) {
				return existing;
			}

			try {
				const res = await frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Customer",
						name: customerName,
					},
				});

				if (!res?.message) {
					return null;
				}

				const customerDoc = {
					name: res.message.name,
					customer_name: res.message.customer_name,
					custom_display_name:
						res.message.custom_display_name || res.message.customer_name || res.message.name,
					mobile_no: res.message.mobile_no || res.message.mobile_number || res.message.phone || "",
					country: res.message.country || "",
				};

				this.customer_list.push(customerDoc);
				return customerDoc;
			} catch (e) {
				console.warn("Failed to fetch customer for dialog:", e);
				return null;
			}
		},

		reset_dialog() {
			this.vehicle_id = null;
			this.vehicle_no = "";
			this.vehicle_no_error = "";
			this.customer = "";
			this.loading = false;
			this.make = "";
			this.model = "";
			this.mobile_no = "";
			this.mobile_no_error = "";
			this.customer_list = [];
			this.chasis_no = "";
			this.color = "";
			this.registration_number = "";
			this.make_list = []; // Reset make list
			this.selected_country_iso = "BH";
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
		async search_makes(search_term = "") {
			this.loading_makes = true;
			try {
				const res = await frappe.call({
					method: "posawesome.posawesome.api.vehicles.get_vehicle_makes",
					args: { search_term, limit: 5000 },
				});

				this.make_list = res.message || [];
			} catch (err) {
				console.error("Make search failed:", err);
				this.make_list = [];
			} finally {
				this.loading_makes = false;
			}
		},

		onMakeSearch(search_term = "") {
			// Vuetify emits `update:search` during programmatic selection/prefill,
			// which was causing the list to be filtered down to only the selected make
			// in Update mode. Ignore those emissions.
			if (this.suppressMakeSearch) {
				return;
			}
			if (search_term && this.make && search_term === this.make) {
				return;
			}
			return this.search_makes(search_term);
		},

		// single entry point to open and populate the dialog
		async open_dialog(payload = {}) {
			this.reset_dialog();
			this.isPrefilling = true;
			this.suppressMakeSearch = true;
			try {
				// pre-load lists (no-op if server returns quickly)
				await Promise.all([this.search_customers(), this.search_makes()]);

				if (payload && payload.name) {
					let fullVehicle = null;
					try {
						const vehicleNo = (payload.vehicle_no || "").trim();
						const customerName = payload.customer || this.customer || "";
						if (vehicleNo && customerName) {
							const fullRes = await frappe.call({
								method: "posawesome.posawesome.api.vehicles.get_vehicles_by_customer",
								args: {
									customer_name: customerName,
									vehicle_no: vehicleNo,
									limit: 1,
								},
							});
							fullVehicle = (fullRes?.message || [])[0] || null;
						}
					} catch (e) {
						console.warn("Failed to fetch full vehicle details for edit dialog:", e);
					}

					const v = fullVehicle || payload;

					// editing an existing vehicle
					this.vehicle_id = payload.name;
					this.vehicle_no = v.vehicle_no || payload.vehicle_no || "";
					this.validateVehicleNo(this.vehicle_no);
					this.customer = v.customer || payload.customer || "";
					this.make = v.make || payload.make || "";
					this.model = v.model || payload.model || "";
					this.mobile_no = v.mobile_no || payload.mobile_no || "";
					this.normalizeMobileForDisplay();
					this.chasis_no = v.chasis_no || payload.chasis_no || "";
					this.color = v.color || payload.color || "";
					this.registration_number = v.registration_number || payload.registration_number || "";

					// Ensure selected make exists in autocomplete list.
					if (this.make && !this.make_list.includes(this.make)) {
						this.make_list.push(this.make);
					}

					// ensure chosen customer exists in the dropdown list
					if (this.customer) {
						const customerDoc = await this.ensureCustomerInList(this.customer);
						if (customerDoc) {
							this.selected_country_iso = this.getGccIsoFromCountry(customerDoc.country);
						}
					}
				} else {
					// payload may include preselected customer or vehicle_no
					if (payload && payload.customer) this.customer = payload.customer;
					if (payload && payload.vehicle_no) this.vehicle_no = payload.vehicle_no;

					if (this.customer) {
						const customerDoc = await this.ensureCustomerInList(this.customer);
						if (customerDoc && !this.mobile_no) {
							this.mobile_no = customerDoc.mobile_no || "";
							this.normalizeMobileForDisplay();
						}
						if (customerDoc) {
							this.selected_country_iso = this.getGccIsoFromCountry(customerDoc.country);
						}
					}
				}
			} finally {
				this.isPrefilling = false;
			}
			// allow `v-autocomplete` to settle after programmatic value assignment
			// before we start responding to search events.
			this.vehicleDialog = true;
			await this.$nextTick();
			this.suppressMakeSearch = false;
		},

		async save_vehicle() {
			if (!this.vehicle_no || !this.customer) {
				frappe.show_alert({
					message: this.__("Please fill in all mandatory fields."),
					indicator: "orange",
				});
				return;
			}
			if (String(this.vehicle_no).length > 8) {
				frappe.show_alert({
					message: this.__("Only 8 characters required"),
					indicator: "red",
				});
				return;
			}
			if (this.vehicle_no && !/^[A-Za-z0-9-]{1,8}$/.test(String(this.vehicle_no))) {
				frappe.show_alert({
					message: this.__("Vehicle Number can contain only letters, numbers, and '-'"),
					indicator: "red",
				});
				return;
			}
			if (this.vehicle_no_error) {
				frappe.show_alert({
					message: this.vehicle_no_error,
					indicator: "red",
				});
				return;
			}
			// Mobile validation
			const normalizedMobile = this.normalizeMobileForSave();
			const mobileValidation = validateGccNational(this.mobile_no, this.selected_country_iso, "BH");
			if (!mobileValidation.national) {
				frappe.show_alert({
					message: this.__("Mobile number is required"),
					indicator: "red",
				});
				return;
			}
			if (!mobileValidation.isComplete) {
				frappe.show_alert({
					message:
						this.__("Mobile number must be exactly") +
						` ${mobileValidation.expectedLength} ` +
						this.__("digits for selected country"),
					indicator: "red",
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
					mobile_no: normalizedMobile || null,
					country: this.selected_country_iso,
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
				let msg = null;
				try {
					const serverMessages =
						err?._server_messages ||
						err?.responseJSON?._server_messages ||
						err?.xhr?.responseJSON?._server_messages;

					if (serverMessages) {
						const msgs = JSON.parse(serverMessages);
						if (Array.isArray(msgs) && msgs.length) {
							const parsed = JSON.parse(msgs[0]);
							msg = parsed?.message || parsed;
						}
					}

					// Fallback: direct message from JSON response
					msg =
						msg ||
						err?.responseJSON?.message ||
						err?.xhr?.responseJSON?.message ||
						err?.message ||
						null;
				} catch (e) {
					msg = err?.message || null;
				}

				frappe.show_alert(
					{
						message: msg || this.__("Failed to save vehicle."),
						indicator: "red",
					},
					5,
				);
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
