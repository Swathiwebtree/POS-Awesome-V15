<template>
	<v-card
		:class="['cards mb-0 mt-3 py-2 px-3 rounded-lg resizable', isDarkTheme ? '' : 'bg-grey-lighten-4']"
		:style="(isDarkTheme ? 'background-color:#1E1E1E;' : '') + 'resize: vertical; overflow: auto;'"
	>
		<v-row dense>
			<!-- Summary Info -->
			<v-col cols="12" md="7">
				<v-row dense>
					<!-- Total Qty -->
					<v-col cols="6">
						<v-text-field
							:model-value="formatFloat(total_qty, hide_qty_decimals ? 0 : undefined)"
							:label="frappe._('Total Qty')"
							prepend-inner-icon="mdi-format-list-numbered"
							variant="solo"
							density="compact"
							readonly
							color="accent"
						/>
					</v-col>

					<!-- Additional Discount (Amount or Percentage) -->
					<v-col cols="6" v-if="!pos_profile.posa_use_percentage_discount">
						<v-text-field
							:model-value="additional_discount"
							@update:model-value="handleAdditionalDiscountUpdate"
							@change="apply_additional_discount"
							:label="frappe._('Additional Discount')"
							prepend-inner-icon="mdi-cash-minus"
							variant="solo"
							density="compact"
							color="warning"
							:prefix="currencySymbol(pos_profile.currency)"
							:disabled="
								!pos_profile.posa_allow_user_to_edit_additional_discount ||
								!!discount_percentage_offer_name
							"
							class="summary-field"
						/>
					</v-col>

					<v-col cols="6" v-else>
						<v-text-field
							:model-value="additional_discount_percentage"
							@update:model-value="handleAdditionalDiscountPercentageUpdate"
							@change="apply_additional_discount"
							:rules="[isNumber]"
							:label="frappe._('Additional Discount %')"
							suffix="%"
							prepend-inner-icon="mdi-percent"
							variant="solo"
							density="compact"
							color="warning"
							:disabled="
								!pos_profile.posa_allow_user_to_edit_additional_discount ||
								!!discount_percentage_offer_name
							"
							class="summary-field"
						/>
					</v-col>

					<!-- Items Discount -->
					<v-col cols="6">
						<v-text-field
							:model-value="formatCurrency(total_items_discount_amount)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Items Discounts')"
							prepend-inner-icon="mdi-tag-minus"
							variant="solo"
							density="compact"
							color="warning"
							readonly
							class="summary-field"
						/>
					</v-col>

					<!-- Total -->
					<v-col cols="6">
						<v-text-field
							:model-value="formatCurrency(subtotal)"
							:prefix="currencySymbol(displayCurrency)"
							:label="frappe._('Total')"
							prepend-inner-icon="mdi-cash"
							variant="solo"
							density="compact"
							readonly
							color="success"
							class="summary-field"
						/>
					</v-col>
				</v-row>
			</v-col>

			<!-- Action Buttons -->
			<v-col cols="12" md="5">
				<v-row dense>
					<!-- Top Buttons -->
					<v-col cols="6">
						<v-btn
							block
							color="white"
							outline="blue"
							theme="dark"
							prepend-icon="mdi-content-save"
							@click="handleSaveAndClear"
							class="summary-outline-btn blue-outline"
							:loading="saveLoading"
						>
							{{ __("Save & Clear") }}
						</v-btn>
					</v-col>

					<v-col cols="6">
						<v-btn
							block
							color="white"
							outline="red"
							theme="dark"
							prepend-icon="mdi-file-document"
							@click="handleLoadDrafts"
							class="summary-outline-btn orange-outline"
							:loading="loadDraftsLoading"
						>
							{{ __("Load Drafts") }}
						</v-btn>
					</v-col>

					<!-- Loyalty Points Button -->
					<v-col cols="12">
						<v-btn
							block
							color="purple"
							theme="dark"
							prepend-icon="mdi-star"
							@click="handleLoyaltyPoints"
							class="summary-btn"
							:loading="loyaltyLoading"
						>
							{{ __("Loyalty Points") }}
						</v-btn>
					</v-col>

					<v-col cols="6" v-if="pos_profile.custom_allow_select_sales_order == 1">
						<v-btn
							block
							color="info"
							theme="dark"
							prepend-icon="mdi-book-search"
							@click="handleSelectOrder"
							class="summary-btn"
							:loading="selectOrderLoading"
						>
							{{ __("Select S.O") }}
						</v-btn>
					</v-col>

					<v-col cols="6" v-if="pos_profile.posa_allow_return == 1">
						<v-btn
							block
							color="secondary"
							theme="dark"
							prepend-icon="mdi-backup-restore"
							@click="handleOpenReturns"
							class="summary-btn"
							:loading="returnsLoading"
						>
							{{ __("Sales Return") }}
						</v-btn>
					</v-col>

					<v-col cols="6" v-if="pos_profile.posa_allow_print_draft_invoices">
						<v-btn
							block
							color="primary"
							theme="dark"
							prepend-icon="mdi-printer"
							@click="handlePrintDraft"
							class="summary-btn"
							:loading="printLoading"
						>
							{{ __("Print Draft") }}
						</v-btn>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Full width bottom row: Cancel Sale & PAY -->
		<v-row dense class="mt-4">
			<v-col cols="6">
				<v-btn
					block
					color="error"
					theme="dark"
					@click="handleCancelSale"
					class="summary-btn"
					:loading="cancelLoading"
					style="display: flex; align-items: center; justify-content: center"
				>
					<v-icon left size="18">mdi-close-circle</v-icon>
					{{ __("CANCEL SALE") }}
				</v-btn>
			</v-col>

			<v-col cols="6">
				<v-btn
					block
					color="green darken-2"
					theme="dark"
					@click="handleShowPayment"
					class="summary-btn pay-btn"
					:loading="paymentLoading"
					style="display: flex; align-items: center; justify-content: center"
				>
					<v-icon left size="18">mdi-credit-card</v-icon>
					{{ __("PAY") }}
				</v-btn>
			</v-col>
		</v-row>
	</v-card>
