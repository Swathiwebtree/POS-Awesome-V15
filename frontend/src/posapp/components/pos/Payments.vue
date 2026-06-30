<template>
	<v-dialog
		v-model="showDialog"
		max-width="900px"
		width="900px"
		persistent
		scrollable="false"
		transition="dialog-bottom-transition"
		overlay-opacity="0.5"
	>
		<div class="payment-modal-container">
			<div class="payment-content">
				<div class="payment-card-wrapper">
					<!-- MAIN CARD -->
					<v-card
						:class="['selection mx-auto pa-0 my-0 mt-0', isDarkTheme ? '' : 'bg-grey-lighten-5']"
						:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
					>
						<!-- Header inside the card -->
						<div class="payments-header">
							<div class="payments-header-left">
								<v-icon class="ml-2 white--text" large>mdi-cash-register</v-icon>
							</div>

							<div class="payments-header-title">
								<div class="text-h6 font-weight-bold white--text">{{ __("Payment") }}</div>
							</div>

							<div class="payments-header-right">
								<v-btn
									icon
									@click="closeDialog"
									class="white--text"
									aria-label="Close payments dialog"
								>
									<v-icon class="white--text">mdi-close</v-icon>
								</v-btn>
							</div>
						</div>

						<v-progress-linear
							:active="loading"
							:indeterminate="loading"
							absolute
							location="top"
							color="info"
						></v-progress-linear>

						<div v-if="invoice_doc" class="payment-summary-hero payment-summary-fixed mt-3">
							<div class="summary-box paid">
								<div class="label">{{ __("Paid") }}</div>
								<div class="value">{{ total_payments_display }}</div>
							</div>

							<div class="summary-box due">
								<div class="label">{{ __("To Be Paid") }}</div>
								<div class="value">{{ diff_payment_display }}</div>
							</div>
						</div>
						<!-- Scrollable content -->
						<div ref="paymentContainer" class="pa-2 payment-content-container">
							<v-row dense>
								<v-col cols="6" class="payment-left-column">
									<!-- PAYMENT METHODS -->
									<div v-if="is_cashback">
										<!-- CREDIT SALE -->
										<div
											v-if="
												pos_profile.posa_allow_credit_sale &&
												!invoice_doc.is_return &&
												selected_customer_is_corporate
											"
											class="payment-method-card credit-sale-card"
											:class="{ active: is_credit_sale }"
										>
											<div class="method-left">
												<v-icon
													size="26"
													:color="is_credit_sale ? 'success' : 'grey'"
												>
													mdi-credit-card-clock
												</v-icon>
												<div>
													<div class="method-title">Credit Sale</div>
													<div class="method-amount">
														Amount will be added to customer credit
													</div>
												</div>
											</div>

											<v-btn
												size="small"
												:color="is_credit_sale ? 'success' : 'grey'"
												:variant="is_credit_sale ? 'elevated' : 'outlined'"
												@click="toggleCreditSale"
											>
												<v-icon size="20">
													{{
														is_credit_sale
															? "mdi-check-circle"
															: "mdi-close-circle"
													}}
												</v-icon>
											</v-btn>
										</div>

										<v-divider class="my-2" />
										<div class="payment-methods-grid">
											<div
												v-for="(payment, index) in invoice_doc.payments"
												:key="payment.name || `${payment.mode_of_payment}-${index}`"
												class="mb-1"
											>
												<div
													v-if="!is_mpesa_c2b_payment(payment)"
													class="payment-method-card"
													:class="{
														active: payment.amount > 0,
														disabled: invoice_doc.is_return,
													}"
													@click.stop
												>
													<div class="method-left">
														<v-icon size="26" color="primary">
															{{
																payment.mode_of_payment
																	.toLowerCase()
																	.includes("cash")
																	? "mdi-cash"
																	: "mdi-credit-card"
															}}
														</v-icon>

														<div>
															<div class="method-title">
																{{ payment.mode_of_payment }}
															</div>
															<div class="method-amount">
																{{ formatCurrency(payment.amount) }}
															</div>
														</div>
													</div>

													<v-text-field
														density="compact"
														variant="solo"
														hide-details
														class="method-input"
														:model-value="
															getPaymentInputDisplayValue(payment, index)
														"
														@update:model-value="
															onPaymentAmountInput(payment, index, $event)
														"
														@blur="
															handlePaymentAmountBlur(payment, index, $event)
														"
														@focus="handlePaymentAmountFocus(payment, index)"
														:rules="[
															isNumber,
															(v) => validateCashPaymentAmount(v, payment),
														]"
														:prefix="currencySymbol(invoice_doc.currency)"
														:readonly="invoice_doc.is_return"
													/>
												</div>

												<!-- M-PESA -->
												<v-btn
													v-if="is_mpesa_c2b_payment(payment)"
													block
													size="large"
													color="success"
													theme="dark"
													@click="mpesa_c2b_dialog(payment)"
												>
													<v-icon left>mdi-cellphone</v-icon>
													{{ __("Get Payments") }} {{ payment.mode_of_payment }}
												</v-btn>

												<!-- PHONE REQUEST -->
												<v-btn
													v-if="
														payment.type === 'Phone' &&
														payment.amount > 0 &&
														request_payment_field
													"
													block
													color="success"
													theme="dark"
													class="mt-1"
													@click="request_payment(payment)"
												>
													<v-icon left>mdi-send</v-icon>
													{{ __("Request Payment") }}
												</v-btn>
											</div>
										</div>
									</div>
								</v-col>

								<!-- ================= RIGHT COLUMN ================= -->
								<v-col cols="6" class="pl-2 mt-2">
									<!-- Invoice Totals -->
									<v-row class="pa-1" dense>
										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('Net Total')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												:model-value="
													formatCurrency(
														getDiscountedNetTotal(invoice_doc),
														displayCurrency,
													)
												"
												readonly
												:prefix="currencySymbol()"
												persistent-placeholder
											/>
										</v-col>

										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('VAT and Charges')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="
													formatCurrency(
														invoice_doc.total_taxes_and_charges || 0,
														displayCurrency,
													)
												"
												readonly
												:prefix="currencySymbol()"
												persistent-placeholder
											/>
										</v-col>

										<!-- <v-col cols="6" class="mb-3">
											<v-text-field density="compact" variant="solo" color="primary"
												:label="frappe._('Discount Amount')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field" hide-details
												:model-value="formatCurrency(invoice_doc.discount_amount)" readonly
												:prefix="currencySymbol(invoice_doc.currency)" persistent-placeholder />
										</v-col> -->

										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('Grand Total')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="
													formatCurrency(invoice_doc.grand_total, displayCurrency)
												"
												readonly
												:prefix="currencySymbol(invoice_doc.currency)"
												persistent-placeholder
											/>
										</v-col>

										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('Manual Round Off / Rounding Adjustment')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="getRoundingAdjustmentDisplayValue()"
												@update:model-value="onRoundingAdjustmentInput"
												@focus="handleRoundingAdjustmentFocus"
												@blur="handleRoundingAdjustmentBlur"
												:prefix="currencySymbol(invoice_doc.currency)"
												type="text"
												inputmode="decimal"
												persistent-placeholder
											/>
										</v-col>

										<v-col
											cols="6"
											class="mb-4"
											v-if="
												invoice_doc.rounded_total !== null &&
												invoice_doc.rounded_total !== undefined
											"
										>
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('Rounded Total')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="formatCurrency(invoice_doc.rounded_total)"
												readonly
												:prefix="currencySymbol(invoice_doc.currency)"
												persistent-placeholder
											/>
										</v-col>

										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="frappe._('Total Amount')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="
													formatCurrency(invoice_doc.grand_total, displayCurrency)
												"
												readonly
												:prefix="currencySymbol()"
												persistent-placeholder
											/>
										</v-col>

										<v-col cols="6" class="mb-3">
											<v-text-field
												density="compact"
												variant="solo"
												color="primary"
												:label="diff_label"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="formatCurrency(diff_payment, displayCurrency)"
												readonly
												:prefix="currencySymbol()"
												persistent-placeholder
											/>
										</v-col>
									</v-row>

									<v-divider class="my-2" />

									<v-row v-if="invoice_doc" dense>
										<v-col cols="6" v-if="credit_change > 0 && !invoice_doc.is_return">
											<v-text-field
												variant="solo"
												density="compact"
												color="primary"
												:label="frappe._('Paid Change')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="formatCurrency(paid_change)"
												:prefix="currencySymbol(invoice_doc.currency)"
												:rules="paid_change_rules"
												readonly
												persistent-placeholder
											/>
										</v-col>

										<v-col cols="6" v-if="credit_change > 0 && !invoice_doc.is_return">
											<v-text-field
												variant="solo"
												density="compact"
												color="primary"
												:label="frappe._('Credit Change')"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												:model-value="formatCurrency(credit_change)"
												:prefix="currencySymbol(invoice_doc.currency)"
												@change="
													setFormatedCurrency(
														this,
														'credit_change',
														null,
														false,
														$event,
													);
													updateCreditChange(this.credit_change);
												"
												persistent-placeholder
											/>
										</v-col>
									</v-row>

									<!-- Delivery Date -->
									<v-row
										class="pa-1"
										dense
										v-if="pos_profile.posa_allow_sales_order && invoiceType === 'Order'"
									>
										<v-col cols="6">
											<VueDatePicker
												v-model="new_delivery_date"
												model-type="format"
												format="dd-MM-yyyy"
												:min-date="new Date()"
												auto-apply
												:dark="isDarkTheme"
												class="dark-field sleek-field"
												@update:model-value="update_delivery_date()"
											/>
										</v-col>
									</v-row>

									<!-- Shipping Address -->
									<v-row class="pa-1" dense v-if="invoice_doc.posa_delivery_date">
										<v-col cols="12">
											<v-autocomplete
												density="compact"
												clearable
												auto-select-first
												variant="solo"
												color="primary"
												:label="frappe._('Address')"
												v-model="invoice_doc.shipping_address_name"
												:items="addresses"
												item-title="address_title"
												item-value="name"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												hide-details
												append-icon="mdi-plus"
												@click:append="new_address"
											/>
										</v-col>
									</v-row>

									<!-- Additional Notes -->
									<v-row
										class="pa-1"
										dense
										v-if="pos_profile.posa_display_additional_notes"
									>
										<v-col cols="12">
											<v-textarea
												variant="solo"
												density="compact"
												:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
												class="dark-field sleek-field"
												auto-grow
												rows="2"
												:label="frappe._('Additional Notes')"
												v-model="invoice_doc.posa_notes"
											/>
										</v-col>
									</v-row>
								</v-col>
							</v-row>

							<!-- Customer Purchase Order (if enabled in POS profile) -->
							<div v-if="pos_profile.posa_allow_customer_purchase_order">
								<v-divider></v-divider>
								<v-row class="pa-1" justify="center" align="start">
									<v-col cols="6">
										<v-text-field
											v-model="invoice_doc.po_no"
											:label="frappe._('Purchase Order')"
											variant="solo"
											density="compact"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field sleek-field"
											clearable
											color="primary"
											hide-details
										></v-text-field>
									</v-col>
									<v-col cols="6">
										<VueDatePicker
											v-model="new_po_date"
											model-type="format"
											format="dd-MM-yyyy"
											:min-date="new Date()"
											auto-apply
											:dark="isDarkTheme"
											class="dark-field sleek-field"
											@update:model-value="update_po_date()"
										/>
										<v-text-field
											v-model="invoice_doc.po_date"
											:label="frappe._('Purchase Order Date')"
											readonly
											variant="solo"
											density="compact"
											hide-details
											color="primary"
										></v-text-field>
									</v-col>
								</v-row>
							</div>

							<v-divider></v-divider>

							<!-- Switches for Write Off and Credit Sale -->
							<v-row class="pa-1" align="start" no-gutters>
								<v-col
									cols="6"
									v-if="
										pos_profile.posa_allow_write_off_change &&
										credit_change > 0 &&
										!invoice_doc.is_return
									"
								>
									<v-switch
										v-model="is_write_off_change"
										flat
										:label="frappe._('Write Off Difference Amount')"
										class="my-0 pa-1"
									></v-switch>
								</v-col>
								<!-- <v-col cols="6"
									v-if="pos_profile.posa_allow_credit_sale && !invoice_doc.is_return && selected_customer_is_corporate">
									<v-chip color="green" class="ma-2" size="large" text-color="white">
										{{ __('CREDIT SALE') }}
									</v-chip>
								</v-col> -->

								<v-col cols="6" v-if="invoice_doc.is_return && pos_profile.use_cashback">
									<v-switch
										v-model="is_cashback"
										flat
										:label="frappe._('Cashback?')"
										class="my-0 pa-1"
									></v-switch>
								</v-col>
								<v-col cols="6" v-if="invoice_doc.is_return">
									<v-switch
										v-model="is_credit_return"
										flat
										:label="frappe._('Credit Return?')"
										class="my-0 pa-1"
									></v-switch>
								</v-col>
								<v-col cols="6" v-if="is_credit_sale && false">
									<VueDatePicker
										v-model="new_credit_due_date"
										model-type="format"
										format="dd-MM-yyyy"
										:min-date="new Date()"
										auto-apply
										:dark="isDarkTheme"
										class="dark-field sleek-field"
										@update:model-value="update_credit_due_date()"
									/>
									<v-text-field
										class="mt-2 dark-field sleek-field"
										density="compact"
										variant="solo"
										type="number"
										min="0"
										max="365"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										v-model.number="credit_due_days"
										:label="frappe._('Days until due')"
										hide-details
										@change="applyDuePreset(credit_due_days)"
									></v-text-field>
									<div class="mt-1">
										<v-chip
											v-for="d in credit_due_presets"
											:key="d"
											size="small"
											class="ma-1"
											variant="solo"
											color="primary"
											@click="applyDuePreset(d)"
										>
											{{ d }} {{ frappe._("days") }}
										</v-chip>
									</div>
								</v-col>
								<v-col
									cols="6"
									v-if="!invoice_doc.is_return && pos_profile.use_customer_credit"
								>
									<v-switch
										v-model="redeem_customer_credit"
										flat
										:label="frappe._('Use Customer Credit')"
										class="my-0 pa-1"
										@update:model-value="get_available_credit(redeem_customer_credit)"
									></v-switch>
								</v-col>
							</v-row>

							<!-- Customer Credit Details -->
							<div
								v-if="
									invoice_doc &&
									available_customer_credit > 0 &&
									!invoice_doc.is_return &&
									redeem_customer_credit
								"
							>
								<v-row v-for="(row, idx) in customer_credit_dict" :key="idx">
									<v-col cols="4">
										<div class="pa-2 py-3">{{ row.credit_origin }}</div>
									</v-col>
									<v-col cols="4">
										<v-text-field
											density="compact"
											variant="solo"
											color="primary"
											:label="frappe._('Available Credit')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field sleek-field"
											hide-details
											:model-value="formatCurrency(row.total_credit)"
											readonly
											:prefix="currencySymbol(invoice_doc.currency)"
										></v-text-field>
									</v-col>
									<v-col cols="4">
										<v-text-field
											density="compact"
											variant="solo"
											color="primary"
											:label="frappe._('Redeem Credit')"
											:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
											class="dark-field sleek-field"
											hide-details
											type="text"
											:model-value="formatCurrency(row.credit_to_redeem)"
											@change="
												setFormatedCurrency(
													row,
													'credit_to_redeem',
													null,
													false,
													$event,
												)
											"
											:prefix="currencySymbol(invoice_doc.currency)"
										></v-text-field>
									</v-col>
								</v-row>
							</div>

							<v-divider></v-divider>

							<!-- Sales Person Selection -->
							<!-- <v-row class="pb-0 mb-2" align="start">
								<v-col cols="12">
									<p v-if="sales_persons && sales_persons.length > 0"
										class="mt-1 mb-1 text-subtitle-2">
										{{ sales_persons.length }} sales persons found
									</p>
									<p v-else class="mt-1 mb-1 text-subtitle-2 text-red d-none">No sales persons found</p>
									<v-select density="compact" clearable variant="solo" color="primary"
										:label="frappe._('Sales Person')" v-model="sales_person" :items="sales_persons"
										item-title="title" item-value="value"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'" class="dark-field sleek-field"
										:no-data-text="__('Sales Person not found')" hide-details
										:disabled="readonly"></v-select>
								</v-col>
							</v-row> -->
						</div>

						<div class="card-footer">
							<v-row align="start" no-gutters class="button-row">
								<!-- Submit Dropdown Button -->
								<v-col cols="12" class="mb-2">
									<v-menu
										:teleport="{ to: 'body' }"
										offset-y
										:close-on-content-click="true"
										location="top"
										transition="slide-y-reverse-transition"
									>
										<template v-slot:activator="{ props }">
											<v-btn
												ref="submitButton"
												block
												size="x-large"
												color="primary"
												theme="dark"
												v-bind="props"
												:loading="loading"
												:disabled="loading || vaildatPayment"
												:class="[
													'submit-btn-main',
													{ 'submit-highlight': highlightSubmit },
												]"
												elevation="4"
											>
												<v-icon left size="24">mdi-check-circle</v-icon>
												<span class="submit-text">{{ __("SUBMIT") }}</span>
												<v-icon right size="20">mdi-chevron-up</v-icon>
											</v-btn>
										</template>
										<v-list class="submit-menu" elevation="8" density="compact">
											<v-list-item
												@click="submit"
												class="menu-item"
												prepend-icon="mdi-check"
											>
												<v-list-item-title class="menu-title">
													{{ __("Submit Only") }}
												</v-list-item-title>
												<v-list-item-subtitle class="menu-subtitle">
													{{ __("Save invoice without printing") }}
												</v-list-item-subtitle>
											</v-list-item>
											<v-divider></v-divider>
											<v-list-item
												@click="submit(undefined, false, true)"
												class="menu-item"
												prepend-icon="mdi-printer-check"
											>
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
									<v-btn
										block
										size="large"
										color="error"
										theme="dark"
										@click="back_to_invoice"
										class="cancel-btn"
										elevation="2"
									>
										<v-icon left size="20">mdi-close-circle</v-icon>
										{{ __("Close") }}
									</v-btn>
								</v-col>
							</v-row>
						</div>
					</v-card>

					<!-- Custom Days Dialog -->
					<v-dialog v-model="custom_days_dialog" max-width="300px">
						<v-card>
							<v-card-title class="text-h6">
								{{ __("Custom Due Days") }}
							</v-card-title>
							<v-card-text class="pa-0">
								<v-container>
									<v-text-field
										density="compact"
										variant="solo"
										type="number"
										min="0"
										max="365"
										class="dark-field sleek-field"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										v-model.number="custom_days_value"
										:label="frappe._('Days')"
										hide-details
									></v-text-field>
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
									<v-text-field
										density="compact"
										variant="solo"
										color="primary"
										:label="frappe._('Mobile Number')"
										:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
										class="dark-field sleek-field"
										hide-details
										v-model="invoice_doc.contact_mobile"
										type="number"
									></v-text-field>
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

					<!-- Raw Printer Mapping Dialog -->
					<v-dialog v-model="printer_mapping_dialog" max-width="520px">
						<v-card>
							<v-card-title class="text-h6">
								{{ __("Printer Mapping") }}
							</v-card-title>
							<v-card-text class="pa-0">
								<v-container>
									<!-- <div class="text-body-2 mb-2">
										{{ __("Print Format") }}: {{ printer_mapping_context.print_format || "-" }}
									</div>
									<div class="text-body-2 mb-4">
										{{ __("Doctype") }}: {{ printer_mapping_context.doctype || "-" }}
									</div> -->
									<v-alert v-if="printer_error" type="error" variant="tonal" class="mb-3">
										{{ printer_error }}
									</v-alert>
									<v-select
										:items="available_printers"
										v-model="selected_printer"
										:label="__('Select Printer')"
										variant="solo"
										density="compact"
										:loading="printer_loading"
										:disabled="printer_loading"
									/>
								</v-container>
							</v-card-text>
							<v-card-actions>
								<v-spacer></v-spacer>
								<v-btn color="error" theme="dark" @click="printer_mapping_dialog = false">
									{{ __("Close") }}
								</v-btn>
								<v-btn
									color="primary"
									theme="dark"
									:disabled="!selected_printer"
									@click="save_printer_mapping"
								>
									{{ __("Save Mapping") }}
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
	getTaxTemplate,
	getTaxInclusiveSetting,
} from "../../../offline/index.js";

