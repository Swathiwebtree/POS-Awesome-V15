<template>
	<v-dialog v-model="showDialog" max-width="1000px" persistent transition="dialog-bottom-transition"
		overlay-opacity="0.5">

		<div class="payment-modal-container">
			<div class="payment-content">
				<div class="payment-card-wrapper">
					<!-- MAIN CARD -->
					<v-card :class="['selection mx-auto pa-0 my-0 mt-0', isDarkTheme ? '' : 'bg-grey-lighten-5']"
						:style="isDarkTheme ? 'background-color:#1E1E1E' : ''">
						<!-- Header inside the card -->
						<div class="payments-header">
							<div class="payments-header-left">
								<v-icon class="ml-2 white--text" large>mdi-cash-register</v-icon>
							</div>

							<div class="payments-header-title">
								<div class="text-h6 font-weight-bold white--text">{{ __("Payment") }}</div>
							</div>

							<div class="payments-header-right">
								<v-btn icon @click="closeDialog" class="white--text" aria-label="Close payments dialog">
									<v-icon class="white--text">mdi-close</v-icon>
								</v-btn>
							</div>
						</div>

						<!-- progress bar (absolute at top of card) -->
						<v-progress-linear :active="loading" :indeterminate="loading" absolute location="top"
							color="info"></v-progress-linear>

						<!-- Scrollable content -->
						<div ref="paymentContainer" class="overflow-y-auto pa-2">
							<!-- Payment Summary (Paid, To Be Paid, Change) -->
							<v-row v-if="invoice_doc" class="pa-1" dense>
								<v-col cols="7">
									<v-text-field variant="solo" color="primary" :label="frappe._('Paid Amount')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details v-model="total_payments_display" readonly
										:prefix="currencySymbol(invoice_doc.currency)" density="compact"
										@click="showPaidAmount"></v-text-field>
								</v-col>
								<v-col cols="5">
									<v-text-field variant="solo" color="primary" label="To Be Paid"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details v-model="diff_payment_display"
										:prefix="currencySymbol(invoice_doc.currency)" density="compact"
										@focus="showDiffPayment" persistent-placeholder></v-text-field>
								</v-col>

								<!-- Paid Change (if applicable) -->
								<v-col cols="7" v-if="credit_change > 0 && !invoice_doc.is_return">
									<v-text-field variant="solo" color="primary" :label="frappe._('Paid Change')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										:model-value="formatCurrency(paid_change)"
										:prefix="currencySymbol(invoice_doc.currency)" :rules="paid_change_rules"
										density="compact" readonly type="text" @click="showPaidChange"></v-text-field>
								</v-col>

								<!-- Credit Change (if applicable) -->
								<v-col cols="5" v-if="credit_change > 0 && !invoice_doc.is_return">
									<v-text-field variant="solo" color="primary" :label="frappe._('Credit Change')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										:model-value="formatCurrency(credit_change)"
										:prefix="currencySymbol(invoice_doc.currency)" density="compact" type="text"
										@change="
									setFormatedCurrency(this, 'credit_change', null, false, $event);
									updateCreditChange(this.credit_change);
								"></v-text-field>
								</v-col>
							</v-row>

							<v-divider></v-divider>

							<!-- Payment Inputs (All Payment Methods) -->
							<div v-if="is_cashback">
								<v-row class="payments pa-1" v-for="payment in invoice_doc.payments"
									:key="payment.name">
									<v-col cols="6" v-if="!is_mpesa_c2b_payment(payment)">
										<v-text-field density="compact" variant="solo" color="primary"
											:label="frappe._(payment.mode_of_payment)"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
											hide-details :model-value="formatCurrency(payment.amount)"
											@change="setFormatedCurrency(payment, 'amount', null, false, $event)"
											:rules="[
										isNumber,
										(v) =>
											!payment.mode_of_payment.toLowerCase().includes('cash') ||
											this.is_credit_sale ||
											v >=
												(this.invoice_doc.rounded_total ||
													this.invoice_doc.grand_total) ||
											'Cash payment cannot be less than invoice total when credit sale is off',
									]" :prefix="currencySymbol(invoice_doc.currency)" @focus="set_rest_amount(payment.idx)"
											:readonly="invoice_doc.is_return"></v-text-field>
									</v-col>
									<v-col cols="6" v-if="!is_mpesa_c2b_payment(payment)">
										<v-btn block color="primary" theme="dark" @click="set_full_amount(payment.idx)">
											{{ payment.mode_of_payment }}
										</v-btn>
									</v-col>

									<!-- M-Pesa Payment Button (if payment is M-Pesa) -->
									<v-col cols="12" v-if="is_mpesa_c2b_payment(payment)" class="pl-3">
										<v-btn block color="success" theme="dark" @click="mpesa_c2b_dialog(payment)">
											{{ __("Get Payments") }} {{ payment.mode_of_payment }}
										</v-btn>
									</v-col>

									<!-- Request Payment for Phone Type -->
									<v-col cols="3"
										v-if="payment.type === 'Phone' && payment.amount > 0 && request_payment_field"
										class="pl-1">
										<v-btn block color="success" theme="dark" :disabled="payment.amount === 0"
											@click="request_payment(payment)">
											{{ __("Request") }}
										</v-btn>
									</v-col>
								</v-row>
							</div>

							<v-divider></v-divider>

							<!-- Credit Sale Button - Compact Right-Aligned -->
							<v-row class="pa-1" align="center"
								v-if="pos_profile.posa_allow_credit_sale && !invoice_doc.is_return && selected_customer_is_corporate">
								<v-col cols="6">
									<div class="text-subtitle-1 font-weight-medium pa-2">
										Credit Sale
									</div>
								</v-col>
								<v-col cols="6">
									<v-btn block size="large" :color="is_credit_sale ? 'success' : 'grey'"
										:variant="is_credit_sale ? 'elevated' : 'outlined'" theme="dark"
										@click="toggleCreditSale" class="credit-sale-btn-compact" elevation="2">
										<v-icon left size="20">mdi-credit-card-clock</v-icon>
										<span>{{ is_credit_sale ? 'CREDIT SALE ✓' : 'CREDIT SALE' }}</span>
									</v-btn>
								</v-col>
							</v-row>

							<v-divider></v-divider>

							<!-- Loyalty Points Redemption -->
							<v-row class="payments pa-1"
								v-if="invoice_doc && available_points_amount > 0 && !invoice_doc.is_return">
								<v-col cols="7">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Redeem Loyalty Points')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatCurrency(loyalty_amount)" type="text"
										@change="setFormatedCurrency(this, 'loyalty_amount', null, false, $event)"
										:prefix="currencySymbol(invoice_doc.currency)"></v-text-field>
								</v-col>
								<v-col cols="5">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('You can redeem up to')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatFloat(available_points_amount)"
										:prefix="currencySymbol(invoice_doc.currency)" readonly></v-text-field>
								</v-col>
							</v-row>

							<!-- Customer Credit Redemption -->
							<v-row class="payments pa-1" v-if="
							invoice_doc &&
							available_customer_credit > 0 &&
							!invoice_doc.is_return &&
							redeem_customer_credit
						">
								<v-col cols="7">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Redeemed Customer Credit')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatCurrency(redeemed_customer_credit)" type="text"
										@change="
									setFormatedCurrency(this, 'redeemed_customer_credit', null, false, $event)
								" :prefix="currencySymbol(invoice_doc.currency)" readonly></v-text-field>
								</v-col>
								<v-col cols="5">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('You can redeem credit up to')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatCurrency(available_customer_credit)"
										:prefix="currencySymbol(invoice_doc.currency)" readonly></v-text-field>
								</v-col>
							</v-row>

							<v-divider></v-divider>

							<!-- Invoice Totals (Net, Tax, Total, Discount, Grand, Rounded) -->
							<v-row class="pa-1">
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Net Total')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field"
										:model-value="formatCurrency(invoice_doc.net_total, displayCurrency)" readonly
										:prefix="currencySymbol()" persistent-placeholder></v-text-field>
								</v-col>
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Tax and Charges')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="
									formatCurrency(invoice_doc.total_taxes_and_charges, displayCurrency)
								" readonly :prefix="currencySymbol()" persistent-placeholder></v-text-field>
								</v-col>
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Total Amount')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field" hide-details
										:model-value="formatCurrency(invoice_doc.total, displayCurrency)" readonly
										:prefix="currencySymbol()" persistent-placeholder></v-text-field>
								</v-col>
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary" :label="diff_label"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatCurrency(diff_payment, displayCurrency)"
										readonly :prefix="currencySymbol()" persistent-placeholder></v-text-field>
								</v-col>
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Discount Amount')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										hide-details :model-value="formatCurrency(invoice_doc.discount_amount)" readonly
										:prefix="currencySymbol(invoice_doc.currency)"
										persistent-placeholder></v-text-field>
								</v-col>
								<v-col cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Grand Total')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field" hide-details
										:model-value="formatCurrency(invoice_doc.grand_total)" readonly
										:prefix="currencySymbol(invoice_doc.currency)"
										persistent-placeholder></v-text-field>
								</v-col>
								<v-col v-if="invoice_doc.rounded_total" cols="6">
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Rounded Total')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field" hide-details
										:model-value="formatCurrency(invoice_doc.rounded_total)" readonly
										:prefix="currencySymbol(invoice_doc.currency)"
										persistent-placeholder></v-text-field>
								</v-col>

								<!-- Delivery Date and Address (if applicable) -->
								<v-col cols="6" v-if="pos_profile.posa_allow_sales_order && invoiceType === 'Order'">
									<VueDatePicker v-model="new_delivery_date" model-type="format" format="dd-MM-yyyy"
										:min-date="new Date()" auto-apply :dark="isDarkTheme"
										class="dark-field sleek-field" @update:model-value="update_delivery_date()" />
								</v-col>
								<!-- Shipping Address Selection (if delivery date is set) -->
								<v-col cols="12" v-if="invoice_doc.posa_delivery_date">
									<v-autocomplete density="compact" clearable auto-select-first variant="solo"
										color="primary" :label="frappe._('Address')"
										v-model="invoice_doc.shipping_address_name" :items="addresses"
										item-title="address_title" item-value="name"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										:no-data-text="__('Address not found')" hide-details
										:customFilter="addressFilter" append-icon="mdi-plus"
										@click:append="new_address">
										<template v-slot:item="{ item }">
											<v-list-item>
												<v-list-item-title class="text-primary text-subtitle-1">
													<div v-html="item.address_title"></div>
												</v-list-item-title>
												<v-list-item-subtitle>
													<div v-html="item.address_line1"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.address_line2">
													<div v-html="item.address_line2"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.city">
													<div v-html="item.city"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.state">
													<div v-html="item.state"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.country">
													<div v-html="item.country"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.mobile_no">
													<div v-html="item.mobile_no"></div>
												</v-list-item-subtitle>
												<v-list-item-subtitle v-if="item.address_type">
													<div v-html="item.address_type"></div>
												</v-list-item-subtitle>
											</v-list-item>
										</template>
									</v-autocomplete>
								</v-col>

								<!-- Additional Notes (if enabled in POS profile) -->
								<v-col cols="12" v-if="pos_profile.posa_display_additional_notes">
									<v-textarea class="pa-0 dark-field sleek-field" variant="solo" density="compact"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" clearable color="primary"
										auto-grow rows="2" :label="frappe._('Additional Notes')"
										v-model="invoice_doc.posa_notes"></v-textarea>
								</v-col>
							</v-row>

							<!-- Customer Purchase Order (if enabled in POS profile) -->
							<div v-if="pos_profile.posa_allow_customer_purchase_order">
								<v-divider></v-divider>
								<v-row class="pa-1" justify="center" align="start">
									<v-col cols="6">
										<v-text-field v-model="invoice_doc.po_no" :label="frappe._('Purchase Order')"
											variant="solo" density="compact"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
											clearable color="primary" hide-details></v-text-field>
									</v-col>
									<v-col cols="6">
										<VueDatePicker v-model="new_po_date" model-type="format" format="dd-MM-yyyy"
											:min-date="new Date()" auto-apply :dark="isDarkTheme"
											class="dark-field sleek-field" @update:model-value="update_po_date()" />
										<v-text-field v-model="invoice_doc.po_date"
											:label="frappe._('Purchase Order Date')" readonly variant="solo"
											density="compact" hide-details color="primary"></v-text-field>
									</v-col>
								</v-row>
							</div>

							<v-divider></v-divider>

							<!-- Switches for Write Off and Credit Sale -->
							<v-row class="pa-1" align="start" no-gutters>
								<v-col cols="6" v-if="
							pos_profile.posa_allow_write_off_change &&
							credit_change > 0 &&
							!invoice_doc.is_return
						">
									<v-switch v-model="is_write_off_change" flat
										:label="frappe._('Write Off Difference Amount')" class="my-0 pa-1"></v-switch>
								</v-col>
								<!-- <v-col cols="6"
									v-if="pos_profile.posa_allow_credit_sale && !invoice_doc.is_return && selected_customer_is_corporate">
									<v-chip color="green" class="ma-2" size="large" text-color="white">
										{{ __('CREDIT SALE') }}
									</v-chip>
								</v-col> -->


								<v-col cols="6" v-if="invoice_doc.is_return && pos_profile.use_cashback">
									<v-switch v-model="is_cashback" flat :label="frappe._('Cashback?')"
										class="my-0 pa-1"></v-switch>
								</v-col>
								<v-col cols="6" v-if="invoice_doc.is_return">
									<v-switch v-model="is_credit_return" flat :label="frappe._('Credit Return?')"
										class="my-0 pa-1"></v-switch>
								</v-col>
								<v-col cols="6" v-if="is_credit_sale && false">
									<VueDatePicker v-model="new_credit_due_date" model-type="format" format="dd-MM-yyyy"
										:min-date="new Date()" auto-apply :dark="isDarkTheme"
										class="dark-field sleek-field" @update:model-value="update_credit_due_date()" />
									<v-text-field class="mt-2 dark-field sleek-field" density="compact" variant="solo"
										type="number" min="0" max="365" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										v-model.number="credit_due_days" :label="frappe._('Days until due')"
										hide-details @change="applyDuePreset(credit_due_days)"></v-text-field>
									<div class="mt-1">
										<v-chip v-for="d in credit_due_presets" :key="d" size="small" class="ma-1"
											variant="solo" color="primary" @click="applyDuePreset(d)">
											{{ d }} {{ frappe._("days") }}
										</v-chip>
									</div>
								</v-col>
								<v-col cols="6" v-if="!invoice_doc.is_return && pos_profile.use_customer_credit">
									<v-switch v-model="redeem_customer_credit" flat
										:label="frappe._('Use Customer Credit')" class="my-0 pa-1"
										@update:model-value="get_available_credit(redeem_customer_credit)"></v-switch>
								</v-col>
							</v-row>

							<!-- Customer Credit Details -->
							<div v-if="
						invoice_doc &&
						available_customer_credit > 0 &&
						!invoice_doc.is_return &&
						redeem_customer_credit
					">
								<v-row v-for="(row, idx) in customer_credit_dict" :key="idx">
									<v-col cols="4">
										<div class="pa-2 py-3">{{ row.credit_origin }}</div>
									</v-col>
									<v-col cols="4">
										<v-text-field density="compact" variant="solo" color="primary"
											:label="frappe._('Available Credit')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
											hide-details :model-value="formatCurrency(row.total_credit)" readonly
											:prefix="currencySymbol(invoice_doc.currency)"></v-text-field>
									</v-col>
									<v-col cols="4">
										<v-text-field density="compact" variant="solo" color="primary"
											:label="frappe._('Redeem Credit')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
											hide-details type="text" :model-value="formatCurrency(row.credit_to_redeem)"
											@change="setFormatedCurrency(row, 'credit_to_redeem', null, false, $event)"
											:prefix="currencySymbol(invoice_doc.currency)"></v-text-field>
									</v-col>
								</v-row>
							</div>

							<v-divider></v-divider>

							<!-- Sales Person Selection -->
							<v-row class="pb-0 mb-2" align="start">
								<v-col cols="12">
									<p v-if="sales_persons && sales_persons.length > 0"
										class="mt-1 mb-1 text-subtitle-2">
										{{ sales_persons.length }} sales persons found
									</p>
									<p v-else class="mt-1 mb-1 text-subtitle-2 text-red">No sales persons found</p>
									<v-select density="compact" clearable variant="solo" color="primary"
										:label="frappe._('Sales Person')" v-model="sales_person" :items="sales_persons"
										item-title="title" item-value="value"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										:no-data-text="__('Sales Person not found')" hide-details
										:disabled="readonly"></v-select>
								</v-col>
							</v-row>
						</div>

						<!-- ================= FOOTER MOVED INSIDE CARD ================= -->
						<div class="card-footer">
							<v-row align="start" no-gutters class="button-row">
								<!-- Submit Dropdown Button -->
								<v-col cols="12" class="mb-2">
									<v-menu :teleport="{ to: 'body' }" offset-y :close-on-content-click="true"
										location="top" transition="slide-y-reverse-transition">
										<template v-slot:activator="{ props }">
											<v-btn ref="submitButton" block size="x-large" color="primary" theme="dark"
												v-bind="props" :loading="loading" :disabled="loading || vaildatPayment"
												:class="['submit-btn-main', { 'submit-highlight': highlightSubmit }]"
												elevation="4">
												<v-icon left size="24">mdi-check-circle</v-icon>
												<span class="submit-text">{{ __("SUBMIT") }}</span>
												<v-icon right size="20">mdi-chevron-up</v-icon>
											</v-btn>
										</template>
										<v-list class="submit-menu" elevation="8" density="compact">
											<v-list-item @click="submit" class="menu-item" prepend-icon="mdi-check">
												<v-list-item-title class="menu-title">
													{{ __("Submit Only") }}
												</v-list-item-title>
												<v-list-item-subtitle class="menu-subtitle">
													{{ __("Save invoice without printing") }}
												</v-list-item-subtitle>
											</v-list-item>
											<v-divider></v-divider>
											<v-list-item @click="submit(undefined, false, true)" class="menu-item"
												prepend-icon="mdi-printer-check">
												<v-list-item-title class="menu-title">
													{{ __("Submit & Print") }}
												</v-list-item-title>
												<v-list-item-subtitle class="menu-subtitle">
													{{ __("Save and print receipt") }}
												</v-list-item-subtitle>
											</v-list-item>
										</v-list>
									</v-menu>
								</v-col>

								<!-- Cancel Payment Button -->
								<v-col cols="12">
									<v-btn block size="large" color="error" theme="dark" @click="back_to_invoice"
										class="cancel-btn" elevation="2">
										<v-icon left size="20">mdi-close-circle</v-icon>
										{{ __("Cancel Payment") }}
									</v-btn>
								</v-col>
							</v-row>
						</div>
						<!-- ================= END FOOTER ================= -->

					</v-card>

					<!-- Custom Days Dialog -->
					<v-dialog v-model="custom_days_dialog" max-width="300px">
						<v-card>
							<v-card-title class="text-h6">
								{{ __("Custom Due Days") }}
							</v-card-title>
							<v-card-text class="pa-0">
								<v-container>
									<v-text-field density="compact" variant="solo" type="number" min="0" max="365"
										class="dark-field sleek-field" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										v-model.number="custom_days_value" :label="frappe._('Days')"
										hide-details></v-text-field>
								</v-container>
							</v-card-text>
							<v-card-actions>
								<v-spacer></v-spacer>
								<v-btn color="error" theme="dark" @click="custom_days_dialog = false">
									{{ __("Close") }}
								</v-btn>
								<v-btn color="primary" theme="dark" @click="applyCustomDays">
									{{ __("Apply") }}
								</v-btn>
							</v-card-actions>
						</v-card>
					</v-dialog>

					<!-- Phone Payment Dialog -->
					<v-dialog v-model="phone_dialog" max-width="400px">
						<v-card>
							<v-card-title>
								<span class="text-h5 text-primary">{{ __("Confirm Mobile Number") }}</span>
							</v-card-title>
							<v-card-text class="pa-0">
								<v-container>
									<v-text-field density="compact" variant="solo" color="primary"
										:label="frappe._('Mobile Number')" :bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field" hide-details v-model="invoice_doc.contact_mobile"
										type="number"></v-text-field>
								</v-container>
							</v-card-text>
							<v-card-actions>
								<v-spacer></v-spacer>
								<v-btn color="error" theme="dark" @click="phone_dialog = false">
									{{ __("Close") }}
								</v-btn>
								<v-btn color="primary" theme="dark" @click="request_payment">
									{{ __("Request") }}
								</v-btn>
							</v-card-actions>
						</v-card>
					</v-dialog>

				</div>
			</div>
		</div>
	</v-dialog>
