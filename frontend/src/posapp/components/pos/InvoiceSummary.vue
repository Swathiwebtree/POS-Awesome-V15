<template>
	<v-card :class="['cards mb-0 mt-3 py-2 px-3 rounded-lg resizable', isDarkTheme ? '' : 'bg-grey-lighten-4']"
		:style="(isDarkTheme ? 'background-color:#1E1E1E;' : '') + 'resize: vertical; overflow: auto;'">
		<v-row dense class="w-100">
			<v-col cols="12" class="my-2">
				<v-divider />
			</v-col>

			<!-- Totals and Actions Section -->
			<v-col cols="12">
				<v-row dense>
					<!-- Left Side - Summary Fields -->
					<v-col cols="12" md="7">
						<v-row dense>
							<!-- Odometer Reading Field (Only shown when Engine Oil item is present) -->
							<v-col cols="6" v-if="showOdometerField">
								<v-text-field v-model="odometerReading" :label="__('Odometer Reading (km)')"
									prepend-inner-icon="mdi-speedometer" variant="solo" density="compact"
									color="primary" type="number" class="summary-field" :rules="[isNumber]"
									@update:model-value="emitOdometerData" />
							</v-col>
							<!-- Service Employee Selection (for car wash services) -->
							<v-col cols="12" v-if="showEmployeeSelection">
								<v-autocomplete v-model="selectedEmployee" :items="employees"
									:loading="loadingEmployees" :label="__('Select Service Employee')"
									item-title="employee_name" item-value="name"
									prepend-inner-icon="mdi-account-hard-hat" variant="solo" density="compact"
									color="primary" clearable class="summary-field" :custom-filter="employeeFilter"
									@update:model-value="handleEmployeeChange">
									<template v-slot:item="{ props, item }">
										<v-list-item v-bind="props" :title="item.raw.employee_name">
											<template v-slot:prepend>
												<v-avatar size="32" color="primary" class="mr-2">
													<v-img v-if="item.raw.image" :src="item.raw.image" />
													<v-icon v-else color="white">mdi-account</v-icon>
												</v-avatar>
											</template>
											<template v-slot:subtitle>
												<span class="text-caption">
													{{ item.raw.name }}
													<span v-if="item.raw.designation">
														- {{ item.raw.designation }}</span>
												</span>
											</template>
										</v-list-item>
									</template>
									<template v-slot:chip="{ item }">
										<v-chip size="small" color="primary">
											<v-avatar left>
												<v-img v-if="item.raw.image" :src="item.raw.image" />
												<v-icon v-else>mdi-account</v-icon>
											</v-avatar>
											{{ item.raw.employee_name }} ({{ item.raw.name }})
										</v-chip>
									</template>
								</v-autocomplete>
							</v-col>

							<!-- Total Qty -->
							<v-col cols="6">
								<v-text-field :model-value="formatFloat(total_qty, hide_qty_decimals ? 0 : undefined)"
									:label="__('Total Qty')" prepend-inner-icon="mdi-format-list-numbered"
									variant="solo" density="compact" readonly color="accent" class="summary-field" />
							</v-col>

							<!-- Additional Discount -->
							<v-col cols="6" v-if="pos_profile && !pos_profile.posa_use_percentage_discount">
								<v-text-field :model-value="additional_discount"
									@update:model-value="handleAdditionalDiscountUpdate"
									@change="apply_additional_discount" :label="__('Additional Discount')"
									prepend-inner-icon="mdi-cash-minus" variant="solo" density="compact" color="warning"
									:prefix="pos_profile ? currencySymbol(pos_profile.currency) : ''" :disabled="
										!pos_profile ||
										!pos_profile.posa_allow_user_to_edit_additional_discount ||
										!!discount_percentage_offer_name
									" class="summary-field" />
							</v-col>

							<!-- Additional Discount Percentage -->
							<v-col cols="6" v-else-if="pos_profile">
								<v-text-field :model-value="additional_discount_percentage"
									@update:model-value="handleAdditionalDiscountPercentageUpdate"
									@change="apply_additional_discount" :rules="[isNumber]"
									:label="__('Additional Discount %')" suffix="%" prepend-inner-icon="mdi-percent"
									variant="solo" density="compact" color="warning" :disabled="
										!pos_profile.posa_allow_user_to_edit_additional_discount ||
										!!discount_percentage_offer_name
									" class="summary-field" />
							</v-col>

							<!-- Items Discounts -->
							<v-col cols="6">
								<v-text-field :model-value="formatCurrency(total_items_discount_amount)"
									:prefix="currencySymbol(displayCurrency)" :label="__('Items Discounts')"
									prepend-inner-icon="mdi-tag-minus" variant="solo" density="compact" color="warning"
									readonly class="summary-field" />
							</v-col>

							<!-- Total -->
							<v-col cols="6">
								<v-text-field :model-value="formatCurrency(subtotal)"
									:prefix="currencySymbol(displayCurrency)" :label="__('Total')"
									prepend-inner-icon="mdi-cash" variant="solo" density="compact" readonly
									color="success" class="summary-field" />
							</v-col>

							<!-- Frequent Cards Button (LEFT SIDE) -->
							<v-col cols="12">
								<v-btn block color="orange" theme="dark" prepend-icon="mdi-cards"
									@click="handleFrequentCards" class="summary-btn" :loading="frequentCardsLoading">
									<span class="flex-grow-1">{{ __("FREQUENT CARDS") }}</span>
									<v-chip v-if="completedCardsCount > 0" size="small" color="white"
										text-color="orange" class="ml-2">
										{{ completedCardsCount }} {{ __("Free") }}
									</v-chip>
								</v-btn>
							</v-col>
						</v-row>
					</v-col>

					<!-- Right Side - Action Buttons -->
					<v-col cols="12" md="5">
						<v-row dense>
							<!-- Save Button -->
							<v-col cols="12">
								<v-btn block color="info" prepend-icon="mdi-content-save" @click="handleSaveAndClear"
									class="summary-btn" :loading="saveLoading">
									{{ __("SAVE & CLEAR") }}
								</v-btn>
							</v-col>

							<!-- Loyalty Points Button -->
							<v-col cols="12">
								<v-btn block color="purple" theme="dark" prepend-icon="mdi-star"
									@click="handleLoyaltyPoints" class="summary-btn" :loading="loyaltyLoading">
									{{ __("LOYALTY POINTS") }}
								</v-btn>
							</v-col>

							<!-- Available Loyalty Points Display (RIGHT SIDE - BELOW LOYALTY BUTTON) -->
							<v-col cols="12" v-if="loyaltyPoints !== null && selectedCustomerId">
								<v-card class="loyalty-points-display-card" elevation="2">
									<v-card-text class="pa-3">
										<v-row align="center" no-gutters>
											<v-col cols="auto" class="mr-3">
												<v-avatar color="purple" size="40">
													<v-icon color="white" size="24">mdi-star</v-icon>
												</v-avatar>
											</v-col>
											<v-col>
												<p class="text-caption mb-0 text-grey-darken-1">
													{{ __("Available Loyalty Points") }}
												</p>
												<p class="text-h6 font-weight-bold mb-0 text-purple">
													{{ formatFloat(loyaltyPoints, 0) }} pts
												</p>
											</v-col>
											<v-col cols="auto">
												<p class="text-caption text-grey">
													≈ {{ formatCurrency(loyaltyPoints * conversionFactor) }}
												</p>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- Select Sales Order Button (Conditional) -->
							<v-col cols="12" v-if="pos_profile && pos_profile.custom_allow_select_sales_order == 1">
								<v-btn block color="info" theme="dark" prepend-icon="mdi-book-search"
									@click="handleSelectOrder" class="summary-btn" :loading="selectOrderLoading">
									{{ __("SELECT S.O") }}
								</v-btn>
							</v-col>

							<!-- Sales Return Button (Conditional) -->
							<v-col cols="12" v-if="pos_profile && pos_profile.posa_allow_return == 1">
								<v-btn block color="secondary" theme="dark" prepend-icon="mdi-backup-restore"
									@click="handleOpenReturns" class="summary-btn" :loading="returnsLoading">
									{{ __("SALES RETURN") }}
								</v-btn>
							</v-col>

							<!-- Print Draft Button (Conditional) -->
							<v-col cols="12" v-if="pos_profile && pos_profile.posa_allow_print_draft_invoices">
								<v-btn block color="primary" theme="dark" prepend-icon="mdi-printer"
									@click="handlePrintDraft" class="summary-btn" :loading="printLoading">
									{{ __("PRINT DRAFT") }}
								</v-btn>
							</v-col>
						</v-row>
					</v-col>
				</v-row>
			</v-col>

			<!-- Bottom Action Buttons -->
			<v-col cols="12">
				<v-row dense class="mt-4">
					<!-- Cancel Sale Button -->
					<v-col cols="6">
						<v-btn block color="error" theme="dark" @click="handleCancelSale" class="summary-btn"
							:loading="cancelLoading"
							style="display: flex; align-items: center; justify-content: center">
							<v-icon left size="18">mdi-close-circle</v-icon>
							{{ __("CANCEL SALE") }}
						</v-btn>
					</v-col>

					<!-- Pay Button -->
					<v-col cols="6">
						<v-btn block color="green darken-2" theme="dark" @click="handleShowPayment"
							class="summary-btn pay-btn" :loading="paymentLoading"
							style="display: flex; align-items: center; justify-content: center">
							<v-icon left size="18">mdi-credit-card</v-icon>
							{{ __("PAY") }}
						</v-btn>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Loyalty Points Dialog (Redeem Only) -->
		<v-dialog v-model="showLoyaltyDialog" max-width="500px" persistent>
			<v-card :style="isDarkTheme ? 'background-color:#1E1E1E;' : ''">
				<v-card-title class="text-h6 pb-2 pt-4 px-6">
					<v-row align="center" no-gutters>
						<v-icon left color="purple" size="28">mdi-star</v-icon>
						<span class="ml-2">{{ __("Redeem Loyalty Points") }}</span>
						<v-spacer></v-spacer>
						<v-btn icon size="small" variant="text" @click="showLoyaltyDialog = false">
							<v-icon>mdi-close</v-icon>
						</v-btn>
					</v-row>
				</v-card-title>

				<v-divider></v-divider>

				<v-card-text class="px-6 py-4">
					<div v-if="selectedCustomerId && String(selectedCustomerId).length > 0">
						<!-- Customer Info -->
						<p class="text-subtitle-1 mb-3 font-weight-medium">
							{{ customerName }} <span class="text-grey">({{ selectedCustomerId }})</span>
						</p>

						<!-- Available Points Summary -->
						<v-alert variant="tonal" density="comfortable" class="mb-4">
							<v-row align="center" no-gutters>
								<v-col>
									<p class="text-caption mb-1">{{ __("Available Points") }}</p>
									<p class="text-h5 font-weight-bold mb-0">
										{{ formatFloat(loyaltyPoints, 0) }} pts
									</p>
								</v-col>
								<v-col cols="auto">
									<p class="text-caption text-grey mb-1">{{ __("Value") }}</p>
									<p class="text-subtitle-1 font-weight-bold mb-0">
										{{ formatCurrency(loyaltyPoints * conversionFactor) }}
									</p>
								</v-col>
							</v-row>
						</v-alert>

						<!-- Redeem Points Input -->
						<v-text-field v-model="pointsToRedeem" :label="__('Points to Redeem')"
							prepend-inner-icon="mdi-star-minus" variant="outlined" density="comfortable" color="purple"
							type="number" :rules="[
								isNumber,
								(v) => v <= loyaltyPoints || __('Cannot redeem more than available points'),
								(v) => v >= 0 || __('Points must be positive'),
							]" :hint="__('Enter points to redeem for a discount')" persistent-hint />

						<!-- Redemption Preview -->
						<div v-if="pointsToRedeem > 0" class="mt-3 pa-3 redemption-preview">
							<v-row dense align="center">
								<v-col cols="6">
									<p class="text-caption mb-0 text-grey">{{ __("Points") }}</p>
									<p class="text-subtitle-1 font-weight-bold mb-0">
										{{ formatFloat(pointsToRedeem, 0) }} pts
									</p>
								</v-col>
								<v-col cols="6" class="text-right">
									<p class="text-caption mb-0 text-grey">{{ __("Discount Value") }}</p>
									<p class="text-subtitle-1 font-weight-bold mb-0 text-purple">
										{{ formatCurrency(redemptionValue) }}
									</p>
								</v-col>
							</v-row>
						</div>
					</div>
					<div v-else class="text-center pa-8">
						<v-icon size="64" color="grey-lighten-1">mdi-account-alert</v-icon>
						<p class="text-subtitle-1 mt-3 text-grey">{{ __("No customer selected") }}</p>
					</div>
				</v-card-text>

				<v-divider></v-divider>

				<v-card-actions class="px-6 py-4">
					<v-spacer></v-spacer>
					<v-btn color="error" variant="text" @click="showLoyaltyDialog = false">
						{{ __("Cancel") }}
					</v-btn>
					<v-btn color="purple" variant="flat" :disabled="!isValidRedemption || redeemLoading"
						:loading="redeemLoading" @click="handleRedeemPoints">
						<v-icon left>mdi-check</v-icon>
						{{ __("Apply Redemption") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Frequent Cards Dialog (SEPARATE) -->
		<v-dialog v-model="showFrequentCardsDialog" max-width="700px" persistent scrollable>
			<v-card :style="isDarkTheme ? 'background-color:#1E1E1E;' : ''" class="dialog-card">
				<v-card-title class="text-h6 pb-2 pt-4 px-6 sticky-header">
					<v-row align="center" no-gutters>
						<v-icon left color="orange" size="28">mdi-cards</v-icon>
						<span class="ml-2">{{ __("Frequent Customer Cards") }}</span>
						<v-spacer></v-spacer>
						<v-btn icon size="small" variant="text" @click="showFrequentCardsDialog = false">
							<v-icon>mdi-close</v-icon>
						</v-btn>
					</v-row>
				</v-card-title>

				<v-divider></v-divider>

				<v-card-text class="px-6 py-4 scrollable-content">
					<div v-if="selectedCustomerId && String(selectedCustomerId).length > 0">
						<!-- Customer Info -->
						<p class="text-subtitle-1 mb-4 font-weight-medium">
							{{ customerName }} <span class="text-grey">({{ selectedCustomerId }})</span>
						</p>

						<!-- Loading State -->
						<v-progress-linear v-if="loadingFrequentCards" indeterminate color="orange"
							class="mb-3"></v-progress-linear>

						<!-- Empty State -->
						<div v-else-if="frequentCards.length === 0" class="text-center py-8">
							<v-icon size="64" color="grey-lighten-1">mdi-cards-outline</v-icon>
							<p class="text-subtitle-1 mt-3 text-grey">
								{{ __("No frequent customer cards available") }}
							</p>
							<p class="text-caption text-grey">
								{{ __("Cards will appear here after multiple service visits") }}
							</p>
						</div>

						<!-- Cards Grid -->
						<v-row v-else dense>
							<v-col v-for="card in frequentCards" :key="card.name" cols="12">
								<v-card :class="[
										'frequent-card',
										card.is_expired ? 'expired-card' : '',
										card.visits >= card.required_visits ? 'completed-card' : '',
									]" :elevation="card.visits >= card.required_visits ? 4 : 2" @click="handleCardClick(card)"
									:disabled="card.is_expired || applyingCard">
									<v-card-text class="pa-4">
										<v-row align="center" no-gutters>
											<v-col cols="auto" class="mr-3">
												<v-avatar :color="
														card.is_expired
															? 'grey'
															: card.visits >= card.required_visits
																? 'success'
																: 'orange'
													" size="56">
													<v-icon color="white" size="28">
														{{
														card.visits >= card.required_visits
														? "mdi-gift"
														: "mdi-cards"
														}}
													</v-icon>
												</v-avatar>
											</v-col>
											<v-col>
												<p class="text-subtitle-1 font-weight-bold mb-1">
													{{ card.card_name }}
												</p>
												<p class="text-caption mb-2 text-grey">
													{{ card.service_item_name }}
												</p>

												<!-- Visit Progress -->
												<div class="visit-progress mb-2">
													<v-row dense align="center">
														<v-col cols="auto">
															<v-chip size="small" :color="
																	card.visits >= card.required_visits
																		? 'success'
																		: 'orange'
																">
																{{ card.visits }}/{{ card.required_visits }}
																visits
															</v-chip>
														</v-col>
														<v-col>
															<v-progress-linear :model-value="
																	(card.visits / card.required_visits) * 100
																" :color="
																	card.visits >= card.required_visits
																		? 'success'
																		: 'orange'
																" height="6" rounded></v-progress-linear>
														</v-col>
													</v-row>
												</div>

												<!-- Status & Expiry -->
												<div>
													<v-chip v-if="card.is_expired" size="small" color="error"
														variant="flat">
														<v-icon size="small" left>mdi-clock-alert</v-icon>
														{{ __("Expired") }}
													</v-chip>
													<v-chip v-else-if="card.visits >= card.required_visits" size="small"
														color="success" variant="flat">
														<v-icon size="small" left>mdi-gift</v-icon>
														{{ __("Free Service Available!") }}
													</v-chip>
													<v-chip v-else size="small" color="grey" variant="outlined">
														<v-icon size="small" left>mdi-calendar</v-icon>
														{{ __("Expires") }}:
														{{ formatDate(card.expiry_date) }}
													</v-chip>
												</div>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>
						</v-row>

						<!-- Auto-apply notification -->
						<v-alert v-if="hasCompletedCards" type="success" variant="tonal" density="compact" class="mt-4"
							icon="mdi-information">
							{{
							__(
							"Click on a completed card to add the free service to your invoice automatically",
							)
							}}
						</v-alert>
					</div>
					<div v-else class="text-center pa-8">
						<v-icon size="64" color="grey-lighten-1">mdi-account-alert</v-icon>
						<p class="text-subtitle-1 mt-3 text-grey">{{ __("No customer selected") }}</p>
						<p class="text-caption text-grey">
							{{ __("Please select a customer to view their frequent cards") }}
						</p>
					</div>
				</v-card-text>
			</v-card>
		</v-dialog>
	</v-card>
</template>

<script>
export default {
	props: {
		pos_profile: Object,
		total_qty: [Number, String],
		additional_discount: [Number, String],
		additional_discount_percentage: [Number, String],
		total_items_discount_amount: Number,
		subtotal: Number,
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		discount_percentage_offer_name: [String, Number],
		isNumber: Function,
		selectedCustomerId: [String, Number],
		items_group: Array,
		item_group: String,
		active_price_list: String,
		offersCount: [Number, String],
		couponsCount: [Number, String],
		items_view: String,
	},
	data() {
		return {
			saveLoading: false,
			selectOrderLoading: false,
			cancelLoading: false,
			returnsLoading: false,
			printLoading: false,
			paymentLoading: false,
			loyaltyLoading: false,
			showLoyaltyDialog: false,
			loyaltyPoints: null,
			customerName: "",
			pointsToRedeem: 0,
			conversionFactor: 0,
			redeemLoading: false,
			// Frequent Cards
			frequentCards: [],
			loadingFrequentCards: false,
			applyingCard: false,
			showFrequentCardsDialog: false,
			frequentCardsLoading: false,

			employees: [],
			selectedEmployee: null,
			loadingEmployees: false,
			showEmployeeSelection: false,

			showOdometerField: false,
			odometerReading: null,
			vehicleNumber: "",
			mobileNumber: "",
		};
	},
	emits: [
		"update:additional_discount",
		"update:additional_discount_percentage",
		"update:item_group",
		"update:items_view",
		"update_discount_umount",
		"save-and-clear",
		"load-drafts",
		"select-order",
		"cancel-sale",
		"open-returns",
		"print-draft",
		"show-payment",
		"show-offers",
		"show-coupons",
		"apply-frequent-card",
	],
	computed: {
		__() {
			return window.__ || ((str) => str);
		},
		isDarkTheme() {
			return this.$vuetify?.theme?.global?.current?.dark;
		},
		redemptionValue() {
			const points = parseFloat(this.pointsToRedeem) || 0;
			return points * this.conversionFactor;
		},
		isValidRedemption() {
			const points = parseFloat(this.pointsToRedeem);
			return (
				this.selectedCustomerId &&
				points > 0 &&
				points <= this.loyaltyPoints &&
				this.conversionFactor > 0
			);
		},
		hasCompletedCards() {
			return this.frequentCards.some((card) => card.visits >= card.required_visits && !card.is_expired);
		},
		completedCardsCount() {
			return this.frequentCards.filter(
				(card) => card.visits >= card.required_visits && !card.is_expired,
			).length;
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
	watch: {
		selectedCustomerId: {
			handler(newVal) {
				if (newVal) {
					this.fetchLoyaltyPoints();
					this.fetchFrequentCards();
				} else {
					this.loyaltyPoints = null;
					this.customerName = "";
					this.conversionFactor = 0;
					this.frequentCards = [];
				}
			},
			immediate: true,
		},
		total_qty: {
			handler(newVal) {
				this.$forceUpdate();
			},
			immediate: true,
		},
	},
	methods: {
		handleAdditionalDiscountUpdate(value) {
			this.$emit("update:additional_discount", value);
		},

		handleAdditionalDiscountPercentageUpdate(value) {
			this.$emit("update:additional_discount_percentage", value);
		},

		emitOdometerData() {
			const odometerData = {
				custom_has_oil_item: this.showOdometerField ? 1 : 0,
				custom_odometer_reading: this.odometerReading,
				contact_mobile: this.mobileNumber,
				custom_vehicle_no: this.vehicleNumber,
			};

			this.eventBus.emit("update_odometer_data", odometerData);
		},

		clearOdometerFields() {
			this.odometerReading = null;
			this.vehicleNumber = "";
			this.mobileNumber = "";
			this.showOdometerField = false;
		},

		async handleSaveAndClear() {
			//  MANDATORY EMPLOYEE VALIDATION FOR CAR WASH SERVICE
			if (this.showEmployeeSelection && !this.selectedEmployee) {
				frappe.show_alert({
					message: this.__("Please select a service employee before saving."),
					indicator: "red",
				});
				return;
			}
			// 2. MANDATORY ODOMETER VALIDATION
			if (this.showOdometerField) {
				if (!this.odometerValue || isNaN(this.odometerValue) || Number(this.odometerValue) <= 0) {
					frappe.show_alert({
						message: this.__("Please enter a valid odometer reading before saving."),
						indicator: "red",
					});
					return;
				}

				// Emit odometer data only if valid
				this.emitOdometerData();
			}

			this.saveLoading = true;
			try {
				this.$emit("save-and-clear");
				await this.$nextTick();
				await new Promise((resolve) => setTimeout(resolve, 1000));
				this.eventBus.emit("open_drafts_modal");
			} catch (error) {
				console.error("[InvoiceSummary] Error during save:", error);
				frappe.show_alert({
					message: this.__("Error saving invoice"),
					indicator: "red",
				});
			} finally {
				setTimeout(() => {
					this.saveLoading = false;
				}, 500);
			}
		},

		apply_additional_discount() {
			this.$emit("update_discount_umount");
		},

		async fetchLoyaltyPoints() {
			const customerId = this.selectedCustomerId;
			if (!customerId) {
				this.loyaltyPoints = null;
				return;
			}

			this.loyaltyLoading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_info",
					args: { customer: customerId },
				});

				if (response?.message) {
					this.loyaltyPoints = response.message.loyalty_points || 0;
					this.customerName = response.message.customer_name || "";
					this.conversionFactor = response.message.conversion_factor || 0;
					this.pointsToRedeem = 0;
				}
			} catch (err) {
				console.error("Failed to fetch loyalty points:", err);
				this.loyaltyPoints = null;
			} finally {
				this.loyaltyLoading = false;
			}
		},

		async fetchFrequentCards() {
			const customerId = this.selectedCustomerId;
			if (!customerId) {
				this.frequentCards = [];
				return;
			}

			this.loadingFrequentCards = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.frequent_cards.get_customer_frequent_cards",
					args: {
						customer: customerId,
						company: this.pos_profile?.company,
					},
				});

				if (response?.message) {
					this.frequentCards = response.message.map((card) => ({
						...card,
						is_expired: new Date(card.expiry_date) < new Date(),
					}));
				}
			} catch (err) {
				console.error("Failed to fetch frequent cards:", err);
			} finally {
				this.loadingFrequentCards = false;
			}
		},

		async handleLoyaltyPoints() {
			if (!this.selectedCustomerId || String(this.selectedCustomerId).trim().length === 0) {
				frappe.show_alert({ message: this.__("Please select a customer first"), indicator: "red" });
				return;
			}

			this.loyaltyLoading = true;
			try {
				await this.fetchLoyaltyPoints();
				this.pointsToRedeem = 0;
				this.showLoyaltyDialog = true;
			} finally {
				this.loyaltyLoading = false;
			}
		},

		async handleFrequentCards() {
			if (!this.selectedCustomerId || String(this.selectedCustomerId).trim().length === 0) {
				frappe.show_alert({
					message: this.__("Please select a customer first"),
					indicator: "red",
				});
				return;
			}

			this.frequentCardsLoading = true;
			try {
				await this.fetchFrequentCards();
				this.showFrequentCardsDialog = true;
			} finally {
				this.frequentCardsLoading = false;
			}
		},

		async handleSelectOrder() {
			this.selectOrderLoading = true;
			try {
				this.$emit("select-order");
			} finally {
				setTimeout(() => {
					this.selectOrderLoading = false;
				}, 500);
			}
		},

		async handleRedeemPoints() {
			if (!this.isValidRedemption) {
				return;
			}

			this.redeemLoading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.customers.update_loyalty_points",
					args: {
						customer_name: this.selectedCustomerId,
						company_name: this.pos_profile.company,
						points_amount: this.pointsToRedeem,
						entry_type: "Redeem",
					},
				});

				const result = response?.message;

				if (result?.status === "success") {
					const newDiscountAmount = this.redemptionValue;
					let currentDiscount = parseFloat(this.additional_discount || 0);
					let updatedDiscount = currentDiscount + newDiscountAmount;

					this.$emit("update:additional_discount", updatedDiscount);
					this.apply_additional_discount();

					frappe.show_alert({
						message: this.__(
							`Successfully redeemed ${this.formatFloat(this.pointsToRedeem, 2)} points for a discount of ${this.formatCurrency(newDiscountAmount)}`,
						),
						indicator: "green",
						title: this.__("Redemption Successful"),
					});

					await this.fetchLoyaltyPoints();
					this.pointsToRedeem = 0;
					this.showLoyaltyDialog = false;
				} else {
					frappe.show_alert({
						message: result?.message || this.__("Redemption failed. Please try again."),
						indicator: "red",
						title: this.__("Redemption Failed"),
					});
				}
			} catch (err) {
				console.error("Redemption failed:", err);
				frappe.show_alert({
					message: this.__("An error occurred during redemption."),
					indicator: "red",
				});
			} finally {
				this.redeemLoading = false;
			}
		},

		async handleCardClick(card) {
			// Don't allow clicking on expired cards
			if (card.is_expired) {
				frappe.show_alert({
					message: this.__("This card has expired"),
					indicator: "orange",
				});
				return;
			}

			// Don't allow clicking if not completed
			if (card.visits < card.required_visits) {
				frappe.show_alert({
					message: this.__(
						`Need ${card.required_visits - card.visits} more visits to complete this card`,
					),
					indicator: "blue",
				});
				return;
			}

			// Card is completed - apply the free service!
			this.applyingCard = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.frequent_cards.apply_free_service",
					args: {
						card_name: card.name,
						customer: this.selectedCustomerId,
						service_item: card.service_item,
					},
				});

				if (response?.message?.status === "success") {
					// Emit event to parent to add the item to invoice
					this.$emit("apply-frequent-card", {
						item_code: card.service_item,
						item_name: card.service_item_name,
						service_item_name: card.service_item_name,
						rate: 0,
						qty: 1,
						discount_percentage: 100,
						frequent_card: card.name, // Important: link to card
						name: card.name, // Also pass card name
					});

					frappe.show_alert({
						message: this.__(" Free service added to invoice!"),
						indicator: "green",
					});

					// Refresh cards to show updated status
					await this.fetchFrequentCards();

					// Close dialog
					this.showFrequentCardsDialog = false;
				} else {
					frappe.show_alert({
						message: response?.message?.message || this.__("Failed to apply card"),
						indicator: "red",
					});
				}
			} catch (err) {
				console.error("Failed to apply card:", err);
				frappe.show_alert({
					message: this.__("Failed to apply free service"),
					indicator: "red",
				});
			} finally {
				this.applyingCard = false;
			}
		},

		formatDate(dateStr) {
			if (!dateStr) return "";
			const date = new Date(dateStr);
			return date.toLocaleDateString();
		},

		employeeFilter(value, query, item) {
			if (!query) return true;

			const searchTerm = query.toLowerCase();
			const employeeName = (item.raw.employee_name || "").toLowerCase();
			const employeeCode = (item.raw.name || "").toLowerCase();
			const designation = (item.raw.designation || "").toLowerCase();

			// Extract just the number from employee code (e.g., "HR-EMP-00001" -> "00001" or "1")
			const codeNumber = employeeCode.replace(/[^0-9]/g, "");
			const queryNumber = searchTerm.replace(/[^0-9]/g, "");

			return (
				employeeName.includes(searchTerm) ||
				employeeCode.includes(searchTerm) ||
				designation.includes(searchTerm) ||
				(queryNumber && codeNumber.includes(queryNumber))
			);
		},

		async fetchEmployees() {
			if (!this.pos_profile?.company) {
				console.warn("[InvoiceSummary] No company in POS profile");
				return;
			}

			this.loadingEmployees = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.employees.get_active_employees",
					args: {
						company: this.pos_profile.company,
					},
				});

				if (response?.message) {
					this.employees = response.message;
				} else {
					console.warn("[InvoiceSummary] No employees returned from API");
					this.employees = [];
				}
			} catch (error) {
				console.error("[InvoiceSummary] Failed to fetch employees:", error);
				frappe.show_alert({
					message: this.__("Failed to load employees. Please try again."),
					indicator: "red",
				});
				this.employees = [];
			} finally {
				this.loadingEmployees = false;
			}
		},

		handleEmployeeChange(employeeId) {
			if (!employeeId) {
				// Employee cleared
				this.selectedEmployee = null;
				this.eventBus.emit("employee_selected", {
					employee_id: null,
					employee_name: null,
				});
				return;
			}

			// Find selected employee details
			const employee = this.employees.find((e) => e.name === employeeId);

			if (!employee) {
				console.warn("[InvoiceSummary] Selected employee not found in list:", employeeId);
				return;
			}

			// Emit event to parent component to attach employee to invoice
			this.eventBus.emit("employee_selected", {
				employee_id: employee.name,
				employee_name: employee.employee_name,
				designation: employee.designation,
				department: employee.department,
			});

			// Show confirmation message
			frappe.show_alert({
				message: this.__(`Service employee set to: ${employee.employee_name}`),
				indicator: "green",
			});
		},

		checkIfCarWashService() {

			// Emit event to parent to check items
			this.eventBus.emit("check_items_for_service", {
				callback: (hasCarWashService) => {
					this.showEmployeeSelection = hasCarWashService;

					// Fetch employees if needed and not already loaded
					if (hasCarWashService && this.employees.length === 0) {
						this.fetchEmployees();
					}

					// Clear selection if no longer needed
					if (!hasCarWashService && this.selectedEmployee) {
						this.selectedEmployee = null;
						this.handleEmployeeChange(null);
					}
				},
			});
		},

		async handleExternalEmployeeSelected(payload) {
			// payload may be { employee_id, employee_name } or just employee_id (string)
			if (!payload) {
				this.selectedEmployee = null;
				this.showEmployeeSelection = false;
				return;
			}

			const empId = payload.employee_id || payload;
			const empNameProvided = payload.employee_name || null;

			// show selector
			this.showEmployeeSelection = true;

			// if we already have employees loaded, set selection directly
			if (empNameProvided) {
				// if server gave friendly name, create/ensure employees array entry to show chip
				// (we keep a minimal object, fetchEmployees will refresh full list eventually)
				const exists = this.employees.find((e) => e.name === empId);
				if (!exists) {
					this.employees.unshift({
						name: empId,
						employee_name: empNameProvided,
					});
				}
				this.selectedEmployee = empId;
				return;
			}

			// No friendly name provided — ensure list loaded then set selection
			if (this.employees.length === 0) {
				await this.fetchEmployees();
			}

			// if still not found, try to fetch the single employee explicitly
			let found = this.employees.find((e) => e.name === empId);
			if (!found) {
				try {
					const resp = await frappe.call({
						method: "frappe.client.get",
						args: { doctype: "Employee", name: empId },
					});
					if (resp && resp.message) {
						this.employees.unshift(resp.message);
						found = resp.message;
					}
				} catch (err) {
					console.warn("[InvoiceSummary] Employee single fetch failed", err);
				}
			}

			if (found) {
				this.selectedEmployee = found.name;
				// show toast
				frappe.show_alert({
					message: this.__(`Service employee set to: ${found.employee_name || found.name}`),
					indicator: "green",
				});
			} else {
				// fallback: set id anyway so value exists and user can see placeholder
				this.selectedEmployee = empId;
			}
		},

		async handleCancelSale() {
			this.cancelLoading = true;
			try {
				this.$emit("cancel-sale");
			} finally {
				setTimeout(() => {
					this.cancelLoading = false;
				}, 500);
			}
		},

		async handleOpenReturns() {
			this.returnsLoading = true;
			try {
				this.$emit("open-returns");
			} finally {
				setTimeout(() => {
					this.returnsLoading = false;
				}, 500);
			}
		},

		async handlePrintDraft() {
			this.printLoading = true;
			try {
				this.$emit("print-draft");
			} finally {
				setTimeout(() => {
					this.printLoading = false;
				}, 500);
			}
		},

		async handleShowPayment() {

			if (!this.selectedCustomerId) {
				frappe.show_alert({
					message: this.__("Please select a customer first"),
					indicator: "warning",
				});
				return;
			}

			this.paymentLoading = true;
			try {
				this.eventBus.emit("get_current_invoice_from_component");

				await new Promise((resolve) => {
					const handler = (data) => {
						this.eventBus.off("current_invoice_data", handler);
						resolve();
					};
					this.eventBus.on("current_invoice_data", handler);
					setTimeout(() => {
						this.eventBus.off("current_invoice_data", handler);
						resolve();
					}, 2000);
				});

				this.eventBus.emit("show_payment", "true");
			} catch (error) {
				console.error("[InvoiceSummary] Error:", error);
				frappe.show_alert({
					message: this.__("Error opening payment"),
					indicator: "red",
				});
			} finally {
				this.paymentLoading = false;
			}
		},

		handleShowOffers() {
			this.$emit("show-offers");
		},

		handleShowCoupons() {
			this.$emit("show-coupons");
		},
	},
	mounted() {
		if (this.selectedCustomerId) {
			this.fetchLoyaltyPoints();
			this.fetchFrequentCards();
		}

		// Listen for odometer field visibility
		this.eventBus.on("show_odometer_field", (shouldShow) => {
			this.showOdometerField = shouldShow;

			if (!shouldShow) {
				this.clearOdometerFields();
			}
		});

		// Listen for odometer data from parent (when loading draft)
		this.eventBus.on("load_odometer_data", (data) => {

			if (data) {
				this.showOdometerField = data.custom_has_oil_item === 1;
				this.odometerReading = data.custom_odometer_reading || null;
				this.vehicleNumber = data.custom_vehicle_no || "";
				this.mobileNumber = data.contact_mobile || "";
			}
		});

		// Listen for customer details from Customer component (AUTO-FETCH)
		this.eventBus.on("update_customer_details", (data) => {

			// Auto-populate mobile and vehicle from customer
			this.mobileNumber = data.contact_mobile || "";
			this.vehicleNumber = data.custom_vehicle_no || "";

			// If odometer field is visible, emit the data immediately
			if (this.showOdometerField) {
				this.emitOdometerData();
			}
		});

		// Listen for item additions to check for auto-apply
		this.eventBus.on("item_added_to_invoice", this.checkAutoApplyCard);

		// EMPLOYEE SELECTION LISTENERS
		this.eventBus.on("show_employee_selection", (shouldShow) => {
			this.showEmployeeSelection = shouldShow;

			if (shouldShow && this.employees.length === 0) {
				this.fetchEmployees();
			}
		});

		// Listen for clear employee selection event
		this.eventBus.on("clear_employee_selection", () => {
			this.selectedEmployee = null;
			this.showEmployeeSelection = false;
		});

		// Check initially if we should show employee selection
		this.checkIfCarWashService();

		this.eventBus.on("employee_selected", this.handleExternalEmployeeSelected);
	},
	beforeUnmount() {
		this.eventBus.off("item_added_to_invoice", this.checkAutoApplyCard);
		this.eventBus.off("show_employee_selection");
		this.eventBus.off("clear_employee_selection");
		this.eventBus.off("employee_selected", this.handleExternalEmployeeSelected);
		this.eventBus.off("show_odometer_field");
		this.eventBus.off("load_odometer_data");
		this.eventBus.off("update_customer_details");
	},
};
</script>