import renderOfflineInvoiceHTML from "../../../offline_print_template";
import { silentPrint } from "../../plugins/print.js";

export default {
	// Using format mixin for shared formatting methods
	mixins: [format],
	data() {
		return {
			showEmployeeSelection: false,
			selectedEmployee: null,
			showDialog: false,
			selected_customer_is_corporate: false,
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
			_active_invoice_instance_id: null,
			items_signature: "",
			pending_show_payment: false,
			printer_mapping_dialog: false,
			printer_mapping_context: { doctype: "", print_format: "" },
			available_printers: [],
			selected_printer: "",
			printer_loading: false,
			printer_error: "",
			pending_print_submit: false,
			pending_print_args: null,
			payment_input_values: {},
			active_payment_input: null,
			rounding_adjustment_input: "",
			active_rounding_adjustment_input: false,
		};
	},
	computed: {
		currency_precision() {
			const candidates = [
				this.invoice_doc?.currency_precision,
				this.invoice_doc?.company_currency_precision,
				this.pos_profile?.posa_decimal_precision,
				typeof frappe !== "undefined" && frappe?.defaults?.get_default
					? frappe.defaults.get_default("currency_precision")
					: null,
			];

			for (const candidate of candidates) {
				const precision = Number(candidate);
				if (Number.isFinite(precision)) {
					return precision;
				}
			}

			return 2;
		},

		computedTaxAndCharges() {
			if (!this.invoice_doc) return 0;
			const savedTaxTotal = Number(this.invoice_doc.total_taxes_and_charges || 0);
			if (savedTaxTotal) {
				return this.flt(savedTaxTotal, this.currency_precision);
			}
			if (Array.isArray(this.invoice_doc.taxes) && this.invoice_doc.taxes.length > 0) {
				return this.flt(
					this.invoice_doc.taxes.reduce((sum, tax) => sum + (Number(tax?.tax_amount) || 0), 0),
					this.currency_precision,
				);
			}
			return 0;
		},

		// Get the correct total for payment calculations
		totalInvoiceAmount() {
			if (!this.invoice_doc) return 0;

			return this.flt(this.payable_total, this.currency_precision);
		},
		// Verify tax calculation
		taxBreakdown() {
			if (!this.invoice_doc || !this.invoice_doc.taxes) return null;

			return this.invoice_doc.taxes.map((tax) => ({
				account: tax.account_head,
				rate: tax.rate,
				amount: this.flt(tax.tax_amount, this.currency_precision),
			}));
		},
		currencySymbol() {
			return (currency) => {
				return get_currency_symbol(currency || this.invoice_doc.currency);
			};
		},
		displayCurrency() {
			return this.invoice_doc ? this.invoice_doc.currency : "";
		},
		total_payments() {
			let total = 0;
			if (this.invoice_doc && this.invoice_doc.payments) {
				this.invoice_doc.payments.forEach((payment) => {
					total += parseFloat(formatUtils.fromArabicNumerals(String(payment.amount))) || 0;
				});
			}

			if (this.loyalty_amount) {
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					total += this.flt(
						this.loyalty_amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				} else {
					total += parseFloat(formatUtils.fromArabicNumerals(String(this.loyalty_amount))) || 0;
				}
			}

			if (this.redeemed_customer_credit) {
				if (this.invoice_doc.currency !== this.pos_profile.currency) {
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

		payable_total() {
			if (!this.invoice_doc) return 0;
			const roundedTotal =
				this.invoice_doc.to_be_paid != null
					? this.invoice_doc.to_be_paid
					: this.invoice_doc.rounded_total != null
						? this.invoice_doc.rounded_total
						: (this.invoice_doc.grand_total || 0) + (this.invoice_doc.rounding_adjustment || 0);
			return this.flt(roundedTotal, this.currency_precision);
		},

		diff_payment() {
			if (!this.invoice_doc) return 0;
			const invoice_total = this.payable_total;

			let diff = this.flt(invoice_total - this.total_payments, this.currency_precision);

			if (this.invoice_doc.is_return) {
				return diff >= 0 ? diff : 0;
			}

			return diff >= 0 ? diff : 0;
		},

		credit_change() {
			const invoice_total = this.payable_total;

			let change = this.flt(this.total_payments - invoice_total, this.currency_precision);

			return change > 0 ? change : 0;
		},

		diff_label() {
			return this.diff_payment > 0
				? `To Be Paid (${this.displayCurrency})`
				: `Change (${this.displayCurrency})`;
		},
		total_payments_display() {
			return this.formatCurrency(this.total_payments, this.displayCurrency);
		},
		diff_payment_display() {
			return this.formatCurrency(this.diff_payment, this.displayCurrency);
		},
		available_points_amount() {
			let amount = 0;
			if (this.customer_info.loyalty_points) {
				amount = this.customer_info.loyalty_points * this.customer_info.conversion_factor;

				if (this.invoice_doc.currency !== this.pos_profile.currency) {
					amount = this.flt(
						amount / (this.invoice_doc.conversion_rate || 1),
						this.currency_precision,
					);
				}
			}
			return amount;
		},
		available_customer_credit() {
			return this.customer_credit_dict.reduce((total, row) => total + this.flt(row.total_credit), 0);
		},
		vaildatPayment() {
			if (this.pos_profile.posa_allow_sales_order) {
				if (this.invoiceType === "Order" && !this.invoice_doc.posa_delivery_date) {
					return true;
				}
			}
			return false;
		},
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
		showDialog(newVal) {
			console.log("[Payment] showDialog changed to:", newVal);
			if (newVal === false && this.loading === true) {
				console.log("[Payment] Modal closed but loading still true - clearing");
				this.loading = false;
			}
		},

		loading(newVal) {
			console.log("[Payment] loading state changed to:", newVal);
		},

		// diff_payment(newVal) {
		// 	if (!this.is_user_editing_paid_change) {
		// 		this.paid_change = -newVal;
		// 	}
		// },
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
		loyalty_amount(value) {
			if (!this.invoice_doc || !this.customer_info) return;
			const moneyPrecision = this.currency_precision;
			const loyaltyAmount = Number(
				formatUtils.fromArabicNumerals(String(value || 0)).replace(/,/g, ""),
			);

			if (loyaltyAmount > this.available_points_amount) {
				this.invoice_doc.loyalty_amount = 0;
				this.invoice_doc.redeem_loyalty_points = 0;
				this.loyalty_amount = 0;

				this.eventBus.emit("show_message", {
					title: `Loyalty Amount cannot exceed ${this.available_points_amount}`,
					color: "error",
				});
				return;
			}

			const points = Math.round(loyaltyAmount / this.customer_info.conversion_factor);

			this.invoice_doc.loyalty_amount = this.flt(loyaltyAmount, moneyPrecision);
			this.invoice_doc.loyalty_discount_amount = this.flt(loyaltyAmount, moneyPrecision);
			this.invoice_doc.redeem_loyalty_points = points;
			this.invoice_doc.redeemed_loyalty_points = points;
			const netTotal = this.getDiscountedNetTotal(this.invoice_doc);
			this.invoice_doc.net_total = netTotal;
			this.invoice_doc.total_taxes_and_charges = this.calculateInvoiceTaxTotal(
				this.invoice_doc,
				netTotal,
			);
			this.invoice_doc.grand_total = this.flt(
				netTotal + (this.invoice_doc.total_taxes_and_charges || 0),
				moneyPrecision,
			);
		},
		redeemed_customer_credit(newVal) {
			if (newVal > this.available_customer_credit) {
				this.redeemed_customer_credit = this.available_customer_credit;
				this.eventBus.emit("show_message", {
					title: `You can redeem customer credit up to ${this.available_customer_credit}`,
					color: "error",
				});
			}
		},
		"invoice_doc.items": {
			handler(newItems, oldItems) {
				console.log("[Payment] invoice_doc.items changed, clearing old payment amounts");

				const newSignature = this.computeItemsSignature(newItems);
				if (newSignature !== this.items_signature) {
					this.items_signature = newSignature;
					this.resetPaymentAmounts();
				}
			},
			deep: true,
		},
		customer_credit_dict: {
			handler(newVal) {
				const total = newVal.reduce((sum, row) => sum + this.flt(row.credit_to_redeem || 0), 0);
				this.redeemed_customer_credit = this.flt(total, this.currency_precision);
			},
			deep: true,
		},
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
						payment.amount = this.getEffectiveInvoiceTotal();
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
		isCarWashServiceItem(item) {
			if (!item) {
				return false;
			}

			const group = (item.item_group || "").toLowerCase();
			const code = (item.item_code || "").toLowerCase();
			const name = (item.item_name || "").toLowerCase();

			const washMatch =
				group.includes("car wash") ||
				group.includes("carwash") ||
				group.includes("bike wash") ||
				group.includes("bikewash") ||
				code.includes("carwash") ||
				code.includes("car wash") ||
				code.includes("bikewash") ||
				code.includes("bike wash") ||
				name.includes("carwash") ||
				name.includes("car wash") ||
				name.includes("bikewash") ||
				name.includes("bike wash");

			return washMatch;
		},

		hasCarWashServiceForItems(items) {
			if (!Array.isArray(items) || items.length === 0) {
				return false;
			}
			return items.some((item) => this.isCarWashServiceItem(item));
		},

		hasCarWashService() {
			if (this.invoice_doc?.custom_has_carwash_service !== undefined) {
				return !!this.invoice_doc.custom_has_carwash_service;
			}
			return this.hasCarWashServiceForItems(this.invoice_doc?.items || []);
		},

		computeItemsSignature(items) {
			if (!Array.isArray(items) || items.length === 0) {
				return "";
			}
			return items
				.map((item) =>
					[
						item.item_code || "",
						item.item_group || "",
						item.item_name || "",
						this.flt(item.qty || 0),
						this.flt(item.rate || 0),
						this.flt(item.amount || 0),
					].join("|"),
				)
				.sort()
				.join("::");
		},

		getPaymentInputKey(payment, index) {
			return payment?.name || `${payment?.mode_of_payment || "payment"}-${payment?.idx ?? index}`;
		},

		parsePaymentAmountInput(value) {
			if (value === null || value === undefined || value === "") {
				return 0;
			}
			const western = formatUtils.fromArabicNumerals(String(value)).replace(/,/g, "");
			const parsed = parseFloat(western);
			return Number.isNaN(parsed) ? 0 : parsed;
		},

		validateCashPaymentAmount(value, payment) {
			if (!payment?.mode_of_payment?.toLowerCase().includes("cash") || this.is_credit_sale) {
				return true;
			}
			const enteredAmount = this.parsePaymentAmountInput(value);
			const minimumAmount = this.payable_total;
			return enteredAmount >= minimumAmount || "Cash payment cannot be less than invoice total";
		},

		getPaymentInputDisplayValue(payment, index) {
			const key = this.getPaymentInputKey(payment, index);
			if (this.active_payment_input === key) {
				return this.payment_input_values[key] ?? "";
			}
			if (payment?.amount === null || payment?.amount === undefined) {
				return "";
			}
			return this.flt(payment.amount || 0, this.currency_precision).toFixed(this.currency_precision);
		},

		onPaymentAmountInput(payment, index, value) {
			const key = this.getPaymentInputKey(payment, index);
			this.payment_input_values[key] = value;
			this.is_user_editing_paid_change = true;
			if (value === "" || value === null || value === undefined) {
				payment.amount = null;
				if (payment.base_amount !== undefined) {
					payment.base_amount = null;
				}
				return;
			}
			this.setFormatedCurrency(payment, "amount", this.currency_precision, false, value);
		},

		handlePaymentAmountFocus(payment, index) {
			this.is_user_editing_paid_change = true;
			if (!payment) return;
			const key = this.getPaymentInputKey(payment, index);
			this.active_payment_input = key;
			if (payment.amount === 0) {
				payment.amount = null;
			}
			this.payment_input_values[key] =
				payment.amount === null || payment.amount === undefined ? "" : String(payment.amount);
		},

		handlePaymentAmountBlur(payment, index, $event) {
			if (!payment) return;

			const key = this.getPaymentInputKey(payment, index);
			const raw = $event?.target?.value ?? this.payment_input_values[key];

			if (!raw) {
				payment.amount = null;
				delete this.payment_input_values[key];
				this.active_payment_input = null;
				return;
			}

			// Parse number
			const parsed = this.flt(raw, this.currency_precision);

			// Force precision
			payment.amount = Number(parsed).toFixed(this.currency_precision);

			delete this.payment_input_values[key];
			this.active_payment_input = null;
		},

		getRoundingAdjustmentDisplayValue() {
			if (!this.invoice_doc) return "";
			if (this.active_rounding_adjustment_input) {
				return this.rounding_adjustment_input ?? "";
			}
			const value = this.invoice_doc.rounding_adjustment;
			if (value === null || value === undefined || value === "") {
				return "";
			}
			return this.flt(value, this.currency_precision).toFixed(this.currency_precision);
		},

		applyRoundingAdjustment(value) {
			if (!this.invoice_doc) return;

			const moneyPrecision = this.currency_precision;
			const roundOff = this.flt(value || 0, moneyPrecision);
			const grandTotal = this.flt(this.invoice_doc.grand_total || 0, moneyPrecision);
			const roundedTotal = this.flt(grandTotal + roundOff, moneyPrecision);

			this.invoice_doc.rounding_adjustment = roundOff;
			this.invoice_doc.rounded_total = roundedTotal;
			this.invoice_doc.total_amount = grandTotal;
			this.invoice_doc.to_be_paid = roundedTotal;

			this.grand_total = grandTotal;
			this.rounded_total = roundedTotal;
		},

		onRoundingAdjustmentInput(value) {
			this.active_rounding_adjustment_input = true;
			this.rounding_adjustment_input = value ?? "";

			if (value === "" || value === null || value === undefined) {
				this.applyRoundingAdjustment(0);
				return;
			}

			this.applyRoundingAdjustment(this.parsePaymentAmountInput(value));
		},

		handleRoundingAdjustmentFocus() {
			this.active_rounding_adjustment_input = true;
			this.rounding_adjustment_input = String(this.invoice_doc?.rounding_adjustment ?? "");
		},

		handleRoundingAdjustmentBlur(event) {
			if (!this.invoice_doc) return;

			const raw = event?.target?.value ?? this.rounding_adjustment_input;
			const parsed =
				raw === "" || raw === null || raw === undefined ? 0 : this.parsePaymentAmountInput(raw);

			this.applyRoundingAdjustment(parsed);
			this.rounding_adjustment_input = this.flt(parsed, this.currency_precision).toFixed(
				this.currency_precision,
			);
			this.active_rounding_adjustment_input = false;
		},

		tryOpenPaymentDialog() {
			if (!this.pending_show_payment) {
				return;
			}
			if (!this.invoice_doc || !Array.isArray(this.invoice_doc.items)) {
				return;
			}

			this.refreshPaymentMethodsForCustomer(this.customer_info, this.invoice_doc);

			const hasServiceItem = this.hasCarWashServiceForItems(this.invoice_doc.items || []);
			const hasEmployee = !!this.invoice_doc?.custom_service_employee;

			if (hasServiceItem && !hasEmployee) {
				frappe.show_alert({
					message: __("Please select the service employee."),
					indicator: "red",
				});
				frappe.utils.play_sound("error");
				this.showDialog = false;
				this.loading = false;
				this.highlightSubmit = false;
				this.pending_show_payment = false;
				return;
			}

			this.showDialog = true;
			this.loading = false;
			this.highlightSubmit = false;
			this.pending_show_payment = false;

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
		},

		resetPaymentAmounts() {
			if (!this.invoice_doc || !this.invoice_doc.payments) {
				return;
			}

			console.log("[Payment] Resetting all payment amounts to 0");

			// Clear all payment amounts
			this.invoice_doc.payments.forEach((payment) => {
				payment.amount = null;
				if (payment.base_amount !== undefined) {
					payment.base_amount = null;
				}
			});

			// Reset related flags
			this.redeemed_customer_credit = 0;
			this.is_cashback = true;
			this.is_credit_return = false;
			this.is_write_off_change = false;
			this.paid_change = 0;
			this.credit_change = 0;
			this.customer_credit_dict = [];
			this.redeem_customer_credit = false;
			this.payment_input_values = {};
			this.active_payment_input = null;
			this.rounding_adjustment_input = "";
			this.active_rounding_adjustment_input = false;

			// Force UI update
			this.$nextTick(() => {
				this.$forceUpdate();
			});
		},

		resetPaymentData() {
			console.log("[Payment] Resetting all payment data");

			// Reset invoice document
			this.invoice_doc = null;

			// Reset payment amounts
			this.loyalty_amount = 0;
			this.redeemed_customer_credit = 0;
			this.credit_change = 0;
			this.paid_change = 0;

			// Reset flags
			this.is_credit_sale = false;
			this.is_write_off_change = false;
			this.is_cashback = true;
			this.is_credit_return = false;
			this.redeem_customer_credit = false;
			this.is_return = false;

			// Reset customer credit
			this.customer_credit_dict = [];

			// Reset dates
			this.new_delivery_date = null;
			this.new_po_date = null;
			this.new_credit_due_date = null;
			this.credit_due_days = null;

			// Reset sales person
			this.sales_person = "";

			// Reset customer info
			this.customer = "";
			this.customer_info = "";
			this.selected_customer_is_corporate = false;

			// Reset addresses
			this.addresses = [];
			this.payment_input_values = {};
			this.active_payment_input = null;
			this.rounding_adjustment_input = "";
			this.active_rounding_adjustment_input = false;

			// Reset UI states
			this.loading = false;
			this.showDialog = false;
			this.highlightSubmit = false;
			this.phone_dialog = false;
			this.custom_days_dialog = false;

			console.log("[Payment] Payment data reset complete");
		},

		isCorporateCustomer(source = this.customer) {
			const customer = source && typeof source === "object" ? source : {};
			const customerType = String(customer.customer_type || "")
				.trim()
				.toLowerCase();
			return !!(
				customer.is_corporate ||
				customer.is_company ||
				customerType === "company" ||
				customerType === "corporate"
			);
		},

		isOnAccountPaymentMethod(method) {
			const mode = String(method?.mode_of_payment || "")
				.trim()
				.toLowerCase();
			return mode === "on account" || mode === "on-account";
		},

		filterPaymentMethodsForCustomer(methods = [], customer = this.customer_info) {
			return (methods || []).filter((method) => {
				if (this.isOnAccountPaymentMethod(method)) {
					return this.isCorporateCustomer(customer);
				}
				return true;
			});
		},

		buildPaymentMethodsFromPosProfile(customer = this.customer_info) {
			const methods = Array.isArray(this.pos_profile?.payments) ? this.pos_profile.payments : [];
			return this.filterPaymentMethodsForCustomer(methods, customer).map((payment, index) => {
				return {
					name: "",
					mode_of_payment: payment.mode_of_payment,
					account: payment.custom_account || payment.default_account || "",
					amount: null,
					base_amount: null,
					type: payment.type || "Cash",
					idx: index + 1,
					default: payment.default || 0,
				};
			});
		},

		refreshPaymentMethodsForCustomer(customer = this.customer_info, invoiceDoc = this.invoice_doc) {
			if (!invoiceDoc) return [];

			const currentAmounts = new Map(
				(invoiceDoc.payments || []).map((payment) => [payment.mode_of_payment, payment.amount]),
			);
			const filtered = this.buildPaymentMethodsFromPosProfile(customer);
			invoiceDoc.payments = filtered.map((payment) => ({
				...payment,
				amount: currentAmounts.get(payment.mode_of_payment) ?? null,
			}));
			return invoiceDoc.payments;
		},

		buildTaxRowsFromPosProfile(doc = this.invoice_doc, baseAmount = null) {
			const templateName = this.pos_profile?.taxes_and_charges;
			if (!templateName) return [];

			const tmpl = getTaxTemplate(templateName);
			if (!tmpl || !Array.isArray(tmpl.taxes) || !tmpl.taxes.length) {
				return [];
			}

			const netTotal =
				baseAmount != null
					? Number(baseAmount)
					: doc?.net_total != null
						? Number(doc.net_total)
						: this.getDiscountedNetTotal(doc);
			let runningTotal = Number.isFinite(netTotal) ? Number(netTotal) : 0;
			const rows = [];

			tmpl.taxes.forEach((row) => {
				const rate = Number(row.rate || 0);
				let taxAmount = 0;
				if (row.charge_type === "Actual") {
					taxAmount = Number(row.tax_amount || 0);
				} else {
					taxAmount = (runningTotal * rate) / 100;
				}

				runningTotal += taxAmount;
				rows.push({
					account_head: row.account_head,
					charge_type: row.charge_type || "On Net Total",
					description: row.description,
					rate,
					included_in_print_rate: row.included_in_print_rate || 0,
					tax_amount: this.flt(taxAmount, this.currency_precision),
					total: this.flt(runningTotal, this.currency_precision),
				});
			});

			return rows;
		},

		applyLoadedInvoiceTotals(doc = this.invoice_doc) {
			if (!doc) return null;

			const moneyPrecision = this.currency_precision;
			const hasSavedTaxes = Array.isArray(doc.taxes) && doc.taxes.length > 0;
			const toNumber = (value) => {
				const parsed = Number(formatUtils.fromArabicNumerals(String(value ?? 0)).replace(/,/g, ""));
				return Number.isFinite(parsed) ? parsed : 0;
			};

			const netTotal =
				doc.net_total != null ? toNumber(doc.net_total) : this.getDiscountedNetTotal(doc);
			let taxRows = hasSavedTaxes ? doc.taxes : [];
			let taxTotal = 0;

			if (hasSavedTaxes) {
				taxTotal =
					doc.total_taxes_and_charges != null
						? toNumber(doc.total_taxes_and_charges)
						: doc.taxes.reduce((sum, tax) => sum + toNumber(tax?.tax_amount), 0);
				if (!taxTotal && doc.taxes.length > 0) {
					taxTotal = doc.taxes.reduce((sum, tax) => sum + toNumber(tax?.tax_amount), 0);
				}
			} else {
				taxRows = this.buildTaxRowsFromPosProfile(doc, netTotal);
				if (taxRows.length) {
					doc.taxes = taxRows;
				}
				taxTotal = this.calculateInvoiceTaxTotal(doc, netTotal);
				if (!taxTotal && taxRows.length) {
					taxTotal = taxRows.reduce((sum, tax) => sum + toNumber(tax?.tax_amount), 0);
				}
			}

			const grandTotal =
				doc.grand_total != null
					? toNumber(doc.grand_total)
					: this.flt(netTotal + taxTotal, moneyPrecision);
			const roundOff = toNumber(doc.rounding_adjustment || 0);
			const roundedTotal =
				doc.rounded_total != null
					? toNumber(doc.rounded_total)
					: this.flt(grandTotal + roundOff, moneyPrecision);
			const exchangeRate = Number(doc.conversion_rate || this.exchange_rate || 1);

			doc.net_total = this.flt(netTotal, moneyPrecision);
			doc.total_taxes_and_charges = this.flt(taxTotal, moneyPrecision);
			doc.grand_total = this.flt(grandTotal, moneyPrecision);
			doc.total_amount = this.flt(grandTotal, moneyPrecision);
			doc.rounding_adjustment = this.flt(roundOff, moneyPrecision);
			doc.rounded_total = this.flt(roundedTotal, moneyPrecision);
			doc.to_be_paid = this.flt(roundedTotal, moneyPrecision);
			doc.base_net_total = this.flt(doc.net_total * exchangeRate, moneyPrecision);
			doc.base_total_taxes_and_charges = this.flt(
				doc.total_taxes_and_charges * exchangeRate,
				moneyPrecision,
			);
			doc.base_grand_total = this.flt(doc.grand_total * exchangeRate, moneyPrecision);
			doc.base_rounded_total = this.flt(doc.rounded_total * exchangeRate, moneyPrecision);

			this.total_tax = doc.total_taxes_and_charges;
			this.grand_total = doc.grand_total;
			this.rounded_total = doc.rounded_total;

			return {
				net_total: doc.net_total,
				total_taxes_and_charges: doc.total_taxes_and_charges,
				grand_total: doc.grand_total,
				rounded_total: doc.rounded_total,
			};
		},

		async syncCorporateCustomerState(source = this.customer) {
			const customerName =
				(typeof source === "string" && source) ||
				source?.customer ||
				source?.customer_name ||
				source?.name ||
				this.customer ||
				this.invoice_doc?.customer;

			if (!customerName) {
				this.selected_customer_is_corporate = false;
				this.customer_info = "";
				this.refreshPaymentMethodsForCustomer(this.customer_info, this.invoice_doc);
				return false;
			}

			try {
				const r = await frappe.call({
					method: "posawesome.posawesome.api.customers.get_customer_info",
					args: { customer: customerName },
				});
				const msg = r?.message || {};
				if (msg.loyalty_program) {
					try {
						const redemptionFactorResponse = await frappe.call({
							method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_redeemption_factor",
							args: {
								customer: customerName,
								loyalty_program: msg.loyalty_program,
							},
						});
						msg.conversion_factor = Number(
							redemptionFactorResponse?.message ?? msg.conversion_factor ?? 0,
						);
					} catch (factorErr) {
						console.warn("[Payment] failed to fetch loyalty redemption factor:", factorErr);
					}
				}
				this.customer_info = msg;
				this.selected_customer_is_corporate = this.isCorporateCustomer(msg);
				this.refreshPaymentMethodsForCustomer(msg, this.invoice_doc);
				return this.selected_customer_is_corporate;
			} catch (err) {
				console.warn("[Payment] could not fetch customer info:", err);
				this.selected_customer_is_corporate = false;
				this.refreshPaymentMethodsForCustomer(this.customer_info, this.invoice_doc);
				return false;
			}
		},

		getPreTaxDiscountAmount(doc = this.invoice_doc) {
			const invoiceDiscountRaw = Number(
				formatUtils
					.fromArabicNumerals(String(doc?.discount_amount || doc?.additional_discount || 0))
					.replace(/,/g, ""),
			);
			const additionalDiscountRaw = Number(doc?.additional_discount || 0);
			const loyaltyDiscountRaw = Number(
				formatUtils
					.fromArabicNumerals(String(doc?.loyalty_discount_amount || doc?.loyalty_amount || 0))
					.replace(/,/g, ""),
			);
			if (
				Number.isFinite(invoiceDiscountRaw) &&
				Number.isFinite(additionalDiscountRaw) &&
				Number.isFinite(loyaltyDiscountRaw) &&
				invoiceDiscountRaw > 0 &&
				additionalDiscountRaw > 0 &&
				Math.abs(invoiceDiscountRaw - additionalDiscountRaw) <= 1 / 10 ** this.currency_precision &&
				Math.abs(invoiceDiscountRaw - loyaltyDiscountRaw) <= 1 / 10 ** this.currency_precision
			) {
				return 0;
			}
			return Number.isFinite(invoiceDiscountRaw) ? invoiceDiscountRaw : 0;
		},

		getLoyaltyDiscountAmount(doc = this.invoice_doc) {
			const loyaltyDiscount = Number(
				formatUtils
					.fromArabicNumerals(String(this.loyalty_amount || doc?.loyalty_discount_amount || 0))
					.replace(/,/g, ""),
			);
			return Number.isFinite(loyaltyDiscount) ? loyaltyDiscount : 0;
		},

		getDiscountedNetTotal(doc = this.invoice_doc) {
			const moneyPrecision = this.currency_precision;
			const itemTotal = Number(
				formatUtils.fromArabicNumerals(String(doc?.total || 0)).replace(/,/g, ""),
			);
			const preTaxDiscount = this.getPreTaxDiscountAmount(doc);
			const loyaltyDiscount = this.getLoyaltyDiscountAmount(doc);
			const safeItemTotal = Number.isFinite(itemTotal) ? itemTotal : 0;
			const safeDiscount = Number.isFinite(preTaxDiscount) ? preTaxDiscount : 0;
			const safeLoyalty = Number.isFinite(loyaltyDiscount) ? loyaltyDiscount : 0;
			return this.flt(safeItemTotal - safeDiscount - safeLoyalty, moneyPrecision);
		},

		calculateTemplateTaxTotal(doc = this.invoice_doc, baseAmount = null) {
			const templateName = this.pos_profile?.taxes_and_charges;
			if (!templateName) return 0;

			const tmpl = getTaxTemplate(templateName);
			if (!tmpl || !Array.isArray(tmpl.taxes) || !tmpl.taxes.length) return 0;
			const moneyPrecision = this.currency_precision;

			const resolvedBaseAmount =
				baseAmount != null
					? Number(baseAmount)
					: this.getDiscountedNetTotal(doc) != null
						? Number(this.getDiscountedNetTotal(doc))
						: doc?.net_total != null
							? Number(formatUtils.fromArabicNumerals(String(doc.net_total)).replace(/,/g, ""))
							: Number(
									formatUtils
										.fromArabicNumerals(
											String(
												(doc?.total ?? 0) -
													this.getPreTaxDiscountAmount(doc) -
													this.getLoyaltyDiscountAmount(doc),
											),
										)
										.replace(/,/g, ""),
								);
			let totalTax = 0;

			tmpl.taxes.forEach((row) => {
				const rate = Number(row.rate || 0);
				let taxAmount = 0;
				if (row.charge_type === "Actual") {
					taxAmount = Number(row.tax_amount || 0);
				} else {
					taxAmount = (resolvedBaseAmount * rate) / 100;
				}
				totalTax += taxAmount;
			});

			return this.flt(totalTax, moneyPrecision);
		},

		calculateItemTax(doc = this.invoice_doc, baseAmount = null) {
			let taxTotal = 0;

			if (!doc || !doc.items) {
				return 0;
			}

			const moneyPrecision = this.currency_precision;
			const itemBaseTotal = Number(
				formatUtils.fromArabicNumerals(String(doc?.total ?? 0)).replace(/,/g, ""),
			);
			const discountedItemTotal =
				baseAmount != null
					? Number(baseAmount)
					: this.getDiscountedNetTotal(doc) != null
						? Number(this.getDiscountedNetTotal(doc))
						: doc?.net_total != null
							? Number(formatUtils.fromArabicNumerals(String(doc.net_total)).replace(/,/g, ""))
							: itemBaseTotal -
								this.getPreTaxDiscountAmount(doc) -
								this.getLoyaltyDiscountAmount(doc);
			const taxableFactor = itemBaseTotal ? discountedItemTotal / itemBaseTotal : 1;

			doc.items.forEach((item) => {
				if (!item.item_tax_rate) return;

				let taxMap = {};
				try {
					taxMap = JSON.parse(item.item_tax_rate);
				} catch (e) {
					return;
				}

				//  POS Awesome uses net_amount as taxable value
				const rate = item.net_rate ?? item.rate ?? 0;
				const quantity = Number(item.qty || 0);
				const amount = item.net_amount ?? item.amount ?? rate * quantity;
				const taxableAmount = amount * taxableFactor;

				Object.values(taxMap).forEach((rate) => {
					taxTotal += (taxableAmount * rate) / 100;
				});
			});

			return this.flt(taxTotal, moneyPrecision);
		},

		calculateInvoiceTaxTotal(doc = this.invoice_doc, baseAmount = null) {
			if (!doc) return 0;
			const hasItemTaxRates = Array.isArray(doc.items) && doc.items.some((item) => item?.item_tax_rate);
			if (hasItemTaxRates) {
				return this.calculateItemTax(doc, baseAmount);
			}
			return this.calculateTemplateTaxTotal(doc, baseAmount);
		},

		// Verify invoice totals before submission
		verifyInvoiceTotals() {
			if (!this.invoice_doc) {
				console.error("[Payment] No invoice document to verify");
				return false;
			}

			const netTotal = this.flt(this.invoice_doc.net_total || 0);
			const taxTotal = this.flt(this.invoice_doc.total_taxes_and_charges || 0);
			const grandTotal = this.flt(this.invoice_doc.grand_total || 0);
			const expectedGrandTotal = netTotal + taxTotal;

			console.log("[Payment] Invoice Verification:", {
				netTotal,
				taxTotal,
				grandTotal,
				expectedGrandTotal,
				difference: Math.abs(grandTotal - expectedGrandTotal),
				taxes: this.taxBreakdown,
			});

			// Check if grand total is correct
			if (Math.abs(grandTotal - expectedGrandTotal) > 0.01) {
				console.error("[Payment] Grand total does not match calculation!");
				this.eventBus.emit("show_message", {
					title: `Tax calculation error detected. Please refresh and try again.`,
					color: "error",
				});
				return false;
			}

			// Check if taxes are present
			if (taxTotal === 0 && this.invoice_doc.taxes && this.invoice_doc.taxes.length > 0) {
				console.warn("[Payment] Tax rows exist but total is zero");
			}

			return true;
		},
		toggleCreditSale() {
			this.is_credit_sale = !this.is_credit_sale;

			if (this.is_credit_sale) {
				if (!this.invoice_doc.due_date || this.invoice_doc.due_date < this.invoice_doc.posting_date) {
					// Set due date automatically (30 days from posting date)
					this.applyDuePreset(30);
				}

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
			this.loading = false;
			this._active_invoice_instance_id = null;
			this.eventBus.emit("show_payment", "false");
			this.eventBus.emit("set_customer_readonly", false);
		},
		// ADD THIS NEW METHOD
		closeDialog() {
			this.showDialog = false;
			this.loading = false;
			this.back_to_invoice();
		},
		handleDialogClose(value) {
			console.log("[Payment] handleDialogClose called with value:", value);
			if (!value) {
				// Dialog is being closed
				this.showDialog = false;
				this.loading = false;
				this._active_invoice_instance_id = null;
				console.log("[Payment] Modal closed by user");
			}
		},
		handleShowPayment(data) {
			if (this.showOdometerField) {
				if (!this.odometerValue || isNaN(this.odometerValue) || Number(this.odometerValue) <= 0) {
					frappe.show_alert({
						message: this.__(
							"Please enter a valid odometer reading before proceeding to payment.",
						),
						indicator: "red",
					});
					frappe.utils.play_sound("error");
					return;
				}
			}

			if (!this.invoice_doc) return;

			this.loading = true;

			frappe.call({
				method: "posawesome.posawesome.api.invoices.update_invoice",
				args: { data: this.invoice_doc },
				callback: (r) => {
					this.loading = false;

					if (!r.message) return;

					this.invoice_doc = {
						...r.message,
					};

					this.applyRoundingAdjustment(this.invoice_doc.rounding_adjustment || 0);
					this.rounding_adjustment_input = this.flt(
						this.invoice_doc.rounding_adjustment || 0,
						this.currency_precision,
					).toFixed(this.currency_precision);
					this.active_rounding_adjustment_input = false;

					console.log("[Payment] Synced invoice before opening", {
						net: r.message.net_total,
						tax: r.message.total_taxes_and_charges,
						grand: r.message.grand_total,
					});

					this.eventBus.emit("show_payment", "true");

					// Optional UX highlight
					this.$nextTick(() => {
						const btn = this.$refs.submitButton;
						const el = btn && btn.$el ? btn.$el : btn;
						if (el) {
							el.scrollIntoView({ behavior: "smooth", block: "center" });
							el.focus();
							this.highlightSubmit = true;
						}
					});
				},
			});
		},
		reset_cash_payments() {
			if (!this.invoice_doc || !this.invoice_doc.payments) {
				console.warn("[Payment] Cannot reset cash payments - invoice_doc not ready");
				return;
			}

			this.invoice_doc.payments.forEach((payment) => {
				if (payment.mode_of_payment && payment.mode_of_payment.toLowerCase() === "cash") {
					payment.amount = null;
				}
			});
		},
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
					const amount = this.getEffectiveInvoiceTotal();
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
		async submit(event, payment_received = false, print = false, skip_raw_precheck = false) {
			// this.invoice_doc.total_taxes_and_charges = this.computedTaxAndCharges;

			// this.invoice_doc.grand_total =
			// 	this.flt(this.invoice_doc.net_total) +
			// 	this.flt(this.computedTaxAndCharges);

			console.log("Synced Tax:", this.invoice_doc.total_taxes_and_charges);
			console.log("Synced Grand Total:", this.invoice_doc.grand_total);

			if (print && !skip_raw_precheck) {
				const print_format =
					this.pos_profile.posa_dot_matrix_print_format ||
					this.pos_profile.print_format_for_online ||
					this.pos_profile.print_format;
				const doctype = this.pos_profile.create_pos_invoice_instead_of_sales_invoice
					? "POS Invoice"
					: "Sales Invoice";
				const is_raw_format = await this.is_raw_print_format(print_format);
				if (is_raw_format) {
					const ready = await this.prepare_raw_print_before_submit(doctype, print_format);
					if (!ready) {
						this.pending_print_submit = true;
						this.pending_print_args = {
							event,
							payment_received,
							print,
						};
						return;
					}
				}
			}

			if (!this.verifyInvoiceTotals()) {
				console.error("[Payment] Invoice total verification failed");
				return;
			}
			if (this.invoice_doc.is_return) {
				this.ensureReturnPaymentsAreNegative();
			}

			if (this.invoice_doc && this.invoice_doc.posting_date) {
				const posting_date = new Date(this.invoice_doc.posting_date);
				const due_date = this.invoice_doc.due_date ? new Date(this.invoice_doc.due_date) : null;

				if (this.is_credit_sale) {
					if (!this.invoice_doc.due_date) {
						// Auto-set to 30 days from posting date
						const newDueDate = new Date(posting_date);
						newDueDate.setDate(newDueDate.getDate() + 30);
						this.invoice_doc.due_date = this.formatDate(newDueDate);
						console.log(
							"[Payment] Auto-set due_date for credit sale:",
							this.invoice_doc.due_date,
						);
					} else if (due_date < posting_date) {
						// If due_date is before posting_date, adjust it
						const newDueDate = new Date(posting_date);
						newDueDate.setDate(newDueDate.getDate() + 30);
						this.invoice_doc.due_date = this.formatDate(newDueDate);
						console.log(
							"[Payment] Adjusted due_date (was before posting_date):",
							this.invoice_doc.due_date,
						);
					}
				} else {
					if (!this.invoice_doc.due_date) {
						const newDueDate = new Date(posting_date);
						newDueDate.setDate(newDueDate.getDate() + 1);
						this.invoice_doc.due_date = this.formatDate(newDueDate);
						console.log("[Payment] Set due_date for regular invoice:", this.invoice_doc.due_date);
					} else if (due_date < posting_date) {
						this.invoice_doc.due_date = this.formatDate(posting_date);
						console.log(
							"[Payment] Corrected due_date to match posting_date:",
							this.invoice_doc.due_date,
						);
					}
				}
			}

			let hasPaymentAmount = false;
			if (this.invoice_doc && this.invoice_doc.payments && this.invoice_doc.payments.length > 0) {
				for (let payment of this.invoice_doc.payments) {
					if (parseFloat(payment.amount) > 0) {
						hasPaymentAmount = true;
						break;
					}
				}
			}

			if (
				!this.is_credit_sale &&
				!this.invoice_doc.is_return &&
				!hasPaymentAmount &&
				this.getEffectiveInvoiceTotal() > 0
			) {
				this.eventBus.emit("show_message", {
					title: `Please enter payment amount`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}

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
						cash_amount < this.getEffectiveInvoiceTotal() &&
						this.getEffectiveInvoiceTotal() > 0
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
			if (
				!this.is_credit_sale &&
				!this.pos_profile.posa_allow_partial_payment &&
				this.total_payments < this.getEffectiveInvoiceTotal() &&
				this.getEffectiveInvoiceTotal() > 0
			) {
				this.eventBus.emit("show_message", {
					title: `The amount paid is not complete`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
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
			// Validate paid_change (skip for credit sales)
			if (!this.is_credit_sale && this.paid_change > -this.diff_payment) {
				this.eventBus.emit("show_message", {
					title: `Paid change cannot be greater than total change!`,
					color: "error",
				});
				frappe.utils.play_sound("error");
				return;
			}
			// Validate cashback
			let total_change = this.flt(this.flt(this.paid_change) + this.flt(-this.credit_change));
			if (this.is_cashback && !this.is_credit_sale && total_change !== -this.diff_payment) {
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
				this.redeemed_customer_credit > this.getEffectiveInvoiceTotal()
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
		submit_invoice(print) {
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

			if (this.invoice_doc && this.invoice_doc.posting_date) {
				const posting_date = new Date(this.invoice_doc.posting_date);
				const due_date = this.invoice_doc.due_date ? new Date(this.invoice_doc.due_date) : null;

				// Ensure due_date exists
				if (!this.invoice_doc.due_date) {
					const newDueDate = new Date(posting_date);
					newDueDate.setDate(newDueDate.getDate() + (this.is_credit_sale ? 30 : 1));
					this.invoice_doc.due_date = this.formatDate(newDueDate);
					console.log("[Payment] Auto-set due_date:", this.invoice_doc.due_date);
				}
				// Ensure due_date is NOT before posting_date
				else if (due_date < posting_date) {
					const newDueDate = new Date(posting_date);
					newDueDate.setDate(newDueDate.getDate() + (this.is_credit_sale ? 30 : 1));
					this.invoice_doc.due_date = this.formatDate(newDueDate);
					console.log("[Payment] Corrected due_date:", this.invoice_doc.due_date);
				}
			}

			// FINAL LOYALTY
			if (this.customer_info?.loyalty_program) {
				this.invoice_doc.loyalty_program = this.customer_info.loyalty_program;
			}

			this.invoice_doc.loyalty_amount = Number(
				formatUtils
					.fromArabicNumerals(
						String(
							this.loyalty_amount ||
								this.invoice_doc.loyalty_discount_amount ||
								this.invoice_doc.loyalty_amount ||
								0,
						),
					)
					.replace(/,/g, ""),
			);
			this.invoice_doc.loyalty_discount_amount = Number(
				formatUtils
					.fromArabicNumerals(
						String(
							this.invoice_doc.loyalty_discount_amount || this.invoice_doc.loyalty_amount || 0,
						),
					)
					.replace(/,/g, ""),
			);
			this.invoice_doc.redeem_loyalty_points = Math.round(
				Number(
					this.invoice_doc.redeemed_loyalty_points || this.invoice_doc.redeem_loyalty_points || 0,
				),
			);
			this.invoice_doc.redeemed_loyalty_points = this.invoice_doc.redeem_loyalty_points;
			this.invoice_doc.total_amount = this.flt(
				this.invoice_doc.grand_total || 0,
				this.currency_precision,
			);
			this.invoice_doc.to_be_paid = this.flt(this.payable_total || 0, this.currency_precision);
			this.invoice_doc.rounded_total = this.invoice_doc.to_be_paid;
			this.invoice_doc.rounding_adjustment = this.flt(
				this.invoice_doc.rounded_total - this.invoice_doc.grand_total,
				this.currency_precision,
			);

			// Safety
			if (this.invoice_doc.loyalty_amount < 0) this.invoice_doc.loyalty_amount = 0;
			if (this.invoice_doc.redeem_loyalty_points < 0) this.invoice_doc.redeem_loyalty_points = 0;

			let data = {
				total_change: !this.invoice_doc.is_return ? -this.diff_payment : 0,
				paid_change: !this.invoice_doc.is_return ? this.paid_change : 0,
				credit_change: -this.credit_change,
				redeemed_customer_credit: this.redeemed_customer_credit,
				customer_credit_dict: this.customer_credit_dict,
				is_cashback: this.is_cashback,
				due_date: this.invoice_doc.due_date,
				is_credit_sale: this.is_credit_sale,
				rounding_adjustment: this.invoice_doc.rounding_adjustment,
				rounded_total: this.invoice_doc.rounded_total,
				total_amount: this.invoice_doc.total_amount,
				to_be_paid: this.invoice_doc.to_be_paid,
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
					vm.showDialog = false;
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
					async: true,
					timeout: 30000,
					callback: function (r) {
						vm.loading = false;

						if (r.exc) {
							console.error("Error submitting invoice:", r.exc);
							const errorMsg = r.exc.toString();
							if (errorMsg.includes("Amount must be negative")) {
								vm.eventBus.emit("show_message", {
									title: __("Fixing payment amounts for return invoice..."),
									color: "warning",
								});
								vm.invoice_doc.payments.forEach((payment) => {
									if (payment.amount > 0) {
										payment.amount = -Math.abs(payment.amount);
									}
									if (payment.base_amount > 0) {
										payment.base_amount = -Math.abs(payment.base_amount);
									}
								});
								setTimeout(() => {
									vm.submit_invoice(print);
								}, 500);
							} else {
								vm.highlightSubmit = false;
								vm.eventBus.emit("show_message", {
									title: __("Error submitting invoice: ") + errorMsg,
									color: "error",
								});
								frappe.utils.play_sound("error");
							}
							return;
						}

						if (!r.message) {
							vm.highlightSubmit = false;
							vm.eventBus.emit("show_message", {
								title: __("Error submitting invoice: No response from server"),
								color: "error",
							});
							frappe.utils.play_sound("error");
							return;
						}

						const submitErrors = Array.isArray(r.message.errors)
							? r.message.errors.filter((error) => !!error)
							: [];
						if (submitErrors.length > 0) {
							const errorMessage = submitErrors
								.map((error) => (typeof error === "string" ? error : JSON.stringify(error)))
								.join("\n");
							vm.highlightSubmit = false;
							vm.eventBus.emit("show_message", {
								title: __("Payment submission finished with errors. Please review and try again."),
								color: "error",
							});
							frappe.msgprint({
								title: __("Payment submission errors"),
								message: errorMessage,
								indicator: "red",
							});
							frappe.utils.play_sound("error");
							console.error("[Payment] Submission completed with errors:", r.message.errors);
							return;
						}

						vm.invoice_doc.name = r.message.name;
						vm.invoice_doc.docstatus = r.message.docstatus || 1;

						if (print) {
							vm.load_print_page();
						}

						vm.customer_credit_dict = [];
						vm.redeem_customer_credit = false;
						vm.is_cashback = true;
						vm.is_credit_return = false;
						vm.sales_person = "";
						vm.eventBus.emit("set_last_invoice", r.message.name);
						vm.eventBus.emit("show_message", {
							title:
								vm.invoiceType === "Order" && vm.pos_profile.posa_create_only_sales_order
									? __("Sales Order {0} is Submitted", [r.message.name])
									: __("Invoice {0} is Submitted", [r.message.name]),
							color: "success",
						});
						frappe.utils.play_sound("submit");

						updateLocalStock(vm.invoice_doc.items || []);
						vm.eventBus.emit("payment_completed", {
							customer: vm.invoice_doc.customer,
							redeemed_loyalty_points: vm.invoice_doc.redeemed_loyalty_points || 0,
							loyalty_discount_amount: vm.invoice_doc.loyalty_discount_amount || 0,
							invoice_name: r.message.name,
						});
						vm.eventBus.emit("refresh_drafts");
						vm.addresses = [];
						vm.eventBus.emit("clear_invoice");
						vm.eventBus.emit("reset_posting_date");
						vm.back_to_invoice();
					},
					fail: function (error) {
						console.error("Invoice submission failed (network error):", error);

						vm.loading = false;
						vm.highlightSubmit = false;
						vm.eventBus.emit("show_message", {
							title: __(
								"Network error while submitting invoice. Please check your connection and try again.",
							),
							color: "error",
						});
						frappe.utils.play_sound("error");
					},
					error: function (error) {
						console.error("Invoice submission error:", error);

						vm.loading = false;
						vm.highlightSubmit = false;
						vm.eventBus.emit("show_message", {
							title: __("An error occurred while submitting the invoice. Please try again."),
							color: "error",
						});
						frappe.utils.play_sound("error");
					},
				});
			},
		set_full_amount(idx) {
			const isReturn = this.invoice_doc.is_return || this.invoiceType === "Return";
			const totalAmount = this.getEffectiveInvoiceTotal();

			const payment = this.invoice_doc.payments.find((p) => p.idx === idx);
			if (!payment) return;

			// ONLY update clicked payment
			let remaining = this.diff_payment;

			if (remaining <= 0) return;

			let amount = isReturn ? -Math.abs(remaining) : remaining;

			payment.amount = this.roundByLastDigit(amount, this.currency_precision);

			if (payment.base_amount !== undefined) {
				payment.base_amount = payment.amount;
			}
		},

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
				payment.amount = null;
			});
		},
		async load_print_page() {
			if (!this.invoice_doc || !this.invoice_doc.name || this.invoice_doc.name === "undefined") {
				this.eventBus.emit("show_message", {
					title: __("Cannot print: Invoice not saved properly"),
					color: "error",
				});
				return;
			}

			const invoice_doc = JSON.parse(JSON.stringify(this.invoice_doc));

			const print_format =
				this.pos_profile.posa_dot_matrix_print_format ||
				this.pos_profile.print_format_for_online ||
				this.pos_profile.print_format;
			// POS should always print without letterhead.
			const no_letterhead = 1;
			const doctype = this.pos_profile.create_pos_invoice_instead_of_sales_invoice
				? "POS Invoice"
				: "Sales Invoice";

			const is_raw_format = await this.is_raw_print_format(print_format);
			if (is_raw_format) {
				await this.print_raw_commands(invoice_doc, doctype, print_format);
				return;
			}

			const url =
				frappe.urllib.get_base_url() +
				"/printview?doctype=" +
				encodeURIComponent(doctype) +
				"&name=" +
				encodeURIComponent(this.invoice_doc.name) +
				"&trigger_print=1" +
				"&format=" +
				encodeURIComponent(print_format) +
				"&no_letterhead=" +
				no_letterhead;

			if (this.pos_profile.posa_silent_print) {
				silentPrint(url);
			} else {
				const printWindow = window.open(url, "Print");
				if (printWindow) {
					printWindow.addEventListener(
						"load",
						function () {
							printWindow.print();
						},
						{ once: true },
					);
				} else {
					this.eventBus.emit("show_message", {
						title: __("Print window blocked. Please allow popups and try again."),
						color: "warning",
					});
				}
			}
		},
		async is_raw_print_format(print_format) {
			if (!print_format) {
				return false;
			}
			try {
				const r = await frappe.db.get_value("Print Format", print_format, "raw_printing");
				return !!(r && r.message && r.message.raw_printing);
			} catch (err) {
				console.warn("[Payment] Could not check raw_printing for format:", print_format, err);
				return false;
			}
		},
		async prepare_raw_print_before_submit(doctype, print_format) {
			try {
				await frappe.ui.form.qz_connect();
			} catch (err) {
				this.eventBus.emit("show_message", {
					title: __("QZ Tray connection failed. Please allow and retry."),
					color: "error",
				});
				return false;
			}

			const mapped = this.get_mapped_printer(doctype, print_format);
			const preselect = mapped && mapped[0] && mapped[0].printer ? mapped[0].printer : "";
			this.open_printer_mapping_dialog(doctype, print_format, preselect);
			return false;
		},
		get_print_format_printer_map() {
			try {
				return JSON.parse(localStorage.print_format_printer_map);
			} catch (e) {
				return {};
			}
		},
		get_mapped_printer(doctype, print_format) {
			const map = this.get_print_format_printer_map();
			if (map && map[doctype]) {
				return map[doctype].filter((row) => row.print_format === print_format);
			}
			return [];
		},
		open_printer_mapping_dialog(doctype, print_format, preselect_printer = "") {
			this.printer_mapping_context = { doctype, print_format };
			this.printer_error = "";
			this.selected_printer = preselect_printer || "";
			this.available_printers = [];
			this.printer_mapping_dialog = true;
			this.load_qz_printers();
		},
		async load_qz_printers() {
			this.printer_loading = true;
			this.printer_error = "";
			try {
				const printers = await frappe.ui.form.qz_get_printer_list();
				this.available_printers = Array.isArray(printers) ? printers : [];
				if (!this.available_printers.length) {
					this.printer_error = __("No printers found from QZ Tray.");
				}
			} catch (err) {
				this.printer_error = __("Failed to connect to QZ Tray.");
				console.error("[Payment] Failed to load QZ printers", err);
			} finally {
				this.printer_loading = false;
			}
		},
		save_printer_mapping() {
			const doctype = this.printer_mapping_context.doctype;
			const print_format = this.printer_mapping_context.print_format;
			const printer = this.selected_printer;

			if (!doctype || !print_format || !printer) {
				this.printer_error = __("Please select a printer.");
				return;
			}

			const map = this.get_print_format_printer_map();
			if (!map[doctype]) {
				map[doctype] = [];
			}

			map[doctype] = map[doctype].filter((row) => row.print_format !== print_format);
			map[doctype].push({
				print_format,
				printer,
			});

			localStorage.print_format_printer_map = JSON.stringify(map);
			this.printer_mapping_dialog = false;
			this.eventBus.emit("show_message", {
				title: __("Printer mapping saved."),
				color: "success",
			});

			if (this.pending_print_submit && this.pending_print_args) {
				const { event, payment_received, print } = this.pending_print_args;
				this.pending_print_submit = false;
				this.pending_print_args = null;
				this.$nextTick(() => {
					this.submit(event, payment_received, print, true);
				});
			}
		},
		async print_raw_commands(invoice_doc, doctype, print_format) {
			try {
				if (!invoice_doc || !invoice_doc.name) {
					this.eventBus.emit("show_message", {
						title: __("Cannot print: Invoice not available for raw printing."),
						color: "error",
					});
					return;
				}

				const mapped = this.get_mapped_printer(doctype, print_format);
				if (!mapped.length || !mapped[0] || !mapped[0].printer) {
					this.open_printer_mapping_dialog(doctype, print_format);
					return;
				}

				const out = await frappe.call({
					method: "frappe.www.printview.get_rendered_raw_commands",
					args: {
						doc: invoice_doc,
						print_format: print_format,
					},
				});

				const raw_commands = out && out.message && out.message.raw_commands;
				if (!raw_commands) {
					this.eventBus.emit("show_message", {
						title: __("Raw print commands are empty."),
						color: "error",
					});
					return;
				}

				await frappe.ui.form.qz_connect();
				const config = qz.configs.create(mapped[0].printer);
				await qz.print(config, [raw_commands]);
				frappe.ui.form.qz_success();
			} catch (err) {
				console.error("[Payment] Raw printing failed", err);
				frappe.ui.form.qz_fail(err);
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
							const amount = this.getEffectiveInvoiceTotal();
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
		convertReportRowsToObjects(msg) {
			if (!msg || !msg.keys || !msg.values) return [];

			const keyIndex = (keyName) => {
				const idx = msg.keys.findIndex((k) => {
					return String(k).replace(/`/g, "").endsWith(`.${keyName}`);
				});
				return idx;
			};

			const idx_name = keyIndex("name");
			const idx_sales_person_name = keyIndex("sales_person_name");
			const idx_parent_sales_person = keyIndex("parent_sales_person");
			const idx_is_group = keyIndex("is_group");
			const idx_enabled = keyIndex("enabled");

			return msg.values.map((row) => {
				const name = idx_name >= 0 ? row[idx_name] : row[0];
				const sales_person_name = (idx_sales_person_name >= 0 && row[idx_sales_person_name]) || name;
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

			frappe
				.call({
					method: "posawesome.posawesome.api.utilities.get_sales_person_names",
					callback: function (r) {
						if (!r || r.exc) {
							vm.sales_persons = vm.sales_persons || [];
							return;
						}

						let items = [];

						if (Array.isArray(r.message)) {
							items = r.message.map((sp) => ({
								value: sp.name,
								title: sp.sales_person_name || sp.name,
								...sp,
							}));
						} else if (r.message && r.message.keys && r.message.values) {
							items = vm.convertReportRowsToObjects(r.message);
						} else {
							try {
								items = (r.message || [])
									.map((sp) => {
										if (typeof sp === "string") {
											return { value: sp, title: sp, name: sp };
										} else if (sp && sp.name) {
											return {
												value: sp.name,
												title: sp.sales_person_name || sp.name,
												...sp,
											};
										} else {
											return null;
										}
									})
									.filter(Boolean);
							} catch (e) {
								items = [];
							}
						}

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
				const exists = this.sales_persons.find(
					(sp) => sp.value === defaultSP || sp.name === defaultSP,
				);
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
			const userSP = this.sales_persons.find(
				(sp) => sp.value === currentUser || sp.name === currentUser || sp.title === currentUser,
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
			const invoiceAmount = this.getEffectiveInvoiceTotal();
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

			// Calculate from posting_date instead of today
			const d =
				this.invoice_doc && this.invoice_doc.posting_date
					? new Date(this.invoice_doc.posting_date)
					: new Date();

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
		getEffectiveInvoiceTotal() {
			if (!this.invoice_doc) return 0;
			return this.payable_total;
		},
		// Get change amount for display
		get_change_amount() {
			return Math.max(0, this.total_payments - this.getEffectiveInvoiceTotal());
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
	created() {
		document.addEventListener("keydown", this.shortPay.bind(this));
		this.syncPendingInvoices();
		this.eventBus.on("network-online", this.syncPendingInvoices);
		// Also sync when the server connection is re-established
		this.eventBus.on("server-online", this.syncPendingInvoices);
	},
	mounted() {
		// Initialize corporate flag
		this.selected_customer_is_corporate = false;

		// Listen for explicit customer detail updates
		this.eventBus.on("update_customer_details", async (payload) => {
			await this.syncCorporateCustomerState(payload);
		});

		this.eventBus.on("send_invoice_doc_payment", async (invoice_doc) => {
			console.log("[Payment] send_invoice_doc_payment received, initializing...");
			this.invoice_doc = invoice_doc;
			this.items_signature = this.computeItemsSignature(this.invoice_doc?.items || []);
			await this.syncCorporateCustomerState(this.invoice_doc);
			if (this.invoice_doc) {
				const hasCarWashService = this.hasCarWashServiceForItems(this.invoice_doc.items || []);
				this.invoice_doc.custom_has_carwash_service = hasCarWashService ? 1 : 0;
				if (!hasCarWashService) {
					this.invoice_doc.custom_service_employee = null;
					this.invoice_doc.custom_service_employee_name = null;
					this.invoice_doc.custom_service_employee_designation = null;
					this.invoice_doc.custom_service_employee_department = null;
				}
				this.invoice_doc.loyalty_discount_amount =
					this.invoice_doc.loyalty_discount_amount || this.invoice_doc.loyalty_amount || 0;
				this.invoice_doc.redeemed_loyalty_points =
					this.invoice_doc.redeemed_loyalty_points || this.invoice_doc.redeem_loyalty_points || 0;
			}
			this.loyalty_amount = Number(
				this.invoice_doc?.loyalty_discount_amount || this.invoice_doc?.loyalty_amount || 0,
			);
			this.applyLoadedInvoiceTotals(this.invoice_doc);
			console.log("[Payment][DraftLoad] invoice snapshot", {
				net_total: this.invoice_doc?.net_total,
				total_taxes_and_charges: this.invoice_doc?.total_taxes_and_charges,
				grand_total: this.invoice_doc?.grand_total,
				taxes: this.invoice_doc?.taxes,
			});

			if (this.invoice_doc && this.invoice_doc.posting_date) {
				const posting_date = new Date(this.invoice_doc.posting_date);
				const due_date = this.invoice_doc.due_date ? new Date(this.invoice_doc.due_date) : null;

				if (!this.invoice_doc.due_date || due_date < posting_date) {
					const newDueDate = new Date(posting_date);
					newDueDate.setDate(newDueDate.getDate() + 30);
					this.invoice_doc.due_date = this.formatDate(newDueDate);
					console.log("[Payment] Initialized/Corrected due_date:", this.invoice_doc.due_date);
				}
			}

			if (!this.invoice_doc.payments) {
				this.invoice_doc.payments = [];
				console.log("[Payment] Created new payments array");
			}

			if (this.invoice_doc.payments.length === 0) {
				console.log("[Payment] Payments empty, loading from POS Profile");

				if (this.pos_profile && this.pos_profile.payments && this.pos_profile.payments.length > 0) {
					this.invoice_doc.payments = this.buildPaymentMethodsFromPosProfile(this.customer_info);
					console.log("[Payment] Loaded payment methods:", this.invoice_doc.payments);
				} else {
					console.warn("[Payment] POS Profile not available");
					this.invoice_doc.payments = [
						{
							name: "",
							mode_of_payment: "Cash",
							account: "",
							amount: null,
							base_amount: null,
							type: "Cash",
							idx: 1,
							default: 1,
						},
					];
				}
			}

			this.refreshPaymentMethodsForCustomer(this.customer_info, this.invoice_doc);
			console.log("[Payment] Payments initialized:", this.invoice_doc.payments);
			this.tryOpenPaymentDialog();

			const default_payment = this.invoice_doc.payments.find((payment) => payment.default === 1);
			this.is_credit_sale = !!(
				this.selected_customer_is_corporate &&
				this.pos_profile?.posa_allow_credit_sale &&
				!invoice_doc.is_return
			);
			this.is_write_off_change = false;

			if (invoice_doc.is_return) {
				this.is_return = true;
				this.is_credit_return = false;
				invoice_doc.payments.forEach((payment) => {
					payment.amount = null;
					payment.base_amount = null;
				});
			} else {
				this.is_credit_return = false;
			}

			this.loyalty_amount = 0;
			this.redeemed_customer_credit = 0;

			if (invoice_doc.customer) {
				this.get_addresses();
			}

			this.get_sales_person_names();
			console.log("[Payment] Initialization complete");
		});

		this.eventBus.on("show_payment", (data) => {
			console.log("[Payment] show_payment event received with data:", data);

			if (data === "true") {
				this.pending_show_payment = true;
				this.tryOpenPaymentDialog();
			} else if (data === "false") {
				this._active_invoice_instance_id = null;
				this.pending_show_payment = false;
				return;
			}
		});

		this.eventBus.on("current_invoice_data", async (invoiceData) => {
			console.log("[Payment] current_invoice_data received");

			const sourceId = invoiceData && invoiceData._posa_invoice_instance_id;
			if (sourceId) {
				if (
					this._active_invoice_instance_id &&
					this._active_invoice_instance_id !== sourceId &&
					this.showDialog
				) {
					console.log("[Payment] Ignoring invoice data from inactive instance:", sourceId);
					return;
				}
				this._active_invoice_instance_id = sourceId;
			}

			if (this.showDialog) {
				console.log("[Payment] Ignoring invoice refresh while payment dialog is open");
				return;
			}

			this.applyLoadedInvoiceTotals(invoiceData);
			console.log("[Payment][DraftLoad] invoice snapshot", {
				net_total: invoiceData?.net_total,
				total_taxes_and_charges: invoiceData?.total_taxes_and_charges,
				grand_total: invoiceData?.grand_total,
				taxes: invoiceData?.taxes,
			});

			// Ensure payments array exists
			if (!invoiceData.payments) {
				invoiceData.payments = [];
			}

			if (invoiceData.payments.length === 0) {
				console.log("[Payment] Loading payment methods from POS Profile");

				if (this.pos_profile && this.pos_profile.payments && this.pos_profile.payments.length > 0) {
					invoiceData.payments = this.buildPaymentMethodsFromPosProfile(invoiceData);
					console.log("[Payment] Loaded payment methods:", invoiceData.payments);
				} else {
					// Fallback if POS Profile is not loaded yet
					console.warn("[Payment] POS Profile not available, using Cash as fallback");
					invoiceData.payments = [
						{
							name: "",
							mode_of_payment: "Cash",
							account: "",
							amount: null,
							base_amount: null,
							type: "Cash",
							idx: 1,
							default: 1,
						},
					];
				}
			}

			this.refreshPaymentMethodsForCustomer(invoiceData, invoiceData);

			if (!this.showDialog) {
				this.invoice_doc = invoiceData;
			} else if (this.invoice_doc) {
				// After the payment popup is open, keep the existing computed snapshot.
				// Only replace the item list if the source is changing; do not overwrite totals.
				if (invoiceData.items) {
					this.invoice_doc.items = invoiceData.items;
				}
			}

			this.items_signature = this.computeItemsSignature(invoiceData.items || []);

			// Reset payment amounts when invoice items change
			if (this.invoice_doc && invoiceData.items) {
				const oldItemCount = this.invoice_doc.items?.length || 0;
				const newItemCount = invoiceData.items?.length || 0;

				if (oldItemCount !== newItemCount) {
					console.log("[Payment] Item count changed, resetting payments");
					this.resetPaymentAmounts();
				}
			}
			this.grand_total = this.flt(invoiceData.grand_total || 0, this.currency_precision);
			this.rounded_total = this.flt(
				invoiceData.rounded_total || this.grand_total,
				this.currency_precision,
			);
			this.invoice_doc.total_amount = this.flt(this.grand_total, this.currency_precision);
			this.invoice_doc.to_be_paid = this.flt(this.rounded_total, this.currency_precision);
			this.customer = invoiceData.customer || "";
			await this.syncCorporateCustomerState(invoiceData);

			const item = invoiceData.items?.[0] || {};
			console.log("[Payment] item fields", {
				item_tax_rate: item.item_tax_rate,
				item_tax_template: item.item_tax_template,
				qty: item.qty,
				rate: item.rate,
				amount: item.amount,
				net_rate: item.net_rate,
				net_amount: item.net_amount,
				price_list_rate: item.price_list_rate,
			});

			// Set payment amount
			this.payment_amount = this.payable_total;
			console.log("[Payment] Payment amount set to:", this.payment_amount);

			// Force UI update
			this.$nextTick(() => {
				this.$forceUpdate();
			});

			this.tryOpenPaymentDialog();
		});

		this.eventBus.on("register_pos_profile", (data) => {
			console.log("[Payment] register_pos_profile received");
			this.pos_profile = data.pos_profile;
			this.stock_settings = data.stock_settings || {};
			this.get_mpesa_modes();
			this.get_sales_person_names();

			this.$nextTick(() => {
				if (this.pos_profile && this.pos_profile.posa_default_sales_person) {
					this.sales_person = this.pos_profile.posa_default_sales_person;
					console.log("[Payment] Auto-selected sales person:", this.sales_person);
				}
			});
		});

		this.eventBus.on("add_the_new_address", (data) => {
			console.log("[Payment] add_the_new_address received");
			this.addresses.push(data);
			this.$forceUpdate();
		});

		this.eventBus.on("update_invoice_type", (data) => {
			console.log("[Payment] update_invoice_type received:", data);
			this.invoiceType = data;
			if (this.invoice_doc && data !== "Order") {
				this.invoice_doc.posa_delivery_date = null;
				this.invoice_doc.posa_notes = null;
				this.invoice_doc.shipping_address_name = null;
			} else if (this.invoice_doc && data === "Order") {
				this.new_delivery_date = this.formatDateDisplay(frappe.datetime.now_date());
				this.update_delivery_date();
			}
			if (this.invoice_doc && data === "Return") {
				this.invoice_doc.is_return = 1;
				this.ensureReturnPaymentsAreNegative();
				this.is_credit_return = false;
			}
		});

		this.eventBus.on("update_customer", async (customer) => {
			console.log("[Payment] update_customer received:", customer);
			if (this.customer !== customer) {
				this.customer_credit_dict = [];
				this.redeem_customer_credit = false;
				this.is_cashback = true;
				this.is_credit_return = false;
			}

			this.customer = customer;
			await this.syncCorporateCustomerState(customer);
			this.refreshPaymentMethodsForCustomer(this.customer_info, this.invoice_doc);
			console.log(
				"[Payment] update_customer set selected_customer_is_corporate:",
				this.selected_customer_is_corporate,
			);
		});

		this.eventBus.on("set_pos_settings", (data) => {
			console.log("[Payment] set_pos_settings received");
			this.pos_settings = data;
		});

		this.eventBus.on("set_customer_info_to_edit", (data) => {
			console.log("[Payment] set_customer_info_to_edit received");
			this.customer_info = data;

			// ATTACH LOYALTY PROGRAM TO INVOICE
			if (this.invoice_doc && data?.loyalty_program) {
				this.invoice_doc.loyalty_program = data.loyalty_program;
			}
		});

		this.eventBus.on("set_mpesa_payment", (data) => {
			console.log("[Payment] set_mpesa_payment received");
			this.set_mpesa_payment(data);
		});

		this.eventBus.on("clear_invoice", () => {
			console.log("[Payment] clear_invoice received");
			this.resetPaymentData();
			this.resetPaymentAmounts();
		});
	},
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
.payments-panel {
	width: 100%;
}

/* DESKTOP (1920px+) */
@media (min-width: 1920px) {
	.payments-panel :deep(.payment-method-btn) {
		padding: 12px 16px;
		font-size: 13px;
		min-height: 44px;
	}

	.payments-panel :deep(.payment-amount-field) {
		font-size: 13px;
	}

	.payments-panel :deep(.payment-input) {
		padding: 10px 12px;
	}

	.payments-panel :deep(.payment-summary) {
		padding: 12px;
		font-size: 13px;
	}
}

/* LAPTOP (1280px - 1919px) */
@media (min-width: 1280px) and (max-width: 1919px) {
	.payments-panel :deep(.payment-method-btn) {
		padding: 10px 12px;
		font-size: 12px;
		min-height: 40px;
	}

	.payments-panel :deep(.payment-amount-field) {
		font-size: 12px;
	}

	.payments-panel :deep(.payment-input) {
		padding: 8px 10px;
	}

	.payments-panel :deep(.payment-summary) {
		padding: 10px;
		font-size: 12px;
	}

	/* Reduce button grid columns */
	.payments-panel :deep(.payment-methods) {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 8px;
	}
}

/* Payment method chips */
.payments-panel :deep(.payment-chip) {
	padding: 6px 12px;
	font-size: 12px;
}

@media (max-width: 1400px) {
	.payments-panel :deep(.payment-chip) {
		padding: 4px 10px;
		font-size: 11px;
	}
}

/* Payment text inputs */
.payments-panel :deep(.v-text-field) {
	margin: 8px 0;
}

.payments-panel :deep(.v-field) {
	border-radius: 6px;
}

/* Payment total section */
.payments-panel :deep(.payment-total) {
	padding: 12px;
	background-color: #f5f5f5;
	border-radius: 6px;
	margin-top: 12px;
}

.payments-panel :deep(.payment-total-label) {
	font-size: 12px;
	font-weight: 600;
}

.payments-panel :deep(.payment-total-amount) {
	font-size: 18px;
	font-weight: 700;
	color: #1976d2;
}

@media (max-width: 1400px) {
	.payments-panel :deep(.payment-total) {
		padding: 10px;
		margin-top: 10px;
	}

	.payments-panel :deep(.payment-total-amount) {
		font-size: 16px;
	}
}

@media (max-width: 1400px) {
	.payments-panel :deep(.v-text-field) {
		margin: 6px 0;
	}
}
/* Further compact at 1350px */
@media (max-width: 1400px) {
	.payments-panel :deep(.payment-method-btn) {
		padding: 8px 10px;
		font-size: 11px;
		min-height: 36px;
	}

	.payments-panel :deep(.payment-input) {
		padding: 6px 8px;
		font-size: 11px;
	}

	.payments-panel :deep(.payment-summary) {
		padding: 8px;
		font-size: 11px;
	}

	.payments-panel :deep(.payment-methods) {
		grid-template-columns: repeat(2, 1fr);
		gap: 6px;
	}
}

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
	font-size: 1rem !important;
	letter-spacing: 1px !important;
	height: 44px !important;
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
	font-size: 0.95rem !important;
	height: 40px !important;
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
		height: 50px !important;
		font-size: 1rem !important;
	}

	.submit-text {
		font-size: 1.1rem;
	}

	.cancel-btn {
		height: 44px !important;
		font-size: 0.9rem !important;
	}

	.menu-item {
		min-height: 56px !important;
		padding: 10px 14px !important;
	}
}

/* ================= PAYMENT GRID ================= */

/* Stack payment methods one below another */
.payment-methods-grid {
	display: grid;
	grid-template-columns: 1fr;
	gap: 4px;
}

/* Tighten cards */
.payment-method-card {
	width: 100%;
	padding: 6px 8px;
	min-height: 36px;
}

.method-title {
	font-size: 11px;
	font-weight: 600;
}

.method-input {
	max-width: 70px;
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
:deep([data-theme="dark"]) .dark-field,
:deep(.v-theme--dark) .dark-field {
	background-color: #1e1e1e !important;
}

:deep([data-theme="dark"]) .dark-field :deep(.v-field__input),
:deep(.v-theme--dark) .dark-field :deep(.v-field__input),
:deep([data-theme="dark"]) .dark-field :deep(input),
:deep(.v-theme--dark) .dark-field :deep(input),
:deep([data-theme="dark"]) .dark-field :deep(.v-label),
:deep(.v-theme--dark) .dark-field :deep(.v-label),
:deep([data-theme="dark"]) .dark-field .v-field__input,
:deep(.v-theme--dark) .dark-field .v-field__input,
:deep([data-theme="dark"]) .dark-field input,
:deep(.v-theme--dark) .dark-field input,
:deep([data-theme="dark"]) .dark-field .v-label,
:deep(.v-theme--dark) .dark-field .v-label {
	color: #fff !important;
}

:deep([data-theme="dark"]) .dark-field :deep(.v-field__overlay),
:deep(.v-theme--dark) .dark-field :deep(.v-field__overlay),
:deep([data-theme="dark"]) .dark-field .v-field__overlay,
:deep(.v-theme--dark) .dark-field .v-field__overlay {
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
	height: 90vh !important;
	max-height: 90vh !important;
	overflow: hidden !important;
	border-radius: 8px !important;
	margin: 0 !important;
	padding: 0 !important;
	box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08) !important;
	box-sizing: border-box;
}

.payments-header {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 8px 12px;
	background: linear-gradient(90deg, #00897b, #00796b) !important;
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
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	margin: 0;
}
.payments-header-title {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0;
	margin: 0;
}
.payments-header-right {
	width: 48px;
	display: flex;
	align-items: center;
	justify-content: center;
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
	padding-bottom: 120px;
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
	padding: 6px 10px;
	box-shadow: 0 -6px 14px rgba(0, 0, 0, 0.06);
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
	font-size: 1rem !important;
	height: 44px !important;
}
.cancel-btn {
	font-weight: 600 !important;
	font-size: 0.95rem !important;
	height: 40px !important;
}

@media (max-width: 760px) {
	.payment-card-wrapper .v-card {
		height: 78vh !important;
		max-height: 78vh !important;
	}
	.payment-card-wrapper .overflow-y-auto {
		padding-bottom: 180px !important;
	}
	.payments-header {
		padding: 6px 10px !important;
		min-height: 48px;
	}
	.payment-modal-container {
		padding: 6px;
	}
	.footer-actions {
		width: calc(100% - 12px);
		max-width: 720px;
	}
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

.v-dialog__content > *,
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
:deep .submit-menu,
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
	box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16) !important;
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

.payment-summary-hero {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 8px;
	margin-bottom: 8px;
	padding-left: 12px;
	padding-right: 12px;
}

/* Main box */
.summary-box {
	padding: 4px 8px; /* ⬅ reduced height */
	border-radius: 12px; /* slightly tighter */
	color: #fff;
	display: flex;
	flex-direction: column;
	justify-content: center;
	min-height: 42px; /* ⬅ controlled compact height */
}

/* Paid (green) */
.summary-box.paid {
	background: linear-gradient(135deg, #16a34a, #22c55e);
}

/* Due (red) */
.summary-box.due {
	background: linear-gradient(135deg, #dc2626, #ef4444);
}

/* Label */
.summary-box .label {
	font-size: 11px;
	font-weight: 700; /* ⬅ bold label */
	line-height: 1.1;
	opacity: 0.95;
}

/* Value */
.summary-box .value {
	font-size: 15px; /* slightly smaller */
	font-weight: 800; /* ⬅ strong bold for amount */
	line-height: 1.2;
	margin-top: 2px;
}

.payment-summary-card {
	background: #000 !important;
	border-radius: 10px;
	padding: 14px 16px;
	margin-bottom: 10px;
	border: 1px solid #e5e7eb;
}

.summary-label {
	font-size: 13px;
	font-weight: 500;
	color: #6b7280;
}

.summary-value {
	font-size: 22px;
	font-weight: 700;
	line-height: 1.2;
}

.success-text {
	color: #16a34a;
}

.danger-text {
	color: #dc2626;
}

.payment-method-card {
	min-height: 36px;
	padding: 6px 8px;
	border-radius: 8px;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.payment-method-card:hover {
	background: #f0f7ff;
	border-color: #2563eb;
}

.payment-method-card.active {
	border-color: #16a34a;
	background: #f0fdf4;
}

.payment-method-card.disabled {
	opacity: 0.6;
	pointer-events: none;
}

.method-left {
	display: flex;
	align-items: center;
	gap: 8px;
	flex: 1;
}

.method-title {
	font-size: 11px;
	font-weight: 600;
}

.payment-method-card .v-icon {
	font-size: 16px !important;
}

.method-amount {
	font-size: 11px;
	color: #6b7280;
	display: none;
}

.method-input {
	min-width: 120px;
	max-width: 140px;
}
.method-input :deep(.v-field) {
	min-height: 28px !important;
}
.method-input :deep(input) {
	font-size: 14px;
	padding: 2px 8px;
	text-align: left;
}
.method-input :deep(.v-field__prefix) {
	margin-right: 6px;
	font-size: 11px;
	white-space: nowrap;
}
.payment-summary-row {
	margin-bottom: 8px;
}

.payment-summary-card {
	padding: 8px 10px;
	font-size: 0.9rem;
}

.credit-sale-banner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 12px 14px;
	background: #ecfdf5;
	border: 1px solid #34d399;
	border-radius: 14px;
	margin: 12px 0;
}

.credit-sale-banner .title {
	font-size: 15px;
	font-weight: 600;
}

.credit-sale-banner .desc {
	font-size: 12px;
	color: #065f46;
}

.payment-summary-fixed {
	position: sticky;
	top: 0;
	z-index: 5;
	background: var(--v-theme-surface);
	padding-bottom: 10px;
}

.sleek-field .v-field-label {
	font-size: 13px;
	font-weight: 600;
	color: #374151;
	opacity: 1;
}

.sleek-field input {
	font-size: 14px;
	font-weight: 700;
	color: #111827;
}

.sleek-field .v-field {
	border-radius: 8px;
	border: 1px solid rgba(0, 0, 0, 0.15);
}

.sleek-field input {
	letter-spacing: 0.3px;
}

.payment-content-container {
	flex: 1;
	overflow: hidden; /* parent should NOT scroll */
}
@media (min-width: 1400px) {
	.payment-left-column {
		max-height: calc(90vh - 130px);
	}
}

.payment-modal-container {
	height: 90vh;
	display: flex;
	flex-direction: column;
}

.payment-card-wrapper,
.payment-content,
.v-card {
	height: 100%;
}

.payment-card-wrapper {
	width: 80%;
	max-width: 100%;
}
.payment-card-wrapper {
	font-size: clamp(12px, 0.9vw, 14px);
}
.summary-box .value {
	font-size: clamp(14px, 1.6vw, 18px);
}
.summary-box .label,
.sleek-field .v-field-label {
	font-size: clamp(10px, 0.8vw, 12px);
}
.sleek-field input {
	font-size: clamp(12px, 0.9vw, 13px);
}
.payment-left-column {
	max-height: calc(90vh - 130px); /* header + summary + footer */
	overflow-y: auto;
	padding-right: 6px;
}

/* smooth scrollbar */
.payment-left-column::-webkit-scrollbar {
	width: 6px;
}
.payment-left-column::-webkit-scrollbar-thumb {
	background: #cbd5e1;
	border-radius: 4px;
}
</style>