</template>

<script>
/* global frappe, __, get_currency_symbol */
// Importing format mixin for currency and utility functions
import format, { formatUtils } from "../../format";
import {
	saveOfflineInvoice,
	syncOfflineInvoices,
	getPendingOfflineInvoiceCount,
	isOffline,
	getSalesPersonsStorage,
	setSalesPersonsStorage,
	updateLocalStock,
} from "../../../offline/index.js";

import renderOfflineInvoiceHTML from "../../../offline_print_template";
import { silentPrint } from "../../plugins/print.js";

export default {
	// Using format mixin for shared formatting methods
	mixins: [format],
	data() {
		return {
			showDialog: false,
			selected_customer_is_corporate:false,
			loading: false, // UI loading state
			pos_profile: "", // POS profile settings
			pos_settings: "", // POS settings
			invoice_doc: "", // Current invoice document
			stock_settings: "", // Stock settings
			invoiceType: "Invoice", // Type of invoice
			is_return: false, // Is this a return invoice?
			loyalty_amount: 0, // Loyalty points to redeem
			redeemed_customer_credit: 0, // Customer credit to redeem
			credit_change: 0, // Change to be given as credit
			paid_change: 0, // Change to be given as paid
			is_credit_sale: false, // Is this a credit sale?
			is_write_off_change: false, // Write-off for change enabled
			is_cashback: true, // Cashback enabled
			is_credit_return: false, // Is this a credit return?
			redeem_customer_credit: false, // Redeem customer credit?
			customer_credit_dict: [], // List of available customer credits
			paid_change_rules: [], // Validation rules for paid change
			phone_dialog: false, // Show phone payment dialog
			custom_days_dialog: false, // Show custom days dialog
			custom_days_value: null, // Custom days entry
			new_delivery_date: null, // New delivery date value
			new_po_date: null, // New PO date value
			new_credit_due_date: null, // New credit due date value
			credit_due_days: null, // Number of days until due
			credit_due_presets: [7, 14, 30], // Preset options for due days
			customer_info: "", // Customer info
			mpesa_modes: [], // List of available M-Pesa modes
			sales_persons: [], // List of sales persons
			sales_person: "", // Selected sales person
			addresses: [], // List of customer addresses
			is_user_editing_paid_change: false, // User interaction flag
			highlightSubmit: false, // Highlight state for submit button
		};
	},
	computed: {
		// Get currency symbol for given or current currency
		currencySymbol() {
			return (currency) => {
				return get_currency_symbol(currency || this.invoice_doc.currency);
			};
		},
		// Display currency for invoice
		displayCurrency() {
			return this.invoice_doc ? this.invoice_doc.currency : "";
		},
		// Calculate total payments (all methods, loyalty, credit)
		total_payments() {
			let total = 0;
			if (this.invoice_doc && this.invoice_doc.payments) {
				this.invoice_doc.payments.forEach((payment) => {
					// Payment amount is already in selected currency
					total += parseFloat(formatUtils.fromArabicNumerals(String(payment.amount))) || 0;
				});
			}

			// Add loyalty amount (convert if needed)
			if (this.loyalty_amount) {
				// Loyalty points are stored in base currency (PKR)
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert to selected currency (e.g. USD) by dividing
					total += this.flt(
						this.loyalty_amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				} else {
					total += parseFloat(formatUtils.fromArabicNumerals(String(this.loyalty_amount))) || 0;
				}
			}

			// Add redeemed customer credit (convert if needed)
			if (this.redeemed_customer_credit) {
				// Customer credit is stored in base currency (PKR)
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert to selected currency (e.g. USD) by dividing
					total += this.flt(
						this.redeemed_customer_credit / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				} else {
					total +=
						parseFloat(formatUtils.fromArabicNumerals(String(this.redeemed_customer_credit))) ||
						0;
				}
			}

			return this.flt(total, this.currency_precision);
		},

		// Calculate difference between invoice total and payments
		diff_payment() {
			if (!this.invoice_doc) return 0;

			// For multi-currency, use grand_total instead of rounded_total
			let invoice_total;
			if (
				this.pos_profile.posa_allow_multi_currency &&
				this.invoice_doc.currency !== this.pos_profile.currency
			) {
				invoice_total = this.flt(this.invoice_doc.grand_total, this.currency_precision);
			} else {
				invoice_total = this.flt(
					this.invoice_doc.rounded_total || this.invoice_doc.grand_total,
					this.currency_precision,
				);
			}

			// Calculate difference (all amounts are in selected currency)
			let diff = this.flt(invoice_total - this.total_payments, this.currency_precision);

			// For returns, ensure difference is not negative
			if (this.invoice_doc.is_return) {
				return diff >= 0 ? diff : 0;
			}

			return diff >= 0 ? diff : 0;
		},

		// Calculate change to be given back to customer
		credit_change() {
			// For multi-currency, use grand_total instead of rounded_total
			let invoice_total;
			if (
				this.pos_profile.posa_allow_multi_currency &&
				this.invoice_doc.currency !== this.pos_profile.currency
			) {
				invoice_total = this.flt(this.invoice_doc.grand_total, this.currency_precision);
			} else {
				invoice_total = this.flt(
					this.invoice_doc.rounded_total || this.invoice_doc.grand_total,
					this.currency_precision,
				);
			}

			// Calculate change (all amounts are in selected currency)
			let change = this.flt(this.total_payments - invoice_total, this.currency_precision);

			// Ensure change is not negative
			return change > 0 ? change : 0;
		},

		// Label for the difference field (To Be Paid/Change)
		diff_label() {
			return this.diff_payment > 0
				? `To Be Paid (${this.displayCurrency})`
				: `Change (${this.displayCurrency})`;
		},
		// Display formatted total payments
		total_payments_display() {
			return this.formatCurrency(this.total_payments, this.displayCurrency);
		},
		// Display formatted difference payment
		diff_payment_display() {
			return this.formatCurrency(this.diff_payment, this.displayCurrency);
		},
		// Calculate available loyalty points amount in selected currency
		available_points_amount() {
			let amount = 0;
			if (this.customer_info.loyalty_points) {
				// Convert loyalty points to amount in base currency (PKR)
				amount = this.customer_info.loyalty_points * this.customer_info.conversion_factor;

				// Convert to selected currency if needed
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					// Convert PKR to USD by dividing
					amount = this.flt(
						amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				}
			}
			return amount;
		},
		// Calculate total available customer credit
		available_customer_credit() {
			return this.customer_credit_dict.reduce((total, row) => total + this.flt(row.total_credit), 0);
		},
		// Validate if payment can be submitted
		vaildatPayment() {
			if (this.pos_profile.posa_allow_sales_order) {
				if (this.invoiceType === "Order" && !this.invoice_doc.posa_delivery_date) {
					return true;
				}
			}
			return false;
		},
		// Should request payment field be shown?
		request_payment_field() {
			return (
				this.pos_settings?.invoice_fields?.some(
					(el) => el.fieldtype === "Button" && el.fieldname === "request_for_payment",
				) || false
			);
		},
		isDarkTheme() {
			return this.$theme.current === "dark";
		},
	},
	watch: {
		// Watch diff_payment to update paid_change
		diff_payment(newVal) {
			if (!this.is_user_editing_paid_change) {
				this.paid_change = -newVal;
			}
		},
		// Watch paid_change to validate and update credit_change
		paid_change(newVal) {
			const changeLimit = -this.diff_payment;
			if (newVal > changeLimit) {
				this.paid_change = changeLimit;
				this.credit_change = 0;
				this.paid_change_rules = ["Paid change can not be greater than total change!"];
			} else {
				this.paid_change_rules = [];
				this.credit_change = this.flt(newVal - changeLimit, this.currency_precision);
			}
		},
		// Watch loyalty_amount to handle loyalty points redemption
		loyalty_amount(value) {
			if (value > this.available_points_amount) {
				this.invoice_doc.loyalty_amount = 0;
				this.invoice_doc.redeem_loyalty_points = 0;
				this.invoice_doc.loyalty_points = 0;
				this.loyalty_amount = 0;
				this.eventBus.emit("show_message", {
					title: `Loyalty Amount can not be more than ${this.available_points_amount}`,
					color: "error",
				});
			} else {
				this.invoice_doc.loyalty_amount = this.flt(this.loyalty_amount);
				this.invoice_doc.redeem_loyalty_points = 1;
				this.invoice_doc.loyalty_points =
					this.flt(this.loyalty_amount) / this.customer_info.conversion_factor;
			}
		},
		// Watch redeemed_customer_credit to validate
		redeemed_customer_credit(newVal) {
			if (newVal > this.available_customer_credit) {
				this.redeemed_customer_credit = this.available_customer_credit;
				this.eventBus.emit("show_message", {
					title: `You can redeem customer credit up to ${this.available_customer_credit}`,
					color: "error",
				});
			}
		},
		// Recalculate total redeemed credit whenever credit entries change
		customer_credit_dict: {
			handler(newVal) {
				const total = newVal.reduce((sum, row) => sum + this.flt(row.credit_to_redeem || 0), 0);
				this.redeemed_customer_credit = this.flt(total, this.currency_precision);
			},
			deep: true,
		},
		// Watch sales_person to update sales_team
		sales_person(newVal) {
			if (newVal) {
				this.invoice_doc.sales_team = [
					{
						sales_person: newVal,
						allocated_percentage: 100,
					},
				];
			} else {
				this.invoice_doc.sales_team = [];
			}
		},
		selected_customer_is_corporate(newVal) {
			if (newVal) {
				this.is_credit_sale = true;
				this.$nextTick(() => {
					this.reset_cash_payments();
				});
			} else {
				this.is_credit_sale = false;
			}
		},
		// Watch is_credit_sale to reset cash payments
		is_credit_sale(newVal) {
			if (!this.invoice_doc || !this.invoice_doc.payments) return;

			if (newVal) {
				// If credit sale is enabled, set cash payment to 0
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment && payment.mode_of_payment.toLowerCase() === "cash") {
						payment.amount = 0;
					}
				});
			} else {
				// If credit sale is disabled, set cash payment to invoice total
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment && payment.mode_of_payment.toLowerCase() === "cash") {
						payment.amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
					}
				});
			}
		},
		// Watch is_credit_return to toggle cashback payments
		is_credit_return(newVal) {
			if (newVal) {
				this.is_cashback = false;
				// Clear any payment amounts
				this.invoice_doc.payments.forEach((payment) => {
					payment.amount = 0;
					if (payment.base_amount !== undefined) {
						payment.base_amount = 0;
					}
				});
			} else {
				this.is_cashback = true;
				// Ensure default negative payment for returns
				this.ensureReturnPaymentsAreNegative();
			}
		},
	},
	methods: {
		toggleCreditSale() {
			this.is_credit_sale = !this.is_credit_sale;

			if (this.is_credit_sale) {
				// Credit sale activated

				// Set due date automatically (30 days from now)
				this.applyDuePreset(30);

				// Show confirmation message
				this.eventBus.emit("show_message", {
					title: "Credit Sale Activated - Payment will be recorded as credit",
					color: "success",
				});
			} else {
				// Credit sale deactivated

				this.eventBus.emit("show_message", {
					title: "Credit Sale Deactivated - Normal payment mode",
					color: "info",
				});
			}
		},
		// Go back to invoice view and reset customer readonly
		back_to_invoice() {
			this.showDialog = false;
			this.eventBus.emit("show_payment", "false");
			this.eventBus.emit("set_customer_readonly", false);
		},
		// ADD THIS NEW METHOD
		closeDialog() {
			this.showDialog = false;
			this.back_to_invoice();
		},
		// Highlight and focus the submit button when payment screen opens
		handleShowPayment(data) {
			// 1. EMPLOYEE VALIDATION (existing)
			if (this.showEmployeeSelection && !this.selectedEmployee) {
				frappe.show_alert({
					message: this.__("Please select a service employee before proceeding to payment."),
					indicator: "red",
				});
				frappe.utils.play_sound && frappe.utils.play_sound("error");
				return;
			}

			// 2. ODOMETER VALIDATION (new)
			if (this.showOdometerField) {
				if (!this.odometerValue || isNaN(this.odometerValue) || Number(this.odometerValue) <= 0) {
					frappe.show_alert({
						message: this.__("Please enter a valid odometer reading before proceeding to payment."),
						indicator: "red",
					});
					frappe.utils.play_sound && frappe.utils.play_sound("error");
					return;
				}
			}

			// 3. Continue as normal
			if (data === "true") {
				this.$nextTick(() => {
					setTimeout(() => {
						const btn = this.$refs.submitButton;
						const el = btn && btn.$el ? btn.$el : btn;
						if (el) {
							el.scrollIntoView({ behavior: "smooth", block: "center" });
							el.focus();
							this.highlightSubmit = true;
						}
					}, 100);
				});
			} else {
				this.highlightSubmit = false;
			}
		},
		// Reset all cash payments to zero
		reset_cash_payments() {
			if (!this.invoice_doc || !this.invoice_doc.payments) {
				console.warn("[Payment] Cannot reset cash payments - invoice_doc not ready");
				return;
			}

			this.invoice_doc.payments.forEach((payment) => {
				if (payment.mode_of_payment && payment.mode_of_payment.toLowerCase() === "cash") {
					payment.amount = 0;
				}
			});
		},
		// Ensure all payments are negative for return invoices
		ensureReturnPaymentsAreNegative() {
			if (!this.invoice_doc || !this.invoice_doc.is_return || !this.is_cashback) {
				return;
			}
			// Check if any payment amount is set
			let hasPaymentSet = false;
			this.invoice_doc.payments.forEach((payment) => {
				if (Math.abs(payment.amount) > 0) {
					hasPaymentSet = true;
				}
			});
			// If no payment set, set the default one
			if (!hasPaymentSet) {
				const default_payment = this.invoice_doc.payments.find((payment) => payment.default === 1);
				if (default_payment) {
					const amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
					default_payment.amount = -Math.abs(amount);
					if (default_payment.base_amount !== undefined) {
						default_payment.base_amount = -Math.abs(amount);
					}
				}
			}
			// Ensure all set payments are negative
			this.invoice_doc.payments.forEach((payment) => {
				if (payment.amount > 0) {
					payment.amount = -Math.abs(payment.amount);
				}
				if (payment.base_amount !== undefined && payment.base_amount > 0) {
					payment.base_amount = -Math.abs(payment.base_amount);
				}
			});
		},
		// Submit payment after validation
		async submit(event, payment_received = false, print = false) {
			// For return invoices, ensure payment amounts are negative
			if (this.invoice_doc.is_return) {
				this.ensureReturnPaymentsAreNegative();
			}

			// ========== FIXED: Better payment validation ==========
			// Check if at least one payment has an amount entered
			let hasPaymentAmount = false;
			if (this.invoice_doc && this.invoice_doc.payments && this.invoice_doc.payments.length > 0) {
				for (let payment of this.invoice_doc.payments) {
					if (parseFloat(payment.amount) > 0) {
						hasPaymentAmount = true;
						break;
					}
				}
			}

			// If not credit sale and invoice total > 0, need payment
			if (
				!this.is_credit_sale &&
				!this.invoice_doc.is_return &&
				!hasPaymentAmount &&
				(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
			) {
				this.eventBus.emit("show_message", {
					title: `Please enter payment amount`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// ========== END FIX ==========

			// Validate cash payments when credit sale is off
			if (!this.is_credit_sale && !this.invoice_doc.is_return) {
				let has_cash_payment = false;
				let cash_amount = 0;
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.mode_of_payment.toLowerCase().includes("cash")) {
						has_cash_payment = true;
						cash_amount = this.flt(payment.amount);
					}
				});
				if (has_cash_payment && cash_amount > 0) {
					if (
						!this.pos_profile.posa_allow_partial_payment &&
						cash_amount < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
						(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
					) {
						this.eventBus.emit("show_message", {
							title: `Cash payment cannot be less than invoice total when partial payment is not allowed`,
							color: "error",
						});
						frappe.utils.play_sound("error");
						return;
					}
				}
			}
			// Validate partial payments only if not credit sale and invoice total is not zero
			if (
				!this.is_credit_sale &&
				!this.pos_profile.posa_allow_partial_payment &&
				this.total_payments < (this.invoice_doc.rounded_total || this.invoice_doc.grand_total) &&
				(this.invoice_doc.rounded_total || this.invoice_doc.grand_total) > 0
			) {
				this.eventBus.emit("show_message", {
					title: `The amount paid is not complete`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate phone payment
			let phone_payment_is_valid = true;
			if (!payment_received) {
				this.invoice_doc.payments.forEach((payment) => {
					if (payment.type === "Phone" && ![0, "0", "", null, undefined].includes(payment.amount)) {
						phone_payment_is_valid = false;
					}
				});
				if (!phone_payment_is_valid) {
					this.eventBus.emit("show_message", {
						title: __("Please request phone payment or use another payment method"),
						color: "error",
					});
					frappe.utils.play_sound("error");
					return;
				}
			}
			// Validate paid_change
			if (this.paid_change > -this.diff_payment) {
				this.eventBus.emit("show_message", {
					title: `Paid change cannot be greater than total change!`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate cashback
			let total_change = this.flt(this.flt(this.paid_change) + this.flt(-this.credit_change));
			if (this.is_cashback && total_change !== -this.diff_payment) {
				this.eventBus.emit("show_message", {
					title: `Error in change calculations!`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate customer credit redemption
			let credit_calc_check = this.customer_credit_dict.filter((row) => {
				return this.flt(row.credit_to_redeem) > this.flt(row.total_credit);
			});
			if (credit_calc_check.length > 0) {
				this.eventBus.emit("show_message", {
					title: `Redeemed credit cannot be greater than its total.`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			if (
				!this.invoice_doc.is_return &&
				this.redeemed_customer_credit >
					(this.invoice_doc.rounded_total || this.invoice_doc.grand_total)
			) {
				this.eventBus.emit("show_message", {
					title: `Cannot redeem customer credit more than invoice total`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate stock availability before submitting
			if (!isOffline()) {
				try {
					const itemsToCheck = this.invoice_doc.items.filter((it) => !it.is_bundle);
					const stockCheck = await frappe.call({
						method: "posawesome.posawesome.api.invoices.validate_cart_items",
						args: { items: JSON.stringify(itemsToCheck) },
					});
					if (stockCheck.message && stockCheck.message.length) {
						const msg = stockCheck.message
							.map(
								(e) =>
									`${e.item_code} (${e.warehouse}) - ${this.formatFloat(e.available_qty)}`,
							)
							.join("\n");
						const blocking =
							!this.stock_settings.allow_negative_stock ||
							this.pos_profile.posa_block_sale_beyond_available_qty;
						this.eventBus.emit("show_message", {
							title: blocking
								? __("Insufficient stock:\n{0}", [msg])
								: __("Stock is lower than requested:\n{0}", [msg]),
							color: blocking ? "error" : "warning",
						});
						if (blocking) {
							frappe.utils.play_sound("error");
							this.loading = false;
							return;
						}
					}
				} catch (e) {
					console.error("Stock validation failed", e);
				}
			}

			// Proceed to submit the invoice
			this.loading = true;
			this.submit_invoice(print);
		},
		// Submit invoice to backend after all validations
		submit_invoice(print) {
			// For return invoices, ensure payments are negative one last time
			if (this.invoice_doc.is_return) {
				this.ensureReturnPaymentsAreNegative();
			}
			let totalPayedAmount = 0;
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = this.flt(payment.amount);
				totalPayedAmount += payment.amount;
			});
			if (this.invoice_doc.is_return && totalPayedAmount === 0) {
				this.invoice_doc.is_pos = 0;
			}
			if (this.customer_credit_dict.length) {
				this.customer_credit_dict.forEach((row) => {
					row.credit_to_redeem = this.flt(row.credit_to_redeem);
				});
			}

			// ===== IMPORTANT: Include due_date in the data object =====
			let data = {
				total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
				paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
				credit_change: -this.credit_change,
				redeemed_customer_credit: this.redeemed_customer_credit,
				customer_credit_dict: this.customer_credit_dict,
				is_cashback: this.is_cashback,
				due_date: this.invoice_doc.due_date,
				is_credit_sale: this.is_credit_sale,
			};

			const vm = this;

			if (isOffline()) {
				try {
					saveOfflineInvoice({ data: data, invoice: this.invoice_doc });
					this.eventBus.emit("pending_invoices_changed", getPendingOfflineInvoiceCount());
					vm.eventBus.emit("show_message", {
						title: __("Invoice saved offline"),
						color: "warning",
					});
					if (print) {
						this.print_offline_invoice(this.invoice_doc);
					}
					vm.eventBus.emit("clear_invoice");
					vm.eventBus.emit("reset_posting_date");
					vm.back_to_invoice();
					vm.loading = false;
					return;
				} catch (error) {
					vm.eventBus.emit("show_message", {
						title: __("Cannot Save Offline Invoice: ") + (error.message || __("Unknown error")),
						color: "error",
					});
					vm.loading = false;
					return;
				}
			}

			frappe.call({
				method:
					this.invoiceType === "Order" && this.pos_profile.posa_create_only_sales_order
						? "posawesome.posawesome.api.sales_orders.submit_sales_order"
						: "posawesome.posawesome.api.invoices.submit_invoice",
				args: {
					data: data,
					invoice: this.invoice_doc,
					order: this.invoice_doc,
				},
				callback: function (r) {
					if (r.exc) {
						console.error("Error submitting invoice:", r.exc);
						// Show detailed error message to help debugging
						let errorMsg = r.exc.toString();
						if (errorMsg.includes("Amount must be negative")) {
							vm.eventBus.emit("show_message", {
								title: __("Fixing payment amounts for return invoice..."),
								color: "warning",
							});
							// Force fix the amounts
							vm.invoice_doc.payments.forEach((payment) => {
								if (payment.amount > 0) {
									payment.amount = -Math.abs(payment.amount);
								}
								if (payment.base_amount > 0) {
									payment.base_amount = -Math.abs(payment.base_amount);
								}
							});
							// Retry submission once
							setTimeout(() => {
								vm.submit_invoice(print);
							}, 500);
						} else {
							vm.eventBus.emit("show_message", {
								title: __("Error submitting invoice: ") + errorMsg,
								color: "error",
							});
						}
						vm.loading = false;
						return;
					}
					if (!r.message) {
						vm.eventBus.emit("show_message", {
							title: __("Error submitting invoice: No response from server"),
							color: "error",
						});
						vm.loading = false;
						return;
					}
					if (print) {
						vm.load_print_page();
					}
					vm.customer_credit_dict = [];
					vm.redeem_customer_credit = false;
					vm.is_cashback = true;
					vm.is_credit_return = false;
					vm.sales_person = "";
					vm.eventBus.emit("set_last_invoice", vm.invoice_doc.name);
					vm.eventBus.emit("show_message", {
						title:
							vm.invoiceType === "Order" && vm.pos_profile.posa_create_only_sales_order
								? __("Sales Order {0} is Submitted", [r.message.name])
								: __("Invoice {0} is Submitted", [r.message.name]),
						color: "success",
					});
					frappe.utils.play_sound("submit");
					// Update local stock quantities immediately after successful
					// invoice submission so item availability reflects changes
					updateLocalStock(vm.invoice_doc.items || []);
					vm.addresses = [];
					vm.eventBus.emit("clear_invoice");
					vm.eventBus.emit("reset_posting_date");
					vm.back_to_invoice();
					vm.loading = false;
				},
			});
		},
		// Set full amount for a payment method (or negative for returns)
		set_full_amount(idx) {
			const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
			let totalAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;

			// Reset all payment amounts first
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = 0;
				if (payment.base_amount !== undefined) {
					payment.base_amount = 0;
				}
			});

			// Get the clicked payment method's name from the button text
			const clickedButton = event?.target?.textContent?.trim();

			// Set amount only for clicked payment method
			const clickedPayment = this.invoice_doc.payments.find(
				(payment) => payment.mode_of_payment === clickedButton,
			);

			if (clickedPayment) {
				let amount = isReturn ? -Math.abs(totalAmount) : totalAmount;
				clickedPayment.amount = amount;
				if (clickedPayment.base_amount !== undefined) {
					clickedPayment.base_amount = isReturn ? -Math.abs(amount) : amount;
				}
			} else {
				console.log("No payment found for button text:", clickedButton);
			}

			// Force Vue to update the view
			this.$forceUpdate();
		},
		// Set remaining amount for a payment method when focused
		set_rest_amount(idx) {
			const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
			this.invoice_doc.payments.forEach((payment) => {
				if (payment.idx === idx && payment.amount === 0 && this.diff_payment > 0) {
					let amount = this.diff_payment;
					if (isReturn) {
						amount = -Math.abs(amount);
					}
					payment.amount = amount;
					if (payment.base_amount !== undefined) {
						payment.base_amount = isReturn ? -Math.abs(amount) : amount;
					}
				}
			});
		},
		// Clear all payment amounts
		clear_all_amounts() {
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = 0;
			});
		},
		// Open print page for invoice
		load_print_page() {
			const print_format = this.pos_profile.print_format_for_online || this.pos_profile.print_format;
			const letter_head = this.pos_profile.letter_head || 0;
			const doctype = this.pos_profile.create_pos_invoice_instead_of_sales_invoice
				? "POS Invoice"
				: "Sales Invoice";
			const url =
				frappe.urllib.get_base_url() +
				"/printview?doctype=" +
				encodeURIComponent(doctype) +
				"&name=" +
				this.invoice_doc.name +
				"&trigger_print=1" +
				"&format=" +
				print_format +
				"&no_letterhead=" +
				letter_head;
			if (this.pos_profile.posa_silent_print) {
				silentPrint(url);
			} else {
				const printWindow = window.open(url, "Print");
				printWindow.addEventListener(
					"load",
					function () {
						printWindow.print();
					},
					{ once: true },
				);
			}
		},
		// Print invoice using a more detailed offline template
		async print_offline_invoice(invoice) {
			if (!invoice) return;
			const html = await renderOfflineInvoiceHTML(invoice);
			const win = window.open("", "_blank");
			win.document.write(html);
			win.document.close();
			win.focus();
			win.print();
		},
		// Validate due date (should not be in the past)
		validate_due_date() {
			const today = frappe.datetime.now_date();
			const new_date = Date.parse(this.invoice_doc.due_date);
			const parse_today = Date.parse(today);
			if (new_date < parse_today) {
				this.invoice_doc.due_date = today;
			}
		},
		// Keyboard shortcut for payment submit (Ctrl+X)
		shortPay(e) {
			if (e.key.toLowerCase() === "x" && (e.ctrlKey || e.metaKey)) {
				e.preventDefault();
				e.stopPropagation();
				if (this.invoice_doc && this.invoice_doc.payments) {
					this.submit_invoice();
				}
			}
		},
		// Get available customer credit and auto-allocate
		get_available_credit(use_credit) {
			this.clear_all_amounts();
			if (use_credit) {
				frappe
					.call("posawesome.posawesome.api.payments.get_available_credit", {
						customer: this.invoice_doc.customer,
						company: this.pos_profile.company,
					})
					.then((r) => {
						const data = r.message;
						if (data.length) {
							const amount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
							let remainAmount = amount;
							data.forEach((row) => {
								if (remainAmount > 0) {
									if (remainAmount >= row.total_credit) {
										row.credit_to_redeem = row.total_credit;
										remainAmount -= row.total_credit;
									} else {
										row.credit_to_redeem = remainAmount;
										remainAmount = 0;
									}
								} else {
									row.credit_to_redeem = 0;
								}
							});
							this.customer_credit_dict = data;
						} else {
							this.customer_credit_dict = [];
						}
					});
			} else {
				this.customer_credit_dict = [];
			}
		},
		// Get customer addresses for shipping
		get_addresses() {
			const vm = this;
			if (!vm.invoice_doc || !vm.invoice_doc.customer) {
				vm.addresses = [];
				return;
			}
			frappe.call({
				method: "posawesome.posawesome.api.customers.get_customer_addresses",
				args: { customer: vm.invoice_doc.customer },
				async: true,
				callback: function (r) {
					if (!r.exc) {
						vm.addresses = r.message;
					} else {
						vm.addresses = [];
					}
				},
			});
		},
		// Filter addresses for autocomplete
		addressFilter(item, queryText) {
			const searchText = queryText.toLowerCase();
			return (
				(item.address_title && item.address_title.toLowerCase().includes(searchText)) ||
				(item.address_line1 && item.address_line1.toLowerCase().includes(searchText)) ||
				(item.address_line2 && item.address_line2.toLowerCase().includes(searchText)) ||
				(item.city && item.city.toLowerCase().includes(searchText)) ||
				(item.name && item.name.toLowerCase().includes(searchText))
			);
		},
		// Open dialog to add new address
		new_address() {
			if (!this.invoice_doc || !this.invoice_doc.customer) {
				this.eventBus.emit("show_message", {
					title: __("Please select a customer first"),
					color: "error",
				});
				return;
			}
			this.eventBus.emit("open_new_address", this.invoice_doc.customer);
		},
		// helper: convert report-style message (keys + values) to objects
		convertReportRowsToObjects(msg) {
			// msg.keys = [...], msg.values = [[row], [row]...]
			if (!msg || !msg.keys || !msg.values) return [];

			const keyIndex = (keyName) => {
				const idx = msg.keys.findIndex((k) => {
					// keys in your debug were like "`tabSales Person`.`sales_person_name`"
					// normalize by checking endsWith field name
					return String(k).replace(/`/g, "").endsWith(`.${keyName}`);
				});
				return idx;
			};

			const idx_name = keyIndex("name"); // docname
			const idx_sales_person_name = keyIndex("sales_person_name");
			const idx_parent_sales_person = keyIndex("parent_sales_person");
			const idx_is_group = keyIndex("is_group");
			const idx_enabled = keyIndex("enabled");

			return msg.values.map((row) => {
				const name = idx_name >= 0 ? row[idx_name] : row[0];
				const sales_person_name =
					(idx_sales_person_name >= 0 && row[idx_sales_person_name]) || name;
				const parent = idx_parent_sales_person >= 0 ? row[idx_parent_sales_person] : null;
				const is_group = idx_is_group >= 0 ? Number(row[idx_is_group]) : 0;
				const enabled = idx_enabled >= 0 ? Number(row[idx_enabled]) : 1;

				return {
					value: name,
					title: sales_person_name,
					name,
					sales_person_name,
					parent,
					is_group,
					enabled,
				};
			});
		},

		// robust sales person loader
		get_sales_person_names() {
			const vm = this;

			// Try local cache if enabled
			if (vm.pos_profile && vm.pos_profile.posa_local_storage) {
				try {
					const cached = getSalesPersonsStorage(); // your helper
					if (cached && Array.isArray(cached) && cached.length) {
						vm.sales_persons = cached;
						vm.autoSelectSalesPerson();
					}
				} catch (e) {
					console.warn("Could not load cached sales persons", e);
				}
			}

			// Call server method (your existing API)
			frappe
				.call({
					method: "posawesome.posawesome.api.utilities.get_sales_person_names",
					callback: function (r) {
						// r.message might be either:
						// - array of objects [{name, sales_person_name}, ...] OR
						// - report style { keys: [...], values: [[...], ...] }
						if (!r || r.exc) {
							vm.sales_persons = vm.sales_persons || [];
							return;
						}

						let items = [];

						if (Array.isArray(r.message)) {
							// already array of objects (preferred)
							items = r.message.map((sp) => ({
								value: sp.name,
								title: sp.sales_person_name || sp.name,
								...sp,
							}));
						} else if (r.message && r.message.keys && r.message.values) {
							items = vm.convertReportRowsToObjects(r.message);
						} else {
							// fallback: try to map any array-like response
							try {
								items = (r.message || []).map((sp) => {
									if (typeof sp === "string") {
										return { value: sp, title: sp, name: sp };
									} else if (sp && sp.name) {
										return { value: sp.name, title: sp.sales_person_name || sp.name, ...sp };
									} else {
										return null;
									}
								}).filter(Boolean);
							} catch (e) {
								items = [];
							}
						}

						// filter out group rows (is_group === 1) and disabled (enabled === 0)
						items = items.filter((it) => {
							const notGroup = it.is_group === undefined ? true : Number(it.is_group) === 0;
							const enabled = it.enabled === undefined ? true : Number(it.enabled) !== 0;
							return notGroup && enabled;
						});

						vm.sales_persons = items;

						vm.autoSelectSalesPerson();

						// save cache if allowed
						if (vm.pos_profile && vm.pos_profile.posa_local_storage) {
							try {
								setSalesPersonsStorage(vm.sales_persons);
							} catch (e) {
								console.warn("Failed to save sales persons to storage", e);
							}
						}
					},
				})
				.fail(function (err) {
					console.error("Failed to fetch sales person names:", err);
				});
		},
		// Request payment for phone type
		request_payment() {
			this.phone_dialog = false;
			const vm = this;
			if (!this.invoice_doc.contact_mobile) {
				this.eventBus.emit("show_message", {
					title: __("Please set the customer's mobile number"),
					color: "error",
				});
				this.eventBus.emit("open_edit_customer");
				this.back_to_invoice();
				return;
			}
			this.eventBus.emit("freeze", { title: __("Waiting for payment...") });
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = this.flt(payment.amount);
			});
			let formData = { ...this.invoice_doc };
			formData["total_change"] = !this.invoice_doc.is_return ? -this.diff_payment : 0;
			formData["paid_change"] = !this.invoice_doc.is_return ? this.paid_change : 0;
			formData["credit_change"] = -this.credit_change;
			formData["redeemed_customer_credit"] = this.redeemed_customer_credit;
			formData["customer_credit_dict"] = this.customer_credit_dict;
			formData["is_cashback"] = this.is_cashback;
			frappe
				.call({
					method: "posawesome.posawesome.api.invoices.update_invoice",
					args: { data: formData },
					async: false,
					callback: function (r) {
						if (r.message) {
							vm.invoice_doc = r.message;
						}
					},
				})
				.then(() => {
					frappe
						.call({
							method: "posawesome.posawesome.api.payments.create_payment_request",
							args: { doc: vm.invoice_doc },
						})
						.fail(() => {
							vm.eventBus.emit("unfreeze");
							vm.eventBus.emit("show_message", {
								title: __("Payment request failed"),
								color: "error",
							});
						})
						.then(({ message }) => {
							const payment_request_name = message.name;
							setTimeout(() => {
								frappe.db
									.get_value("Payment Request", payment_request_name, [
										"status",
										"grand_total",
									])
									.then(({ message }) => {
										if (message.status !== "Paid") {
											vm.eventBus.emit("unfreeze");
											vm.eventBus.emit("show_message", {
												title: __(
													"Payment Request took too long to respond. Please try requesting for payment again",
												),
												color: "error",
											});
										} else {
											vm.eventBus.emit("unfreeze");
											vm.eventBus.emit("show_message", {
												title: __("Payment of {0} received successfully.", [
													vm.formatCurrency(
														message.grand_total,
														vm.invoice_doc.currency,
														0,
													),
												]),
												color: "success",
											});
											frappe.db
												.get_doc(vm.invoice_doc.doctype, vm.invoice_doc.name)
												.then((doc) => {
													vm.invoice_doc = doc;
													vm.submit(null, true);
												});
										}
									});
							}, 30000);
						});
				});
		},

		// Auto-select sales person based on various criteria
		autoSelectSalesPerson() {
			// If already selected, don't override
			if (this.sales_person) {
				return;
			}

			// Try to select from POS Profile
			if (this.pos_profile && this.pos_profile.posa_default_sales_person) {
				const defaultSP = this.pos_profile.posa_default_sales_person;
				const exists = this.sales_persons.find(sp => sp.value === defaultSP || sp.name === defaultSP);
				if (exists) {
					this.sales_person = exists.value;
					return;
				}
			}

			// If only one sales person available, select it
			if (this.sales_persons.length === 1) {
				this.sales_person = this.sales_persons[0].value;
				return;
			}

			// Try to select current user
			const currentUser = frappe.session.user;
			const userSP = this.sales_persons.find(sp =>
				sp.value === currentUser ||
				sp.name === currentUser ||
				sp.title === currentUser
			);
			if (userSP) {
				this.sales_person = userSP.value;
			}
		},
		// Get M-Pesa payment modes from backend
		get_mpesa_modes() {
			const vm = this;
			frappe.call({
				method: "posawesome.posawesome.api.m_pesa.get_mpesa_mode_of_payment",
				args: { company: vm.pos_profile.company },
				async: true,
				callback: function (r) {
					if (!r.exc) {
						vm.mpesa_modes = r.message;
					} else {
						vm.mpesa_modes = [];
					}
				},
			});
		},
		// Check if payment is M-Pesa C2B
		is_mpesa_c2b_payment(payment) {
			if (this.mpesa_modes.includes(payment.mode_of_payment) && payment.type === "Bank") {
				payment.amount = 0;
				return true;
			} else {
				return false;
			}
		},
		// Open M-Pesa payment dialog
		mpesa_c2b_dialog(payment) {
			const data = {
				company: this.pos_profile.company,
				mode_of_payment: payment.mode_of_payment,
				customer: this.invoice_doc.customer,
			};
			this.eventBus.emit("open_mpesa_payments", data);
		},
		// Set M-Pesa payment as customer credit
		set_mpesa_payment(payment) {
			this.pos_profile.use_customer_credit = true;
			this.redeem_customer_credit = true;
			const invoiceAmount = this.invoice_doc.rounded_total || this.invoice_doc.grand_total;
			let amount =
				payment.unallocated_amount > invoiceAmount ? invoiceAmount : payment.unallocated_amount;
			amount = amount > 0 ? amount : 0;
			const advance = {
				type: "Advance",
				credit_origin: payment.name,
				total_credit: this.flt(payment.unallocated_amount),
				credit_to_redeem: this.flt(amount),
			};
			this.clear_all_amounts();
			this.customer_credit_dict.push(advance);
		},
		// Update delivery date after selection
		update_delivery_date() {
			this.invoice_doc.posa_delivery_date = this.formatDate(this.new_delivery_date);
			// After setting delivery date, fetch addresses if not already loaded
			if (this.invoice_doc.customer && (!this.addresses || this.addresses.length === 0)) {
				this.get_addresses();
			}
		},
		// Update purchase order date after selection
		update_po_date() {
			this.invoice_doc.po_date = this.formatDate(this.new_po_date);
		},
		// Update credit due date after selection
		update_credit_due_date() {
			this.invoice_doc.due_date = this.formatDate(this.new_credit_due_date);
		},
		// Apply preset or typed number of days to set due date
		applyDuePreset(days) {
			if (days === null || days === "") {
				return;
			}
			const westernDays = formatUtils.fromArabicNumerals(String(days));
			if (isNaN(westernDays)) {
				return;
			}
			const parsed = parseInt(westernDays, 10);
			const d = new Date();
			d.setDate(d.getDate() + parsed);
			this.new_credit_due_date = this.formatDateDisplay(d);
			this.credit_due_days = parsed;
			this.update_credit_due_date();
		},
		// Apply days entered in dialog
		applyCustomDays() {
			this.applyDuePreset(this.custom_days_value);
			this.custom_days_dialog = false;
		},
		// Format date to YYYY-MM-DD
		formatDate(date) {
			if (!date) return null;
			if (typeof date === "string") {
				const western = formatUtils.fromArabicNumerals(date);
				if (/^\d{4}-\d{2}-\d{2}$/.test(western)) {
					return western;
				}
				if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(western)) {
					const [d, m, y] = western.split("-");
					return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
				}
				date = western;
			}
			const d = new Date(formatUtils.fromArabicNumerals(String(date)));
			if (!isNaN(d.getTime())) {
				const year = d.getFullYear();
				const month = `0${d.getMonth() + 1}`.slice(-2);
				const day = `0${d.getDate()}`.slice(-2);
				return `${year}-${month}-${day}`;
			}
			return formatUtils.fromArabicNumerals(String(date));
		},

		formatDateDisplay(date) {
			if (!date) return "";
			const western = formatUtils.fromArabicNumerals(String(date));
			if (typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(western)) {
				const [y, m, d] = western.split("-");
				return formatUtils.toArabicNumerals(`${d}-${m}-${y}`);
			}
			const d = new Date(western);
			if (!isNaN(d.getTime())) {
				const year = d.getFullYear();
				const month = `0${d.getMonth() + 1}`.slice(-2);
				const day = `0${d.getDate()}`.slice(-2);
				return formatUtils.toArabicNumerals(`${day}-${month}-${year}`);
			}
			return formatUtils.toArabicNumerals(western);
		},
		// Show paid amount info message
		showPaidAmount() {
			this.eventBus.emit("show_message", {
				title: `Total Paid Amount: ${this.formatCurrency(this.total_payments)}`,
				color: "info",
			});
		},
		// Show diff payment info message
		showDiffPayment() {
			if (!this.invoice_doc) return;
			this.eventBus.emit("show_message", {
				title: `To Be Paid: ${this.formatCurrency(this.diff_payment)}`,
				color: "info",
			});
		},
		// Show paid change info message
		showPaidChange() {
			this.eventBus.emit("show_message", {
				title: `Paid Change: ${this.formatCurrency(this.paid_change)}`,
				color: "info",
			});
		},
		// Show credit change info message
		showCreditChange(value) {
			if (value > 0) {
				this.credit_change = value;
				this.paid_change = -this.diff_payment;
			} else {
				this.credit_change = 0;
			}
		},
		// Format currency value
		formatCurrency(value) {
			return this.$options.mixins[0].methods.formatCurrency.call(this, value, this.currency_precision);
		},
		// Get change amount for display
		get_change_amount() {
			return Math.max(0, this.total_payments - this.invoice_doc.grand_total);
		},
		// Sync any invoices stored offline and show pending/synced counts
		async syncPendingInvoices() {
			const pending = getPendingOfflineInvoiceCount();
			if (pending) {
				this.eventBus.emit("show_message", {
					title: `${pending} invoice${pending > 1 ? "s" : ""} pending for sync`,
					color: "warning",
				});
				this.eventBus.emit("pending_invoices_changed", pending);
			}
			if (isOffline()) {
				// Don't attempt to sync while offline; just update the counter
				return;
			}
			const result = await syncOfflineInvoices();
			if (result && (result.synced || result.drafted)) {
				if (result.synced) {
					this.eventBus.emit("show_message", {
						title: `${result.synced} offline invoice${result.synced > 1 ? "s" : ""} synced`,
						color: "success",
					});
				}
				if (result.drafted) {
					this.eventBus.emit("show_message", {
						title: `${result.drafted} offline invoice${result.drafted > 1 ? "s" : ""} saved as draft`,
						color: "warning",
					});
				}
			}
			this.eventBus.emit("pending_invoices_changed", getPendingOfflineInvoiceCount());
		},
	},
	// Lifecycle hook: created
	created() {
		// Register keyboard shortcut for payment
		document.addEventListener("keydown", this.shortPay.bind(this));
		this.syncPendingInvoices();
		this.eventBus.on("network-online", this.syncPendingInvoices);
		// Also sync when the server connection is re-established
		this.eventBus.on("server-online", this.syncPendingInvoices);
	},
	// Lifecycle hook: mounted
	mounted() {
		// Initialize corporate flag
		this.selected_customer_is_corporate = false;

		// Listen for explicit customer detail updates
		this.eventBus.on("update_customer_details", (payload) => {
			this.selected_customer_is_corporate = !!(
				payload &&
				(payload.is_corporate || payload.is_company)
			);
		});

		// When the invoice data is provided, try to resolve corporate flag
		this.eventBus.on("send_invoice_doc_payment", (invoice_doc) => {
			// existing code...

			// ADD THIS BLOCK:
			if (invoice_doc && invoice_doc.customer) {
				// 1) if invoice_doc contains the flag already
				if (invoice_doc.is_corporate !== undefined || invoice_doc.is_company !== undefined) {
					this.selected_customer_is_corporate = !!(invoice_doc.is_corporate || invoice_doc.is_company);
				} else {
					// 2) fetch from server
					frappe
						.call({
							method: "posawesome.posawesome.api.customers.get_customer_info",
							args: { customer: invoice_doc.customer },
						})
						.then((r) => {
							if (r && r.message) {
								this.selected_customer_is_corporate = !!(r.message.is_corporate || r.message.is_company);
							} else {
								this.selected_customer_is_corporate = false;
							}
						})
						.catch((err) => {
							console.warn("[Payment] could not fetch customer info:", err);
							this.selected_customer_is_corporate = false;
						});
				}
			} else {
				this.selected_customer_is_corporate = false;
			}
		});

		// ADD THESE EVENT LISTENERS
		this.eventBus.on("show_payment", (data) => {
			if (data === "true") {
				// Get invoice data from Invoice component
				this.eventBus.emit("get_current_invoice_from_component");
			}
		});
		this.eventBus.on("current_invoice_data", (invoiceData) => {

			// Ensure payments array exists
			if (!invoiceData.payments) {
				invoiceData.payments = [];
			}

			// If empty, load ALL payment methods from POS Profile
			if (invoiceData.payments.length === 0) {
				console.log("[Payment] Loading payment methods from POS Profile");

				if (this.pos_profile && this.pos_profile.payments && this.pos_profile.payments.length > 0) {
					invoiceData.payments = this.pos_profile.payments.map((payment, index) => {
						return {
							name: "",
							mode_of_payment: payment.mode_of_payment,
							account: payment.custom_account || payment.default_account || "",
							amount: 0,
							base_amount: 0,
							type: payment.type || "Cash",
							idx: index + 1,
							default: payment.default || 0,
						};
					});

					// Detect corporate (treat Customer Type "Company" as corporate)
					const isCorporateFromInvoice = !!(
						invoiceData.is_corporate ||
						invoiceData.is_company ||
						invoiceData.customer_type === "Company" ||
						invoiceData.customer_type === "Corporate" ||
						invoiceData.customer_group === "Commercial"
					);
					const isCorporateFromComponent = !!(
						this.selected_customer_is_corporate ||
						(this.customer && (
							this.customer.is_corporate ||
							this.customer.is_company ||
							this.customer.customer_type === "Company" ||
							this.customer.customer_type === "Corporate" ||
							this.customer.customer_group === "Comercial"
						))
					);

					// Add Credit method if not present and customer is corporate
					if (!invoiceData.payments.some(p => (p.type || '').toLowerCase() === 'credit' || (p.mode_of_payment || '').toLowerCase() === 'credit')) {
						if (isCorporateFromInvoice || isCorporateFromComponent) {
							invoiceData.payments.push({
								name: "",
								mode_of_payment: "Credit",
								account: "",
								amount: 0,
								base_amount: 0,
								type: "Credit",
								idx: invoiceData.payments.length + 1,
								default: 0,
							});
						}
					}

					console.log("[Payment] Loaded payment methods:", invoiceData.payments);
				} else {
					// Fallback if POS Profile is not loaded yet
					console.warn("[Payment] POS Profile not available, using Cash as fallback");
					invoiceData.payments = [
						{
							name: "",
							mode_of_payment: "Cash",
							account: "",
							amount: 0,
							base_amount: 0,
							type: "Cash",
							idx: 1,
							default: 1,
						},
					];
				}
			}

			// Assign invoice and totals
			this.invoice_doc = invoiceData;
			this.grand_total = invoiceData.grand_total || 0;
			this.rounded_total = invoiceData.rounded_total || invoiceData.grand_total || 0;
			this.customer = invoiceData.customer || "";

			// Set selected_customer_is_corporate immediately if flags present or if customer_type indicates Company
			this.selected_customer_is_corporate = !!(
				invoiceData.is_corporate ||
				invoiceData.is_company ||
				invoiceData.customer_type === "Company" ||
				invoiceData.customer_type === "Corporate" ||
				invoiceData.customer_group === "Comercial"
			);

			// If we still don't know and invoice has customer id, fetch backend customer info (optional)
			if (!this.selected_customer_is_corporate && invoiceData.customer) {
				frappe
					.call({
						method: "posawesome.posawesome.api.customers.get_customer_info",
						args: { customer: invoiceData.customer },
					})
					.then((r) => {
						if (r && r.message) {
							const msg = r.message;
							this.selected_customer_is_corporate = !!(
								msg.is_corporate ||
								msg.is_company ||
								msg.customer_type === "Company" ||
								msg.customer_type === "Corporate" ||
								msg.customer_group === "Comercial"
							);

							// If we discovered corporate after fetching, ensure Credit exists
							if (this.selected_customer_is_corporate && Array.isArray(this.invoice_doc.payments)) {
								if (!this.invoice_doc.payments.some(p => (p.type || '').toLowerCase() === 'credit' || (p.mode_of_payment || '').toLowerCase() === 'credit')) {
									this.invoice_doc.payments.push({
										name: "",
										mode_of_payment: "Credit",
										account: "",
										amount: 0,
										base_amount: 0,
										type: "Credit",
										idx: this.invoice_doc.payments.length + 1,
										default: 0,
									});
									this.$forceUpdate && this.$forceUpdate();
									console.log("[Payment] Added Credit payment after fetching customer info");
								}
							}
						}
					})
					.catch((err) => {
						console.warn("[Payment] could not fetch customer info:", err);
					});
			}

			// Set payment amount
			this.payment_amount = this.rounded_total;
			console.log("[Payment] Payment amount set to:", this.payment_amount);

			// Force UI update
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		});


		this.$nextTick(() => {
			// Listen to various event bus events for POS actions
			this.eventBus.on("send_invoice_doc_payment", (invoice_doc) => {
				console.log("[Payment] send_invoice_doc_payment received, initializing...");
				this.invoice_doc = invoice_doc;

				// Ensure payments array exists
				if (!this.invoice_doc.payments) {
					this.invoice_doc.payments = [];
					console.log("[Payment] Created new payments array");
				}

				// If payments array is empty, load from POS Profile
				if (this.invoice_doc.payments.length === 0) {
					console.log("[Payment] Payments empty, loading from POS Profile");

					// Check if POS Profile has payment methods
					if (
						this.pos_profile &&
						this.pos_profile.payments &&
						this.pos_profile.payments.length > 0
					) {
						// Loop through all payment methods
						this.invoice_doc.payments = this.pos_profile.payments.map((payment, index) => {
							return {
								name: "",
								mode_of_payment: payment.mode_of_payment,
								account: payment.default_account || "",
								amount: 0,
								base_amount: 0,
								type: payment.type || "Cash",
								idx: index + 1,
								default: payment.default || 0,
							};
						});
						console.log("[Payment] Loaded payment methods:", this.invoice_doc.payments);
					} else {
						console.warn("[Payment] POS Profile not available");
						this.invoice_doc.payments = [
							{
								name: "",
								mode_of_payment: "Cash",
								account: "",
								amount: 0,
								base_amount: 0,
								type: "Cash",
								idx: 1,
								default: 1,
							},
						];
					}
				}

				console.log("[Payment] Payments initialized:", this.invoice_doc.payments);
				// ========== END FIX ==========

				const default_payment = this.invoice_doc.payments.find((payment) => payment.default === 1);
				this.is_credit_sale = false;
				this.is_write_off_change = false;
				if (invoice_doc.is_return) {
					this.is_return = true;
					this.is_credit_return = false;
					// Reset all payment amounts to zero for returns
					invoice_doc.payments.forEach((payment) => {
						payment.amount = 0;
						payment.base_amount = 0;
					});
					// Set default payment to negative amount for returns
					if (default_payment) {
						const amount = invoice_doc.rounded_total || invoice_doc.grand_total;
						default_payment.amount = -Math.abs(amount);
						if (default_payment.base_amount !== undefined) {
							default_payment.base_amount = -Math.abs(amount);
						}
					}
				} else if (default_payment) {
					// For regular invoices, set positive amount
					default_payment.amount = this.flt(
						invoice_doc.rounded_total || invoice_doc.grand_total,
						this.currency_precision,
					);
					this.is_credit_return = false;
				}
				this.loyalty_amount = 0;
				this.redeemed_customer_credit = 0;
				// Only get addresses if customer exists
				if (invoice_doc.customer) {
					this.get_addresses();
				}
				this.get_sales_person_names();
				console.log("[Payment] Initialization complete");
			});
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
				this.stock_settings = data.stock_settings || {};
				this.get_mpesa_modes();
				this.get_sales_person_names();

				// AUTO-SELECT SALES PERSON from POS Profile
				this.$nextTick(() => {
					if (this.pos_profile && this.pos_profile.posa_default_sales_person) {
						this.sales_person = this.pos_profile.posa_default_sales_person;
						console.log("[Payment] Auto-selected sales person:", this.sales_person);
					}
				});
			});
			this.eventBus.on("add_the_new_address", (data) => {
				this.addresses.push(data);
				this.$forceUpdate();
			});
			this.eventBus.on("update_invoice_type", (data) => {
				this.invoiceType = data;
				if (this.invoice_doc && data !== "Order") {
					this.invoice_doc.posa_delivery_date = null;
					this.invoice_doc.posa_notes = null;
					this.invoice_doc.shipping_address_name = null;
				} else if (this.invoice_doc && data === "Order") {
					// Initialize delivery date to today when switching to Order type
					this.new_delivery_date = this.formatDateDisplay(frappe.datetime.now_date());
					this.update_delivery_date();
				}
				// Handle return invoices properly
				if (this.invoice_doc && data === "Return") {
					this.invoice_doc.is_return = 1;
					// Ensure payments are negative for returns
					this.ensureReturnPaymentsAreNegative();
					this.is_credit_return = false;
				}
			});
			this.eventBus.on("update_customer", (customer) => {
				// Preserve existing reset behavior
				if (this.customer !== customer) {
					this.customer_credit_dict = [];
					this.redeem_customer_credit = false;
					this.is_cashback = true;
					this.is_credit_return = false;
				}

				// Normalize and store customer reference
				this.customer = customer;

				// Determine corporate flag (treat Customer Type === "Company" as corporate)
				if (customer && typeof customer === "object") {
					this.selected_customer_is_corporate = !!(
						customer.is_corporate ||
						customer.is_company ||
						customer.customer_type === "Company" ||
						customer.customer_type === "Corporate" ||
						customer.customer_group === "Commercial"
					);
				} else {
					// If only a string id/name was passed, clear and optionally fetch later
					this.selected_customer_is_corporate = false;
					// Optionally: fetch customer info from server here to resolve flags
				}

				console.log("[Payment] update_customer set selected_customer_is_corporate:", this.selected_customer_is_corporate);
			});

			this.eventBus.on("set_pos_settings", (data) => {
				this.pos_settings = data;
			});
			this.eventBus.on("set_customer_info_to_edit", (data) => {
				this.customer_info = data;
			});
			this.eventBus.on("set_mpesa_payment", (data) => {
				this.set_mpesa_payment(data);
			});
			// Clear any stored invoice when parent emits clear_invoice
			this.eventBus.on("clear_invoice", () => {
				this.invoice_doc = "";
				this.is_return = false;
				this.is_credit_return = false;
			});
			// Scroll to top when payment view is shown
			this.eventBus.on("show_payment", (data) => {
				if (data === "true") {
					this.showDialog = true; // ADD THIS
					this.handleShowPayment(data);
				} else {
					this.showDialog = false; // ADD THIS
					this.highlightSubmit = false;
				}
			});
		});
	},
	// Lifecycle hook: beforeUnmount
	beforeUnmount() {
		// Remove all event listeners
		this.eventBus.off("send_invoice_doc_payment");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("add_the_new_address");
		this.eventBus.off("update_invoice_type");
		this.eventBus.off("update_customer");
		this.eventBus.off("set_pos_settings");
		this.eventBus.off("set_customer_info_to_edit");
		this.eventBus.off("set_mpesa_payment");
		this.eventBus.off("clear_invoice");
		this.eventBus.off("network-online", this.syncPendingInvoices);
		this.eventBus.off("server-online", this.syncPendingInvoices);
		this.eventBus.off("show_payment", this.handleShowPayment);
	},
	// Lifecycle hook: unmounted
	unmounted() {
		// Remove keyboard shortcut listener
		document.removeEventListener("keydown", this.shortPay);
	},
};
</script>

<style scoped>

/* Remove readonly styling */
.v-text-field--readonly {
	cursor: text;
}

.v-text-field--readonly:hover {
	background-color: transparent;
}

.cards {
	background-color: var(--surface-secondary) !important;
}

/* Main Submit Button */
.submit-btn-main {
	position: relative;
	overflow: hidden;
	font-weight: 700 !important;
	font-size: 1.2rem !important;
	letter-spacing: 1px !important;
	height: 64px !important;
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.submit-btn-main::before {
	content: "";
	position: absolute;
	top: 0;
	left: -100%;
	width: 100%;
	height: 100%;
	background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
	transition: left 0.5s;
}

.submit-btn-main:hover {
	transform: translateY(-2px);
	background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
}

.submit-btn-main:hover::before {
	left: 100%;
}

.submit-btn-main:active {
	transform: translateY(0px);
}

.submit-btn-main:disabled {
	opacity: 0.6;
	transform: none !important;
}

/* Submit text styling */
.submit-text {
	font-size: 1.3rem;
	font-weight: 800;
	margin: 0 12px;
	text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Highlight animation */
/* .submit-highlight {
	animation: pulse-glow 1.5s ease-in-out infinite;
} */

/* @keyframes pulse-glow {
	0%, 100% {
		box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4),
					0 0 0 0 rgba(25, 118, 210, 0.7);
	}
	50% {
		box-shadow: 0 8px 20px rgba(25, 118, 210, 0.6),
					0 0 0 8px rgba(25, 118, 210, 0);
	}
} */

/* Dropdown Menu Styling - FIXED */
.submit-menu {
	border-radius: 8px !important;
	overflow: hidden;
	width: 100%;
	max-width: none !important;
	min-width: auto !important;
	border: 1px solid rgba(0, 0, 0, 0.1);
}

.menu-item {
	padding: 12px 16px !important;
	min-height: 60px !important;
	transition: all 0.2s ease;
	cursor: pointer;
}

.menu-item:hover {
	background: rgba(25, 118, 210, 0.08) !important;
}

.menu-item :deep(.v-list-item__prepend) {
	margin-right: 12px;
}

.menu-item :deep(.v-list-item-title) {
	font-weight: 600 !important;
	font-size: 0.95rem !important;
	line-height: 1.3 !important;
	margin-bottom: 2px !important;
}

.menu-item :deep(.v-list-item-subtitle) {
	font-size: 0.8rem !important;
	opacity: 0.7 !important;
	line-height: 1.2 !important;
}

.menu-title {
	font-weight: 600;
	font-size: 0.95rem;
	margin-bottom: 2px;
}

.menu-subtitle {
	font-size: 0.8rem;
	opacity: 0.7;
	white-space: normal;
	line-height: 1.2;
}

/* Cancel Button */
.cancel-btn {
	font-weight: 600 !important;
	font-size: 1rem !important;
	height: 52px !important;
	background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%) !important;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.cancel-btn:hover {
	transform: translateY(-1px);
	background: linear-gradient(135deg, #c62828 0%, #b71c1c 100%) !important;
}

.cancel-btn:active {
	transform: translateY(0px);
}

/* Button Row Spacing */
.button-row {
	gap: 8px;
}

/* Loading State */
.submit-btn-main.v-btn--loading {
	pointer-events: none;
}

.submit-btn-main .v-btn__loader {
	color: white;
}

/* Ensure parent card allows overflow for dropdown */
.cards {
	overflow: visible !important;
}

/* Dark Theme Adjustments */
:deep([data-theme="dark"]) .submit-btn-main,
:deep(.v-theme--dark) .submit-btn-main {
	background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%) !important;
}

:deep([data-theme="dark"]) .submit-btn-main:hover,
:deep(.v-theme--dark) .submit-btn-main:hover {
	background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
}

:deep([data-theme="dark"]) .submit-menu,
:deep(.v-theme--dark) .submit-menu {
	background-color: #1e1e1e !important;
	border-color: rgba(255, 255, 255, 0.1);
}

:deep([data-theme="dark"]) .menu-item:hover,
:deep(.v-theme--dark) .menu-item:hover {
	background: rgba(33, 150, 243, 0.12) !important;
}

/* Responsive Design */
@media (max-width: 600px) {
	.submit-btn-main {
		height: 56px !important;
		font-size: 1.1rem !important;
	}

	.submit-text {
		font-size: 1.1rem;
	}

	.cancel-btn {
		height: 48px !important;
		font-size: 0.95rem !important;
	}

	.menu-item {
		min-height: 56px !important;
		padding: 10px 14px !important;
	}
}

/* Icon Animations */
.submit-btn-main .v-icon {
	transition: transform 0.3s ease;
}

.submit-btn-main:hover .v-icon:first-child {
	transform: scale(1.1) rotate(5deg);
}

.submit-btn-main:hover .v-icon:last-child {
	transform: rotate(180deg);
}

/* Menu appears above button */
:deep(.v-overlay__content) {
	position: absolute !important;
}

/* Dark mode styling for input fields */
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


:deep(.v-overlay__content),
.v-overlay__content,
.v-dialog__content,
.v-dialog__content > .v-overlay__content {
  padding: 0 !important;
  margin: 0 !important;
  display: flex;
  align-items: flex-start; 
  box-sizing: border-box;
}

.payment-modal-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  padding: 8px 8px 12px; 
  box-sizing: border-box;
  background: transparent !important;
}

.payment-content {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  box-sizing: border-box;
}

.payment-card-wrapper {
  width: 100%;
  max-width: 1000px !important; 
  box-sizing: border-box;
  margin: 0 auto;
}

.payment-card-wrapper .v-card,
.payment-card-wrapper > .v-card,
.payment-card-wrapper .v-card.selection {
  display: flex !important;
  flex-direction: column !important;
  height: 75vh !important;        
  max-height: 75vh !important;
  overflow: hidden !important;   
  border-radius: 8px !important;
  margin: 0 !important;          
  padding: 0 !important;         
  box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
  box-sizing: border-box;
}

.payments-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px; 
  background: linear-gradient(90deg,#00897b,#00796b) !important; 
  color: #fff;
  min-height: 52px;
  box-sizing: border-box;
  border-top-left-radius: 0px;
  border-top-right-radius: 0px;
  width: 100%;
  z-index: 50;
  position: relative;
}

.payments-header-left {
  width: 44px;
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 0;
  margin: 0;
}
.payments-header-title {
  flex: 1;
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 0;
  margin: 0;
}
.payments-header-right {
  width: 48px;
  display:flex;
  align-items:center;
  justify-content:center;
  padding-right: 6px;
  margin: 0;
}

.payments-header .text-h6 {
  margin: 0;
  font-weight: 700;
  line-height: 1;
}

.payments-header-right .v-btn,
.payments-header-right v-btn {
  margin: 0 !important;
  padding: 6px !important;
  min-width: 36px !important;
  background: transparent !important;
}
.payments-header-right .v-icon {
  color: #fff !important;
}

.v-progress-linear[location="top"] {
  top: 0 !important;
  left: 0;
  right: 0;
  position: absolute !important;
  z-index: 60;
}

.payment-card-wrapper .overflow-y-auto,
.payment-card-wrapper .v-card .overflow-y-auto {
  flex: 1 1 auto;
  overflow-y: auto !important;
  padding: 12px !important;
  max-height: none !important;
  box-sizing: border-box;
  padding-bottom: 140px; 
}

.payment-card-wrapper .overflow-y-auto .pa-1 {
  margin-bottom: 6px;
}

.card-footer {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background: inherit;
  padding: 12px 16px;
  box-shadow: 0 -6px 14px rgba(0,0,0,0.06);
  z-index: 25;
}

.footer-actions,
.v-card.footer-actions,
.v-card.footer-actions .button-row {
  max-width: 1000px;
  width: calc(100% - 24px);
  margin: 10px auto 0 !important;
  box-sizing: border-box;
  position: relative;
  z-index: 55;
}

.submit-menu {
  border-radius: 8px !important;
  z-index: 1100 !important;
}

::deep .submit-menu,
:root .submit-menu {
  position: absolute !important;
}

.submit-btn-main {
  font-weight: 700 !important;
  font-size: 1.2rem !important;
  height: 64px !important;
}
.cancel-btn {
  font-weight: 600 !important;
  font-size: 1rem !important;
  height: 52px !important;
}

@media (max-width: 760px) {
  .payment-card-wrapper .v-card { height: 78vh !important; max-height: 78vh !important; }
  .payment-card-wrapper .overflow-y-auto { padding-bottom: 180px !important; }
  .payments-header { padding: 6px 10px !important; min-height: 48px; }
  .payment-modal-container { padding: 6px; }
  .footer-actions { width: calc(100% - 12px); max-width: 720px; }
}

.v-dialog__content,
.v-overlay__content,
.v-dialog__content > .v-overlay__content,
.v-overlay__content > .v-dialog__content {
  padding: 0 !important;
  margin: 0 !important;
  display: flex !important;
  align-items: flex-start !important;   
  justify-content: center !important;
  box-sizing: border-box !important;
}

.v-dialog__content > * ,
.v-overlay__content > * {
  margin: 0 !important;
  padding: 0 !important;
  box-sizing: border-box !important;
}

.payment-modal-container,
.payment-content,
.payment-card-wrapper {
  margin: 0 !important;
  padding: 0 !important;
  box-sizing: border-box !important;
}

.payment-card-wrapper .v-card,
.payment-card-wrapper > .v-card,
.payment-card-wrapper .v-card.selection,
div.v-card.selection {
  margin: 0 !important;             
  margin-top: 0 !important;
  padding: 0 !important;
  padding-top: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
}

.payment-card-wrapper .v-card::before,
.payment-card-wrapper .v-card::after,
.v-card.selection::before,
.v-card.selection::after {
  display: none !important;
  content: none !important;
}

.payments-header {
  margin: 0 !important;
  padding-top: 8px !important;   
  padding-bottom: 8px !important;
  box-sizing: border-box !important;
  position: relative !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  border-top-left-radius: 8px !important;
  border-top-right-radius: 8px !important;
}

.v-progress-linear[location="top"],
.v-progress-linear[location="top"][absolute] {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  margin: 0 !important;
  z-index: 999 !important;
}

.v-overlay__content > .payment-modal-container,
.v-overlay__content > .payment-content,
.v-overlay__content > .payment-card-wrapper,
.v-overlay__content > .v-card {
  align-self: flex-start !important;
}

.v-dialog__content,
.v-overlay__content {
  transform: none !important;
}

.payment-card-wrapper > .v-card,
.payment-card-wrapper .v-card.selection {
  overflow: visible !important;
}

.submit-menu,
::v-deep .submit-menu,
:root .submit-menu {
  position: absolute !important;
  z-index: 9000 !important;
}

.v-overlay__content {
  overflow: visible !important;
}

.v-menu > .v-overlay__content > .v-card,
.v-menu > .v-overlay__content > .v-list,
.v-menu > .v-overlay__content > .v-sheet {
  height: auto !important;       
  max-height: none !important;
  overflow: visible !important;   
  background: #ffffff !important;
  box-shadow: none !important;
}

.v-menu__content,
.v-menu__content--active,
.v-overlay__panel,
.submit-menu,
.v-overlay__content .v-list,
.v-overlay__panel .v-list {
  position: fixed !important;    
  left: 50% !important;
  transform: translateX(-50%) !important; 
  z-index: 14000 !important;      
  width: min(920px, 92%) !important; 
  min-width: 360px !important;
  max-width: 920px !important;
  background: transparent !important;
  overflow: visible !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.16) !important;
  border-radius: 10px !important;
}


.v-menu__content .v-list,
.submit-menu .v-list,
.v-overlay__panel .v-list {
  background: #fff !important;
  border-radius: 10px !important;
  padding: 8px !important;
  margin: 0 !important;
  max-height: 420px !important;   
  overflow-y: auto !important;    
  overflow-x: hidden !important;
}

.v-menu__content .v-list-item,
.submit-menu .v-list-item {
  min-height: 64px !important;
  padding: 12px 18px !important;
}

.v-overlay__content,
.v-overlay__panel,
.v-dialog__content {
  overflow: visible !important;
}

@media (max-width: 760px) {
  .v-menu__content,
  .submit-menu {
    left: 8px !important;
    right: 8px !important;
    transform: none !important;
    width: calc(100% - 16px) !important;
  }
  .v-menu__content .v-list,
  .submit-menu .v-list {
    max-height: 70vh !important;
  }
}

.v-menu__content {
  background: #ffffff !important;
}

.v-menu__content > .v-overlay__content,
.v-menu__content .v-sheet,
.v-menu__content .v-card,
.v-menu__content .v-list {
  background: #ffffff !important;
}

/* Credit Sale Button - Compact Style */
.credit-sale-btn-compact {
	font-weight: 600 !important;
	letter-spacing: 0.3px !important;
	height: 48px !important;
	transition: all 0.3s ease !important;
	font-size: 0.95rem !important;
}

.credit-sale-btn-compact:hover {
	transform: translateY(-1px);
	box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3) !important;
}

.credit-sale-btn-compact .v-icon {
	margin-right: 6px !important;
}

:deep([data-theme="dark"]) .credit-sale-btn-compact,
:deep(.v-theme--dark) .credit-sale-btn-compact {
	border-width: 2px !important;
}

</style>