<style scoped>
.cards {
	background-color: #f5f5f5 !important;
	transition: all 0.3s ease;
}

:deep([data-theme="dark"]) .cards,
:deep(.v-theme--dark) .cards {
	background-color: #1e1e1e !important;
}

/* Loyalty Points Display Card (OUTSIDE - in summary) */
.loyalty-points-display-card {
	background: linear-gradient(135deg, rgba(156, 39, 176, 0.12), rgba(106, 27, 154, 0.08));
	border: 2px solid rgba(156, 39, 176, 0.3);
	border-radius: 12px !important;
	transition: all 0.3s ease;
}

:deep(.v-theme--dark) .loyalty-points-display-card {
	background: linear-gradient(135deg, rgba(156, 39, 176, 0.2), rgba(106, 27, 154, 0.12));
	border-color: rgba(156, 39, 176, 0.4);
}

.loyalty-points-display-card:hover {
	transform: translateY(-2px);
}

.text-purple {
	color: #8e24aa !important;
}

/* Redemption Preview */
.redemption-preview {
	background: rgba(156, 39, 176, 0.08);
	border-radius: 8px;
	border-left: 4px solid #8e24aa;
}

:deep(.v-theme--dark) .redemption-preview {
	background: rgba(156, 39, 176, 0.15);
}

