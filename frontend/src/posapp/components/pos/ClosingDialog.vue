<template>
	<v-row justify="center">
		<v-dialog v-model="closingDialog" max-width="900px" persistent>
			<v-card elevation="8" class="closing-dialog-card">
				<!-- Enhanced White Header -->
				<v-card-title class="closing-header pa-6">
					<div class="header-content">
						<div class="header-icon-wrapper">
							<v-icon class="header-icon" size="40">mdi-store-clock-outline</v-icon>
						</div>
						<div class="header-text">
							<h3 class="header-title">{{ __("Closing POS Shift") }}</h3>
							<p class="header-subtitle">
								{{ __("Reconcile payment methods and close shift") }}
							</p>
						</div>
					</div>
				</v-card-title>

				<v-divider class="header-divider"></v-divider>

                                <v-card-text class="pa-0 white-background">
                                        <v-container class="pa-6">
                                                <v-row class="mb-6">
                                                        <v-col cols="12" class="pa-1">
                                                                <div class="table-header mb-4">
                                                                        <h4 class="text-h6 text-grey-darken-2 mb-1">
                                                                                {{ __("Shift Overview") }}
                                                                        </h4>
                                                                        <p class="text-body-2 text-grey">
                                                                                {{ __("Review shift totals before submitting the closing entry") }}
                                                                        </p>
                                                                </div>

                                                                <div class="overview-wrapper" v-if="overviewLoading">
                                                                        <v-progress-circular
                                                                                color="primary"
                                                                                indeterminate
                                                                                size="32"
                                                                        ></v-progress-circular>
                                                                </div>

                                                                <div v-else class="overview-wrapper">
                                                                        <v-row class="overview-summary" dense>
                                                                                <v-col cols="12" md="6">
                                                                                        <div class="overview-card">
                                                                                                <div class="overview-label">
                                                                                                        {{ __("Total Invoices") }}
                                                                                                </div>
                                                                                                <div class="overview-value">
                                                                                                        {{ overview?.total_invoices || 0 }}
                                                                                                </div>
                                                                                        </div>
                                                                                </v-col>
                                                                                <v-col cols="12" md="6">
                                                                                        <div class="overview-card">
                                                                                                <div class="overview-label">
                                                                                                        {{ __("Total in Company Currency") }}
                                                                                                </div>
                                                                                                <div class="overview-value">
                                                                                                        <span class="overview-amount">
                                                                                                                {{ currencySymbol(overviewCompanyCurrency) }}
                                                                                                                {{ formatCurrency(overview?.company_currency_total || 0) }}
                                                                                                        </span>
                                                                                                </div>
                                                                                                <div class="overview-subtle">
                                                                                                        {{ overviewCompanyCurrency }}
                                                                                                </div>
                                                                                        </div>
                                                                                </v-col>
                                                                        </v-row>

                                                                        <div class="table-header mt-6 mb-2">
                                                                                <h5 class="text-subtitle-1 text-grey-darken-2 mb-1">
                                                                                        {{ __("Totals by Invoice Currency") }}
                                                                                </h5>
                                                                                <p class="text-body-2 text-grey">
                                                                                        {{ __("Shows the distribution of invoices per currency") }}
                                                                                </p>
                                                                        </div>

                                                                        <div v-if="multiCurrencyTotals.length" class="overview-table-wrapper">
                                                                                <table class="overview-table">
                                                                                        <thead>
                                                                                                <tr>
                                                                                                        <th>{{ __("Currency") }}</th>
                                                                                                        <th class="text-end">
                                                                                                                {{ __("Total") }}
                                                                                                        </th>
                                                                                                        <th class="text-end">
                                                                                                                {{ __("Invoices") }}
                                                                                                        </th>
                                                                                                </tr>
                                                                                        </thead>
                                                                                        <tbody>
                                                                                                <tr v-for="row in multiCurrencyTotals" :key="row.currency">
                                                                                                        <td>{{ row.currency }}</td>
                                                                                                        <td class="text-end">
                                                                                                                <span class="overview-amount">
                                                                                                                        {{ currencySymbol(row.currency || overviewCompanyCurrency) }}
                                                                                                                        {{ formatCurrency(row.total || 0) }}
                                                                                                                </span>
                                                                                                        </td>
                                                                                                        <td class="text-end">{{ row.invoice_count || 0 }}</td>
                                                                                                </tr>
                                                                                        </tbody>
                                                                                </table>
                                                                        </div>
                                                                        <div v-else class="overview-empty text-body-2">
                                                                                {{ __("No invoices recorded for this shift.") }}
                                                                        </div>

                                                                        <div class="table-header mt-6 mb-2">
                                                                                <h5 class="text-subtitle-1 text-grey-darken-2 mb-1">
                                                                                        {{ __("Payments by Mode of Payment") }}
                                                                                </h5>
                                                                                <p class="text-body-2 text-grey">
                                                                                        {{ __("Grouped totals for each payment method and currency") }}
                                                                                </p>
                                                                        </div>

                                                                        <div v-if="paymentsByMode.length" class="overview-table-wrapper">
                                                                                <table class="overview-table">
                                                                                        <thead>
                                                                                                <tr>
                                                                                                        <th>{{ __("Mode of Payment") }}</th>
                                                                                                        <th>{{ __("Currency") }}</th>
                                                                                                        <th class="text-end">
                                                                                                                {{ __("Amount") }}
                                                                                                        </th>
                                                                                                </tr>
                                                                                        </thead>
                                                                                        <tbody>
                                                                                                <tr
                                                                                                        v-for="row in paymentsByMode"
                                                                                                        :key="`${row.mode_of_payment}-${row.currency}`"
                                                                                                >
                                                                                                        <td>{{ row.mode_of_payment }}</td>
                                                                                                        <td>{{ row.currency }}</td>
                                                                                                        <td class="text-end">
                                                                                                                <span class="overview-amount">
                                                                                                                        {{ currencySymbol(row.currency || overviewCompanyCurrency) }}
                                                                                                                        {{ formatCurrency(row.total || 0) }}
                                                                                                                </span>
                                                                                                        </td>
                                                                                                </tr>
                                                                                        </tbody>
                                                                                </table>
                                                                        </div>
                                                                        <div v-else class="overview-empty text-body-2">
                                                                                {{ __("No payments registered for this shift.") }}
                                                                        </div>
                                                                </div>
                                                        </v-col>
                                                </v-row>
                                                <v-row>
                                                        <v-col cols="12" class="pa-1">
                                                                <div class="table-header mb-4">
                                                                        <h4 class="text-h6 text-grey-darken-2 mb-1">
                                                                                {{ __("Payment Reconciliation") }}
									</h4>
									<p class="text-body-2 text-grey">
										{{ __("Verify closing amounts for each payment method") }}
									</p>
								</div>

								<v-data-table
									:headers="headers"
									:items="dialog_data.payment_reconciliation"
									item-key="mode_of_payment"
									class="elevation-0 rounded-lg white-table"
									:items-per-page="itemsPerPage"
									hide-default-footer
									density="compact"
								>
									<template v-slot:item.closing_amount="props">
										<v-text-field
											v-model="props.item.closing_amount"
											:rules="[closingAmountRule]"
											:label="frappe._('Edit')"
											single-line
											counter
											type="number"
											density="compact"
											variant="outlined"
											color="primary"
											class="pos-themed-input"
											hide-details
											:prefix="currencySymbol(pos_profile.currency)"
										></v-text-field>
									</template>
									<template v-slot:item.difference="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{
											item.difference = formatCurrency(
												item.expected_amount - item.closing_amount,
											)
										}}</template
									>
									<template v-slot:item.opening_amount="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(item.opening_amount) }}</template
									>
									<template v-slot:item.expected_amount="{ item }">
										{{ currencySymbol(pos_profile.currency) }}
										{{ formatCurrency(item.expected_amount) }}</template
									>
								</v-data-table>
							</v-col>
						</v-row>
					</v-container>
				</v-card-text>

				<v-divider></v-divider>
                                <v-card-actions class="dialog-actions-container">
                                        <v-spacer></v-spacer>
                                        <v-btn
                                                theme="dark"
                                                @click="close_dialog"
                                                class="pos-action-btn cancel-action-btn"
                                                size="large"
                                                elevation="2"
                                        >
                                                <v-icon start>mdi-close-circle-outline</v-icon>
                                                <span>{{ __("Close") }}</span>
                                        </v-btn>
                                        <v-btn
                                                theme="dark"
                                                @click="submit_dialog"
                                                class="pos-action-btn submit-action-btn"
                                                size="large"
                                                elevation="2"
                                        >
                                                <v-icon start>mdi-check-circle-outline</v-icon>
                                                <span>{{ __("Submit") }}</span>
                                        </v-btn>
                                </v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";