</template>

<script>
export default {
	props: {
		pos_profile: Object,
		total_qty: [Number, String],
		additional_discount: Number,
		additional_discount_percentage: Number,
		total_items_discount_amount: Number,
		subtotal: Number,
		displayCurrency: String,
		formatFloat: Function,
		formatCurrency: Function,
		currencySymbol: Function,
		discount_percentage_offer_name: [String, Number],
		isNumber: Function,
	},
	data() {
		return {
			// Loading states for better UX
			saveLoading: false,
			loadDraftsLoading: false,
			selectOrderLoading: false,
			cancelLoading: false,
			returnsLoading: false,
			printLoading: false,
			paymentLoading: false,
			loyaltyLoading: false,
		};
	},
	emits: [
		"update:additional_discount",
		"update:additional_discount_percentage",
		"update_discount_umount",
		"save-and-clear",
		"load-drafts",
		"select-order",
		"cancel-sale",
		"open-returns",
		"print-draft",
		"show-payment",
	],
	computed: {
		isDarkTheme() {
			return this.$theme?.current === "dark";
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
		// Debounced handlers for better performance
		handleAdditionalDiscountUpdate(value) {
			this.$emit("update:additional_discount", value);
		},

		handleAdditionalDiscountPercentageUpdate(value) {
			this.$emit("update:additional_discount_percentage", value);
		},

		async handleSaveAndClear() {
			this.saveLoading = true;
			try {
				await this.$emit("save-and-clear");
			} finally {
				this.saveLoading = false;
			}
		},

		apply_additional_discount() {
			// Calculate total before discount
			const totalBeforeDiscount = this.subtotal; // or sum of item amounts if you have items array

			let discountAmount = 0;

			if (this.additional_discount_percentage > 0) {
				discountAmount = (totalBeforeDiscount * this.additional_discount_percentage) / 100;
			} else if (this.additional_discount > 0) {
				discountAmount = this.additional_discount;
			}

			// Update totals
			this.total_after_discount = totalBeforeDiscount - discountAmount;

			// Emit event to parent (Invoice.vue) to update discount values
			this.$emit("update:additional_discount", this.additional_discount);
			this.$emit("update:additional_discount_percentage", this.additional_discount_percentage);
			this.$emit("update_discount_umount");

			// Force UI update
			this.$forceUpdate();
		},

		async handleLoadDrafts() {
			this.loadDraftsLoading = true;
			try {
				await this.$emit("load-drafts");
			} finally {
				this.loadDraftsLoading = false;
			}
		},

		async handleLoyaltyPoints() {
			this.loyaltyLoading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.lazer_pos.get_loyalty_points",
					args: {
						customer: this.pos_profile.customer, // or use selected customer UID
					},
				});

				const points = response?.message?.points || 0;

				frappe.show_alert({
					message: `Loyalty Points: ${points}`,
					indicator: "green",
				});
			} catch (err) {
				console.error("Failed to fetch loyalty points:", err);
				frappe.show_alert({
					message: "Error fetching loyalty points",
					indicator: "red",
				});
			} finally {
				this.loyaltyLoading = false;
			}
		},

		async handleSelectOrder() {
			this.selectOrderLoading = true;
			try {
				await this.$emit("select-order");
			} finally {
				this.selectOrderLoading = false;
			}
		},

		async handleCancelSale() {
			this.cancelLoading = true;
			try {
				await this.$emit("cancel-sale");
			} finally {
				this.cancelLoading = false;
			}
		},

		async handleOpenReturns() {
			this.returnsLoading = true;
			try {
				await this.$emit("open-returns");
			} finally {
				this.returnsLoading = false;
			}
		},

		async handlePrintDraft() {
			this.printLoading = true;
			try {
				await this.$emit("print-draft");
			} finally {
				this.printLoading = false;
			}
		},

		async handleShowPayment() {
			this.paymentLoading = true;
			try {
				await this.$emit("show-payment");
			} finally {
				this.paymentLoading = false;
			}
		},
	},
};
</script>