/* Frequent Cards Styling */
.frequent-card {
	cursor: pointer;
	transition: all 0.3s ease;
	border-radius: 12px !important;
	border: 2px solid transparent;
}

.frequent-card:hover:not(.expired-card):not([disabled]) {
	transform: translateY(-2px);
	border-color: rgba(255, 152, 0, 0.5);
}

.completed-card {
	background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(56, 142, 60, 0.08)) !important;
	border-color: rgba(76, 175, 80, 0.4) !important;
}

.completed-card:hover {
	border-color: rgba(76, 175, 80, 0.7) !important;
}

.expired-card {
	opacity: 0.6;
	cursor: not-allowed;
	filter: grayscale(0.5);
}

.expired-card:hover {
	transform: none;
}

.visit-progress {
	margin-top: 4px;
}

/* Summary Buttons */
.summary-btn {
	transition: all 0.2s ease !important;
	position: relative;
	overflow: hidden;
	height: 44px !important;
	text-transform: none !important;
	font-weight: 600 !important;
}

.summary-btn:hover:not(:disabled) {
	transform: translateY(-1px);
}

.summary-btn[color="purple"] {
	background: linear-gradient(135deg, #8e24aa, #6a1b9a) !important;
	color: white !important;
}

.summary-btn[color="purple"]:hover {
	background: linear-gradient(135deg, #9c27b0, #7b1fa2) !important;
}

.summary-btn[color="orange"] {
	background: linear-gradient(135deg, #ff9800, #f57c00) !important;
	color: white !important;
}

.summary-btn[color="orange"]:hover {
	background: linear-gradient(135deg, #fb8c00, #ef6c00) !important;
}

.pay-btn {
	font-weight: 700 !important;
	font-size: 1.1rem !important;
	background: linear-gradient(135deg, #4caf50, #45a049) !important;
	height: 48px !important;
}

.pay-btn:hover {
	background: linear-gradient(135deg, #45a049, #3d8b40) !important;
	transform: translateY(-2px);
}

.summary-field {
	transition: all 0.2s ease;
}

.summary-field:hover {
	transform: translateY(-1px);
}

/* Dialog Scrolling */
.dialog-card {
	display: flex;
	flex-direction: column;
	max-height: 90vh;
}

.sticky-header {
	position: sticky;
	top: 0;
	z-index: 10;
	background: inherit;
}

:deep(.v-theme--dark) .sticky-header {
	background-color: #1e1e1e;
}

.scrollable-content {
	overflow-y: auto;
	max-height: calc(90vh - 80px);
}

/* Custom scrollbar for dialog */
.scrollable-content::-webkit-scrollbar {
	width: 8px;
}

.scrollable-content::-webkit-scrollbar-track {
	background: rgba(0, 0, 0, 0.05);
	border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb {
	background: rgba(255, 152, 0, 0.3);
	border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb:hover {
	background: rgba(255, 152, 0, 0.5);
}

:deep(.v-theme--dark) .scrollable-content::-webkit-scrollbar-track {
	background: rgba(255, 255, 255, 0.05);
}

:deep(.v-theme--dark) .scrollable-content::-webkit-scrollbar-thumb {
	background: rgba(255, 152, 0, 0.4);
}

:deep(.v-theme--dark) .scrollable-content::-webkit-scrollbar-thumb:hover {
	background: rgba(255, 152, 0, 0.6);
}

/* Responsive Design */
@media (max-width: 960px) {
	.pr-md-2 {
		padding-right: 0 !important;
		padding-bottom: 8px;
	}

	.pl-md-2 {
		padding-left: 0 !important;
	}
}

@media (max-width: 600px) {
	.summary-btn {
		font-size: 0.875rem !important;
		padding: 8px 12px !important;
		height: 40px !important;
	}

	.pay-btn {
		font-size: 1rem !important;
		height: 44px !important;
	}
}
</style>