export default {
	mixins: [format],
        data: () => ({
                closingDialog: false,
                itemsPerPage: 20,
                dialog_data: {},
                pos_profile: "",
                overview: null,
                overviewLoading: false,
                headers: [
			{
				title: __("Mode of Payment"),
				value: "mode_of_payment",
				align: "start",
				sortable: true,
			},
			{
				title: __("Opening Amount"),
				align: "end",
				sortable: true,
				value: "opening_amount",
			},
			{
				title: __("Closing Amount"),
				value: "closing_amount",
				align: "end",
				sortable: true,
			},
		],
		closingAmountRule: (v) => {
			if (v === "" || v === null || v === undefined) {
				return true;
			}

			const value = typeof v === "number" ? v : Number(String(v).trim());

			if (!Number.isFinite(value)) {
				return "Please enter a valid number";
			}

			const stringValue = String(v);
			const [integerPart, fractionalPart] = stringValue.split(".");

			if (integerPart.replace(/^-/, "").length > 20) {
				return "Number is too large";
			}

			if (fractionalPart && fractionalPart.length > 2) {
				return "Maximum of 2 decimal places";
			}

			return true;
		},
                pagination: {},
        }),
        watch: {},

        methods: {
                close_dialog() {
                        this.closingDialog = false;
                        this.overview = null;
                        this.overviewLoading = false;
                },
                submit_dialog() {
                        const invalid = (this.dialog_data.payments || []).some((p) =>
                                isNaN(parseFloat(p.closing_amount)),
                        );
			if (invalid) {
				alert(this.__("Invalid closing amount"));
				return;
                        }
                        this.eventBus.emit("submit_closing_pos", this.dialog_data);
                        this.closingDialog = false;
                },
                fetchOverview(openingShift) {
                        this.overviewLoading = true;
                        this.overview = null;
                        if (!openingShift) {
                                this.overviewLoading = false;
                                return;
                        }

                        const normalize = (payload = {}) => ({
                                total_invoices: payload.total_invoices || 0,
                                company_currency:
                                        payload.company_currency || this.pos_profile?.currency || "",
                                company_currency_total: payload.company_currency_total || 0,
                                multi_currency_totals: Array.isArray(payload.multi_currency_totals)
                                        ? payload.multi_currency_totals
                                        : [],
                                payments_by_mode: Array.isArray(payload.payments_by_mode)
                                        ? payload.payments_by_mode
                                        : [],
                        });

                        frappe
                                .call(
                                        "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.get_closing_shift_overview",
                                        {
                                                pos_opening_shift: openingShift,
                                        },
                                )
                                .then((r) => {
                                        this.overview = normalize(r.message || {});
                                })
                                .catch((err) => {
                                        console.error("Failed to load shift overview", err);
                                        this.overview = normalize();
                                })
                                .finally(() => {
                                        this.overviewLoading = false;
                                });
                },
        },

        computed: {
                multiCurrencyTotals() {
                        return Array.isArray(this.overview?.multi_currency_totals)
                                ? this.overview.multi_currency_totals
                                : [];
                },
                paymentsByMode() {
                        return Array.isArray(this.overview?.payments_by_mode)
                                ? this.overview.payments_by_mode
                                : [];
                },
                overviewCompanyCurrency() {
                        return (
                                this.overview?.company_currency ||
                                this.pos_profile?.currency ||
                                this.dialog_data?.currency ||
                                ""
                        );
                },
        },

        created: function () {
                this.eventBus.on("open_ClosingDialog", (data) => {
                        this.closingDialog = true;
                        this.dialog_data = data;
                        this.fetchOverview(data.pos_opening_shift);
                });
                this.eventBus.on("register_pos_profile", (data) => {
			this.pos_profile = data.pos_profile;
			if (!this.pos_profile.hide_expected_amount) {
				this.headers.push({
					title: __("Expected Amount"),
					value: "expected_amount",
					align: "end",
					sortable: false,
				});
				this.headers.push({
					title: __("Difference"),
					value: "difference",
					align: "end",
					sortable: false,
				});
			}
		});
        },
        beforeUnmount() {
                this.eventBus.off("open_ClosingDialog");
                this.eventBus.off("register_pos_profile");
        },
};
</script>

