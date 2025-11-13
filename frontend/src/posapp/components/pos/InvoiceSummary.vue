<template>
    <v-card 
        :class="['cards mb-0 mt-3 py-2 px-3 rounded-lg resizable', isDarkTheme ? '' : 'bg-grey-lighten-4']"
        :style="(isDarkTheme ? 'background-color:#1E1E1E;' : '') + 'resize: vertical; overflow: auto;'"
    >
        <v-row dense class="w-100">
            <!-- Filter and Action Controls -->
            <!-- <v-col cols="12">
                <v-row no-gutters align="center" justify="center" class="dynamic-spacing-sm">
                    Item Group and Price List
                    <v-col cols="12" class="mb-2">
                        <v-row dense>
                            <v-col cols="12" md="6" class="pr-md-2">
                                <v-select 
                                    :items="items_group" 
                                    :label="__('Items Group')" 
                                    density="compact"
                                    variant="solo" 
                                    hide-details 
                                    :model-value="item_group"
                                    @update:model-value="handleItemGroupUpdate"
                                ></v-select>
                            </v-col>

                            <v-col 
                                cols="12" 
                                md="6" 
                                class="pl-md-2"
                                v-if="pos_profile && pos_profile.posa_enable_price_list_dropdown !== false"
                            >
                                <v-text-field 
                                    density="compact" 
                                    variant="solo" 
                                    color="primary"
                                    :label="__('Price List')" 
                                    hide-details 
                                    :model-value="active_price_list"
                                    readonly
                                ></v-text-field>
                            </v-col>
                        </v-row>
                    </v-col>

                    View Toggle, Offers, Coupons
                    <v-col cols="12" class="mt-2 mb-2">
                        <v-row dense align="center">
                             <v-col cols="12" sm="4" class="py-1">
                                <v-btn-toggle 
                                    :model-value="items_view" 
                                    @update:model-value="handleItemsViewUpdate"
                                    color="primary" 
                                    group 
                                    density="compact" 
                                    rounded
                                    mandatory
                                >
                                    <v-btn size="small" value="list">{{ __("List") }}</v-btn>
                                    <v-btn size="small" value="card">{{ __("Card") }}</v-btn>
                                </v-btn-toggle>
                            </v-col> -->

                            <!-- <v-col cols="12" sm="4" class="py-1">
                                <v-btn 
                                    size="small" 
                                    block 
                                    color="orange" 
                                    variant="text" 
                                    @click="handleShowOffers"
                                    class="action-btn-consistent"
                                >
                                    <v-icon size="small" class="mr-1">mdi-tag-multiple</v-icon>
                                    {{ offersCount }} {{ __("Offers") }}
                                </v-btn>
                            </v-col> -->

                            <!-- <v-col sm="2"></v-col> -->

                            <!-- <v-col cols="12" sm="4" class="py-1 text-right">
                                <v-btn 
                                    size="small"  
                                    color="blue" 
                                    variant="text" 
                                    @click="handleShowCoupons"
                                    class="action-btn-consistent"
                                >
                                    <v-icon size="small" class="mr-1">mdi-ticket-percent</v-icon>
                                    {{ couponsCount }} {{ __("Coupons") }}
                                </v-btn>
                            </v-col> -->
                        <!-- </v-row> -->
                    <!-- </v-col> -->
                <!-- </v-row> -->
            <!-- </v-col> --> 

            <v-col cols="12" class="my-2">
                <v-divider />
            </v-col>

            <!-- Totals and Actions Section -->
            <v-col cols="12">
                <v-row dense>
                    <!-- Left Side - Summary Fields -->
                    <v-col cols="12" md="7">
                        <v-row dense>
                            <!-- Total Qty -->
                            <v-col cols="6">
                                <v-text-field 
                                    :model-value="formatFloat(total_qty, hide_qty_decimals ? 0 : undefined)"
                                    :label="__('Total Qty')" 
                                    prepend-inner-icon="mdi-format-list-numbered"
                                    variant="solo" 
                                    density="compact" 
                                    readonly 
                                    color="accent" 
                                    class="summary-field" 
                                />
                            </v-col>

                            <!-- Additional Discount -->
                            <v-col cols="6" v-if="pos_profile && !pos_profile.posa_use_percentage_discount">
                                <v-text-field 
                                    :model-value="additional_discount"
                                    @update:model-value="handleAdditionalDiscountUpdate"
                                    @change="apply_additional_discount" 
                                    :label="__('Additional Discount')"
                                    prepend-inner-icon="mdi-cash-minus" 
                                    variant="solo" 
                                    density="compact" 
                                    color="warning"
                                    :prefix="pos_profile ? currencySymbol(pos_profile.currency) : ''" 
                                    :disabled="!pos_profile || !pos_profile.posa_allow_user_to_edit_additional_discount || !!discount_percentage_offer_name" 
                                    class="summary-field" 
                                />
                            </v-col>

                            <!-- Additional Discount Percentage -->
                            <v-col cols="6" v-else-if="pos_profile">
                                <v-text-field 
                                    :model-value="additional_discount_percentage"
                                    @update:model-value="handleAdditionalDiscountPercentageUpdate"
                                    @change="apply_additional_discount" 
                                    :rules="[isNumber]"
                                    :label="__('Additional Discount %')" 
                                    suffix="%"
                                    prepend-inner-icon="mdi-percent" 
                                    variant="solo" 
                                    density="compact" 
                                    color="warning"
                                    :disabled="!pos_profile.posa_allow_user_to_edit_additional_discount || !!discount_percentage_offer_name" 
                                    class="summary-field" 
                                />
                            </v-col>

                            <!-- Items Discounts -->
                            <v-col cols="6">
                                <v-text-field 
                                    :model-value="formatCurrency(total_items_discount_amount)"
                                    :prefix="currencySymbol(displayCurrency)" 
                                    :label="__('Items Discounts')"
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
                                    :label="__('Total')"
                                    prepend-inner-icon="mdi-cash" 
                                    variant="solo" 
                                    density="compact" 
                                    readonly
                                    color="success" 
                                    class="summary-field" 
                                />
                            </v-col>

                            <!-- Loyalty Points Display -->
                            <v-col cols="12" v-if="loyaltyPoints !== null">
                                <v-text-field 
                                    :model-value="`${formatFloat(loyaltyPoints, 2)} pts`"
                                    :label="__('Available Loyalty Points')" 
                                    prepend-inner-icon="mdi-star"
                                    variant="solo" 
                                    density="compact" 
                                    readonly 
                                    color="info"
                                    class="summary-field loyalty-points-field" 
                                />
                            </v-col>
                        </v-row>
                    </v-col>

                    <!-- Right Side - Action Buttons -->
                    <v-col cols="12" md="5">
                        <v-row dense>
                            <!-- Save Button -->
                            <v-col cols="12">
                                <v-btn 
                                    block 
                                    color="info"
                                    prepend-icon="mdi-content-save"
                                    @click="handleSaveAndClear" 
                                    class="summary-btn"
                                    :loading="saveLoading"
                                >
                                    {{ __("SAVE & CLEAR") }}
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
                                    {{ __("LOYALTY POINTS") }}
                                </v-btn>
                            </v-col>

                            <!-- Select Sales Order Button (Conditional) -->
                            <v-col cols="12" v-if="pos_profile && pos_profile.custom_allow_select_sales_order == 1">
                                <v-btn 
                                    block 
                                    color="info" 
                                    theme="dark" 
                                    prepend-icon="mdi-book-search"
                                    @click="handleSelectOrder" 
                                    class="summary-btn" 
                                    :loading="selectOrderLoading"
                                >
                                    {{ __("SELECT S.O") }}
                                </v-btn>
                            </v-col>

                            <!-- Sales Return Button (Conditional) -->
                            <v-col cols="12" v-if="pos_profile && pos_profile.posa_allow_return == 1">
                                <v-btn 
                                    block 
                                    color="secondary" 
                                    theme="dark" 
                                    prepend-icon="mdi-backup-restore"
                                    @click="handleOpenReturns" 
                                    class="summary-btn" 
                                    :loading="returnsLoading"
                                >
                                    {{ __("SALES RETURN") }}
                                </v-btn>
                            </v-col>

                            <!-- Print Draft Button (Conditional) -->
                            <v-col cols="12" v-if="pos_profile && pos_profile.posa_allow_print_draft_invoices">
                                <v-btn 
                                    block 
                                    color="primary" 
                                    theme="dark" 
                                    prepend-icon="mdi-printer"
                                    @click="handlePrintDraft" 
                                    class="summary-btn" 
                                    :loading="printLoading"
                                >
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

                    <!-- Pay Button -->
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
            </v-col>
        </v-row>

        <!-- Loyalty Points Dialog -->
        <v-dialog v-model="showLoyaltyDialog" max-width="500px">
            <v-card :style="isDarkTheme ? 'background-color:#1E1E1E;' : ''">
                <v-card-title class="text-h6 pb-0">
                    <v-icon left color="purple">mdi-star</v-icon>
                    {{ __("Loyalty Points") }}
                </v-card-title>
                <v-card-text>
                    <div v-if="selectedCustomerId && String(selectedCustomerId).length > 0">
                        <p class="text-subtitle-1 mb-2">
                            {{ customerName }} ({{ selectedCustomerId }})
                        </p>
                        <v-card class="loyalty-points-display mb-4" flat>
                            <p class="text-subtitle-1 mb-0">{{ __("Available Points") }}:</p>
                            <p class="text-h4 font-weight-bold purple--text mb-0">
                                {{ formatFloat(loyaltyPoints, 2) }} <span class="text-subtitle-1">pts</span>
                            </p>
                        </v-card>

                        <v-text-field 
                            v-model="pointsToRedeem" 
                            :label="__('Points to Redeem')"
                            prepend-inner-icon="mdi-star-minus" 
                            variant="outlined" 
                            density="compact" 
                            color="purple"
                            :rules="[isNumber, v => v <= loyaltyPoints || __('Cannot redeem more than available points')]"
                            :hint="__('Enter points to redeem for a discount on this invoice.')" 
                            persistent-hint 
                        />

                        <p class="text-subtitle-2 mt-3">
                            {{ __("Discount Value") }}:
                            <span class="font-weight-bold purple--text">
                                {{ formatCurrency(redemptionValue) }}
                                ({{ formatFloat(pointsToRedeem, 2) }} x {{ formatFloat(conversionFactor, 4) }})
                            </span>
                        </p>
                    </div>
                    <div v-else class="text-center pa-4">
                        <p class="text-grey">{{ __("No customer selected.") }}</p>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="error" variant="text" @click="showLoyaltyDialog = false">
                        {{ __("Close") }}
                    </v-btn>
                    <v-btn 
                        color="purple" 
                        variant="flat" 
                        :disabled="!isValidRedemption || redeemLoading"
                        :loading="redeemLoading" 
                        @click="handleRedeemPoints"
                    >
                        {{ __("Redeem") }}
                    </v-btn>
                </v-card-actions>
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
    ],
    computed: {
        __() {
            return window.__ || (str => str);
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
                } else {
                    this.loyaltyPoints = null;
                    this.customerName = "";
                    this.conversionFactor = 0;
                }
            },
            immediate: true,
        },
        total_qty: {
            handler(newVal) {
                console.log('[InvoiceSummary] total_qty changed:', newVal);
                // Trigger re-render
                this.$forceUpdate();
            },
            immediate: true,
        },
        subtotal: {
            handler(newVal) {
                console.log('[InvoiceSummary] subtotal changed:', newVal);
                this.$forceUpdate();
            },
            immediate: true,
        },
        total_items_discount_amount: {
            handler(newVal) {
                console.log('[InvoiceSummary] total_items_discount_amount changed:', newVal);
                this.$forceUpdate();
            },
            immediate: true,
        },
        additional_discount: {
            handler(newVal) {
                console.log('[InvoiceSummary] additional_discount changed:', newVal);
                this.$forceUpdate();
            },
            immediate: true,
        },
        additional_discount_percentage: {
            handler(newVal) {
                console.log('[InvoiceSummary] additional_discount_percentage changed:', newVal);
                this.$forceUpdate();
            },
            immediate: true,
        },
    },
    methods: {
        handleItemGroupUpdate(value) {
            console.log('[InvoiceSummary] Item group updated:', value);
            this.$emit("update:item_group", value);
        },

        handleItemsViewUpdate(value) {
            console.log('[InvoiceSummary] Items view toggled to:', value);
            this.$emit("update:items_view", value);
            // Also broadcast via eventBus for real-time updates
            this.eventBus.emit("update:items_view", value);
        },
        
        handleAdditionalDiscountUpdate(value) {
            this.$emit("update:additional_discount", value);
        },

		handleAdditionalDiscountPercentageUpdate(value) {
			this.$emit("update:additional_discount_percentage", value);
		},

        async handleSaveAndClear() {
            console.log('[InvoiceSummary] handleSaveAndClear clicked');
            this.saveLoading = true;
            try {
                // Emit the event to parent Invoice component
                this.$emit("save-and-clear");

                // Wait for parent to process
                await this.$nextTick();
                await new Promise(resolve => setTimeout(resolve, 1000));

                console.log('[InvoiceSummary] Save completed, opening drafts');

                // Open drafts modal after save
                this.eventBus.emit("open_drafts_modal");
            } catch (error) {
                console.error('[InvoiceSummary] Error during save:', error);
                frappe.show_alert({
                    message: this.__('Error saving invoice'),
                    indicator: 'red'
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
                        message: this.__(`Successfully redeemed ${this.formatFloat(this.pointsToRedeem, 2)} points for a discount of ${this.formatCurrency(newDiscountAmount)}`),
                        indicator: "green",
                        title: this.__("Redemption Successful")
                    });

                    this.showLoyaltyDialog = false;
                    await this.fetchLoyaltyPoints();
                } else {
                    // Handle error response
                    frappe.show_alert({
                        message: result?.message || this.__("Redemption failed. Please try again."),
                        indicator: "red",
                        title: this.__("Redemption Failed")
                    });

                    console.error("Redemption error:", result);
                }
            } catch (err) {
                console.error("Redemption failed:", err);
                frappe.show_alert({
                    message: this.__("An error occurred during redemption. See console for details."),
                    indicator: "red"
                });
            } finally {
                this.redeemLoading = false;
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
            console.log('[InvoiceSummary] PAY button clicked');

            if (!this.selectedCustomerId) {
                frappe.show_alert({
                    message: this.__('Please select a customer first'),
                    indicator: 'warning'
                });
                return;
            }

            this.paymentLoading = true;
            try {
                console.log('[InvoiceSummary] Requesting invoice from parent');
                console.log('[InvoiceSummary] Current totals:', {
                    subtotal: this.subtotal,
                    additional_discount: this.additional_discount,
                    total_qty: this.total_qty
                });

                // Request invoice
                this.eventBus.emit('get_current_invoice_from_component');

                // Wait for response
                await new Promise((resolve) => {
                    const handler = (data) => {
                        console.log('[InvoiceSummary] Invoice received:', data.grand_total);
                        this.eventBus.off('current_invoice_data', handler);
                        resolve();
                    };
                    this.eventBus.on('current_invoice_data', handler);
                    setTimeout(() => {
                        this.eventBus.off('current_invoice_data', handler);
                        resolve();
                    }, 2000);
                });

                // Show payment
                console.log('[InvoiceSummary] Emitting show_payment');
                this.eventBus.emit('show_payment', 'true');

            } catch (error) {
                console.error('[InvoiceSummary] Error:', error);
                frappe.show_alert({
                    message: this.__('Error opening payment'),
                    indicator: 'red'
                });
            } finally {
                this.paymentLoading = false;
            }
        },
        
        // FIXED: Offers button handler
        handleShowOffers() {
            console.log('[InvoiceSummary] Show offers clicked');
            this.$emit("show-offers");
        },

        // FIXED: Coupons button handler
        handleShowCoupons() {
            console.log('[InvoiceSummary] Show coupons clicked');
            this.$emit("show-coupons");
        },
    },
    mounted() {
        console.log('[InvoiceSummary] Mounted with items_group:', this.items_group);
        if (this.selectedCustomerId) {
            this.fetchLoyaltyPoints();
        }
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

.action-btn-consistent {
    font-weight: 500 !important;
    text-transform: uppercase;
    transition: all 0.2s ease;
}

.action-btn-consistent:hover {
    transform: translateY(-1px);
}

.summary-btn {
    transition: all 0.2s ease !important;
    position: relative;
    overflow: hidden;
    height: 44px !important;
    text-transform: none !important;
    font-weight: 600 !important;
}

.summary-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

.summary-btn[color="purple"] {
    background: linear-gradient(135deg, #8e24aa, #6a1b9a) !important;
    color: white !important;
}

.summary-btn[color="purple"]:hover {
    background: linear-gradient(135deg, #9c27b0, #7b1fa2) !important;
}

.pay-btn {
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    background: linear-gradient(135deg, #4caf50, #45a049) !important;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    height: 48px !important;
}

.pay-btn:hover {
	background: linear-gradient(135deg, #45a049, #3d8b40) !important;
	box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
	transform: translateY(-2px);
}

.summary-field {
	transition: all 0.2s ease;
}

.summary-field:hover {
    transform: translateY(-1px);
}


.loyalty-points-display {
    padding: 20px;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(106, 27, 154, 0.1));
}

@media (max-width: 960px) {
    .pr-md-2 {
        padding-right: 0 !important;
        padding-bottom: 8px;
    }

    .pl-md-2 {
        padding-left: 0 !important;
    }

    .v-col-sm-4 {
        flex-basis: 100% !important;
        max-width: 100% !important;
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