<style scoped>
.cards {
	background-color: #f5f5f5 !important;
	transition: all 0.3s ease;
}

:deep([data-theme="dark"]) .cards,
:deep([data-theme="dark"]) .cards .v-card__underlay,
:deep(.v-theme--dark) .cards,
:deep(.v-theme--dark) .cards .v-card__underlay,
:deep(.cards.v-theme--dark),
:deep(.cards.v-theme--dark) .v-card__underlay,
::v-deep([data-theme="dark"]) .cards,
::v-deep([data-theme="dark"]) .cards .v-card__underlay,
::v-deep(.v-theme--dark) .cards,
::v-deep(.v-theme--dark) .cards .v-card__underlay,
::v-deep(.cards.v-theme--dark),
::v-deep(.cards.v-theme--dark) .v-card__underlay {
	background-color: #1e1e1e !important;
}

.white-text-btn {
	color: white !important;
}

.white-text-btn :deep(.v-btn__content) {
	color: #4169e1 !important;
}

/* Common outline style */
.summary-outline-btn {
	border-width: 2px !important;
	font-weight: 600 !important;
	display: flex;
	align-items: center;
	justify-content: center;
	text-transform: uppercase;
}

/* Blue outline (Save & Clear) */
.blue-outline {
	border-color: #90caf9 !important;
	color: #1976d2 !important;
}

/* Orange outline (Load Drafts) */
.orange-outline {
	border-color: #ffcc80 !important;
	color: #fb8c00 !important;
}

/* Button hover effects */
.summary-outline-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Enhanced button styling with better performance */
.summary-btn {
	transition: all 0.2s ease !important;
	position: relative;
	overflow: hidden;
}

.summary-btn :deep(.v-btn__content) {
	white-space: normal !important;
	transition: all 0.2s ease;
}

.summary-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

.summary-btn:active {
	transform: translateY(0);
}

/* Loyalty Button Styling */
.summary-btn[color="purple"] {
  background: linear-gradient(135deg, #8e24aa, #6a1b9a) !important;
  color: white !important;
  font-weight: 600 !important;
}

.summary-btn[color="purple"]:hover {
  background: linear-gradient(135deg, #9c27b0, #7b1fa2) !important;
  box-shadow: 0 4px 12px rgba(142, 36, 170, 0.3) !important;
}

/* Special styling for the PAY button */
.pay-btn {
	font-weight: 600 !important;
	font-size: 1.1rem !important;
	background: linear-gradient(135deg, #4caf50, #45a049) !important;
	box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
}

.pay-btn:hover {
	background: linear-gradient(135deg, #45a049, #3d8b40) !important;
	box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
	transform: translateY(-2px);
}

/* Enhanced field styling */
.summary-field {
	transition: all 0.2s ease;
}

.summary-field:hover {
	transform: translateY(-1px);
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Responsive optimizations */
@media (max-width: 768px) {
	.summary-btn {
		font-size: 0.875rem !important;
		padding: 8px 12px !important;
	}

	.pay-btn {
		font-size: 1rem !important;
	}

	.summary-field {
		font-size: 0.875rem;
	}
}

@media (max-width: 480px) {
	.summary-btn {
		font-size: 0.8rem !important;
		padding: 6px 8px !important;
	}

	.pay-btn {
		font-size: 0.95rem !important;
	}
}

/* Loading state animations */
.summary-btn:deep(.v-btn__loader) {
	opacity: 0.8;
}

/* Dark theme enhancements */
:deep([data-theme="dark"]) .summary-btn,
:deep(.v-theme--dark) .summary-btn {
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

:deep([data-theme="dark"]) .summary-btn:hover,
:deep(.v-theme--dark) .summary-btn:hover {
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}
</style>