<style scoped>
/* Enhanced Header Styles */
.closing-header {
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
	border-bottom: 1px solid #e0e0e0;
	padding: 24px !important;
}

.header-content {
	display: flex;
	align-items: center;
	gap: 20px;
	width: 100%;
}

.header-icon-wrapper {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 64px;
	height: 64px;
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
	border-radius: 16px;
	box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.header-icon {
	color: white !important;
}

.header-text {
	flex: 1;
}

.header-title {
	font-size: 1.5rem;
	font-weight: 600;
	color: #1a1a1a;
	margin: 0 0 4px 0;
	line-height: 1.2;
}

.header-subtitle {
	font-size: 0.95rem;
	color: #666;
	margin: 0;
	font-weight: 400;
}

.header-divider {
	border-color: #e0e0e0;
}

.white-background {
	background-color: #ffffff;
}

.table-header {
	padding: 0 4px;
}

.white-table {
        background-color: white;
        border: 1px solid #e0e0e0;
}

.overview-wrapper {
        display: flex;
        flex-direction: column;
        gap: 16px;
}

.overview-summary {
        gap: 16px;
}

.overview-card {
        background: var(--pos-card-bg);
        border: 1px solid var(--pos-border);
        border-radius: 12px;
        padding: 16px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 8px;
}

.overview-label {
        font-size: 0.9rem;
        color: var(--pos-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
}

.overview-value {
        font-size: 1.6rem;
        font-weight: 600;
        color: var(--pos-text-primary);
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: baseline;
}

.overview-subtle {
        font-size: 0.85rem;
        color: var(--pos-text-secondary);
}

.overview-amount {
        font-family: "Inter", "Roboto", sans-serif;
        font-weight: 600;
}

.overview-table-wrapper {
        border: 1px solid var(--pos-border);
        border-radius: 12px;
        overflow: hidden;
}

.overview-table {
        width: 100%;
        border-collapse: collapse;
        background: var(--pos-card-bg);
}

.overview-table th,
.overview-table td {
        padding: 12px 16px;
        border-bottom: 1px solid var(--pos-border);
        color: var(--pos-text-primary);
}

.overview-table th {
        font-weight: 600;
        background: var(--pos-table-header-bg, rgba(0, 0, 0, 0.04));
        color: var(--pos-text-secondary);
}

.overview-table tr:last-child td {
        border-bottom: none;
}

.overview-table .text-end {
        text-align: right;
}

.overview-empty {
        padding: 12px 4px;
        color: var(--pos-text-secondary);
}

.overview-wrapper .v-progress-circular {
        align-self: center;
}

/* Action Buttons */
.dialog-actions-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-top: 1px solid #e0e0e0;
	padding: 16px 24px;
	gap: 12px;
}

.pos-action-btn {
	border-radius: 12px;
	text-transform: none;
	font-weight: 600;
	padding: 12px 32px;
	min-width: 120px;
	transition: all 0.3s ease;
	color: white !important;
	/* Add this line */
}

/* Add these new rules: */
.pos-action-btn .v-icon {
	color: white !important;
}

.pos-action-btn span {
	color: white !important;
}

.pos-action-btn:disabled .v-icon,
.pos-action-btn:disabled span {
	color: white !important;
}

.cancel-action-btn {
	background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%) !important;
}

.submit-action-btn {
	background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%) !important;
}

.submit-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 20px rgba(46, 125, 50, 0.4);
}

.cancel-action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 20px rgba(211, 47, 47, 0.4);
}

.submit-action-btn:disabled {
	opacity: 0.6;
	transform: none;
}

/* Theme-aware dialog styling */
.closing-dialog-card,
.closing-header,
.white-background,
.white-table,
.dialog-actions-container {
	background: var(--pos-card-bg) !important;
	color: var(--pos-text-primary) !important;
}

.closing-header {
	border-bottom: 1px solid var(--pos-border);
}

.dialog-actions-container {
	border-top: 1px solid var(--pos-border);
}

/* And the responsive section: */
@media (max-width: 768px) {
        .dialog-actions-container {
                flex-direction: column;
                gap: 12px;
        }

        .pos-action-btn {
                width: 100%;
        }

        .overview-summary {
                flex-direction: column;
        }
}
</style>
