<template>
	<v-card
		:class="[
			'cards mb-0 mt-1 py-0 px-1 rounded-lg compact-summary',
			isDarkTheme ? '' : 'bg-grey-lighten-4',
		]"
		:style="isDarkTheme ? 'background-color:#1E1E1E;' : ''"
	>
		<v-row dense class="w-100">
			<!-- divider removed to save height -->

			<!-- Totals and Actions Section -->
			<v-col cols="12">
				<v-row dense>
					<!-- Left Side - Summary Fields -->
					<v-col cols="12" md="7">
						<v-row dense>
							<!-- Odometer Reading Field (Only shown when Engine Oil item is present) -->
							<v-col :cols="showEmployeeSelection ? 6 : 12" v-if="showOdometerField">
								<v-text-field
									v-model="odometerReading"
									:label="__('Odometer Reading (km)')"
									prepend-inner-icon="mdi-speedometer"
									variant="solo"
									density="compact"
									color="primary"
									type="text"
									inputmode="numeric"
									class="summary-field"
									:rules="[isNumber]"
									@update:model-value="emitOdometerData"
								/>
							</v-col>
							<!-- Service Employee Selection (for car wash services) -->
							<v-col :cols="showOdometerField ? 6 : 12" v-if="showEmployeeSelection">
								<v-autocomplete
									:key="employeeFieldKey"
									ref="serviceEmployeeAutocomplete"
									v-model="selectedEmployee"
									v-model:menu="employeeMenu"
									:items="filteredEmployees"
									:loading="loadingEmployees"
									:label="__('Select Service Employee')"
									item-title="display_label"
									item-value="employee_id"
									prepend-inner-icon="mdi-account-hard-hat"
									variant="solo"
									density="compact"
									color="primary"
									clearable
									class="summary-field employee-summary-field"
									:no-filter="true"
									:menu-props="{ maxHeight: 360, closeOnContentClick: false }"
									@update:model-value="handleEmployeeChange"
									@update:menu="handleEmployeeMenuToggle"
									@click:clear="handleEmployeeClear"
								>
									<template v-slot:prepend-item>
										<div class="px-3 pt-3 pb-2" @mousedown.stop @click.stop>
											<v-text-field
												ref="employeeSearchInput"
												v-model="employeeSearch"
												autocomplete="off"
												variant="outlined"
												density="compact"
												hide-details
												clearable
												class="employee-search-input"
												:placeholder="__('Search by employee ID or name')"
												prepend-inner-icon="mdi-magnify"
												:loading="loadingEmployees"
												@click.stop
												@focus="employeeMenu = true"
												@blur="handleEmployeeSearchBlur"
												@keydown.stop
												@keypress.stop
												@keyup.stop
												@input.stop
												@update:model-value="handleEmployeeSearchInput"
											/>
											<div
												v-if="employeeSearch && employeeSearch.length < 3"
												class="text-caption mt-1 employee-search-helper"
											>
												{{ __("Type at least 3 characters to search employees") }}
											</div>
										</div>
									</template>
									<template v-slot:item="{ props, item }">
										<v-list-item
											v-bind="props"
											:title="
												item.raw.display_label || buildEmployeeDisplayLabel(item.raw)
											"
										>
											<template v-slot:prepend>
												<v-avatar size="32" color="primary" class="mr-2">
													<v-img v-if="item.raw.image" :src="item.raw.image" />
													<v-icon v-else color="white">mdi-account</v-icon>
												</v-avatar>
											</template>
											<template v-slot:subtitle>
												<span class="text-caption">
													{{ buildEmployeeSubtitle(item.raw) }}
												</span>
											</template>
										</v-list-item>
									</template>
									<template v-slot:selection="{ item }">
										<div class="employee-selection">
											<span
												v-if="selectedEmployeeDisplayLabel"
												class="employee-selection-name"
											>
												{{ selectedEmployeeDisplayLabel }}
											</span>
											<span v-else class="employee-selection-placeholder">
												{{ __("Select Service Employee") }}
											</span>
											<span
												v-if="selectedEmployeeDetails"
												class="employee-selection-id"
											>
												({{
													selectedEmployeeDetails.custom_employee_id ||
													selectedEmployeeDetails.employee_id ||
													selectedEmployeeDetails.name
												}})
											</span>
										</div>
									</template>
									<template v-slot:no-data>
										<v-list-item v-if="employeeSearch && employeeSearch.length < 3">
											<v-list-item-title class="text-caption">
												{{ __("Type at least 3 characters to search employees") }}
											</v-list-item-title>
										</v-list-item>
										<v-list-item v-else>
											<v-list-item-title class="text-caption">
												{{ __("No employees found") }}
											</v-list-item-title>
										</v-list-item>
									</template>
								</v-autocomplete>
							</v-col>

							<!-- Total Qty -->
							<v-col cols="6">
								<v-text-field
									:model-value="Math.trunc(total_qty)"
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
									:model-value="formatByPrecision(additional_discount)"
									@update:model-value="formatByPrecision(handleAdditionalDiscountUpdate)"
									@change="apply_additional_discount"
									:label="__('Additional Discount')"
									prepend-inner-icon="mdi-cash-minus"
									variant="solo"
									density="compact"
									color="warning"
									:prefix="pos_profile ? currencySymbol(pos_profile.currency) : ''"
									:disabled="
										!pos_profile ||
										!pos_profile.posa_allow_user_to_edit_additional_discount ||
										!!discount_percentage_offer_name
									"
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
									:disabled="
										!pos_profile.posa_allow_user_to_edit_additional_discount ||
										!!discount_percentage_offer_name
									"
									class="summary-field"
								/>
							</v-col>

							<!-- Items Discounts -->
							<v-col cols="6">
								<v-text-field
									:model-value="formatByPrecision(total_items_discount_amount)"
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
							<v-text-field
								:model-value="formatByPrecision(finalTotal)"
								:label="__('Total')"
								prepend-inner-icon="mdi-cash"
								variant="solo"
								density="compact"
								color="success"
								class="summary-field"
								readonly
								:prefix="currencySymbol(displayCurrency)"
							/>

							<!-- Manual Round Off + Frequent Cards (side by side) -->
							<v-col cols="6">
								<v-text-field
									v-model="manual_round_off"
									:label="__('Manual Round Off')"
									prepend-inner-icon="mdi-plus-minus"
									variant="solo"
									density="compact"
									color="info"
									class="summary-field manual-round-off-field"
									type="text"
									inputmode="decimal"
									:prefix="currencySymbol(displayCurrency)"
									@change="onManualRoundOffChange"
								/>
							</v-col>
							<v-col cols="6">
								<v-btn
									block
									color="orange"
									theme="dark"
									prepend-icon="mdi-cards"
									@click="handleFrequentCards"
									class="summary-btn"
									:loading="frequentCardsLoading"
								>
									<span class="flex-grow-1">{{ __("FREQUENT CARDS") }}</span>
									<v-chip
										v-if="completedCardsCount > 0"
										size="small"
										color="white"
										text-color="orange"
										class="ml-2"
									>
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
							<v-col cols="6">
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
							<v-col cols="6">
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
												<p :class="['text-h6 font-weight-bold mb-0 text-purple']">
													{{ formatFloat(loyaltyPoints, 0) }} pts
												</p>
											</v-col>
											<v-col cols="auto" class="text-end">
												<p
													class="text-h6 font-weight-bold text-purple mb-0 loyalty-currency-value"
												>
													{{
														formatCurrency(
															loyaltyPoints * conversionFactor,
															moneyPrecision,
														)
													}}
													{{ displayCurrency }}
												</p>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>

							<!-- Item Group Bulk Discount Section -->
							<v-col cols="12" v-if="itemGroupsList && itemGroupsList.length > 0">
								<v-card class="item-group-discount-card" elevation="2">
									<v-card-text class="pa-4">
										<!-- Header with Icon and Title -->
										<div
											class="d-flex align-center justify-space-between item-group-header-row"
										>
											<div class="d-flex align-center">
												<v-avatar
													color="info"
													size="40"
													class="mr-3 item-group-avatar"
												>
													<v-icon color="white" size="24"
														>mdi-folder-multiple</v-icon
													>
												</v-avatar>
												<div>
													<p class="text-subtitle-2 font-weight-bold mb-0">
														{{ __("Item Group Discounts") }}
													</p>
												</div>
											</div>

											<div
												v-if="itemGroupDiscountEntries.length === 1"
												class="discounts-list-compact"
											>
												<v-chip
													closable
													size="x-small"
													color="info"
													variant="tonal"
													class="discount-chip-compact"
													@click:close="
														removeItemGroupDiscount(
															itemGroupDiscountEntries[0][0],
														)
													"
												>
													<span class="font-weight-600">
														{{ itemGroupDiscountEntries[0][0] }}:
														{{ itemGroupDiscountEntries[0][1] }}%
													</span>
												</v-chip>
											</div>

											<div
												v-else-if="itemGroupDiscountEntries.length > 1"
												class="discounts-list-compact"
											>
												<v-menu location="bottom end" offset="6">
													<template #activator="{ props }">
														<v-chip
															v-bind="props"
															size="x-small"
															color="info"
															variant="tonal"
															class="discount-chip-compact discount-dropdown-chip"
														>
															{{ itemGroupDiscountEntries.length }}
															{{ __("Discounts") }}
															<v-icon end size="14">mdi-chevron-down</v-icon>
														</v-chip>
													</template>
													<v-list density="compact" class="discount-dropdown-list">
														<v-list-item
															v-for="[
																group,
																discount,
															] in itemGroupDiscountEntries"
															:key="group"
															:title="`${group}: ${discount}%`"
														>
															<template #append>
																<v-btn
																	icon="mdi-close-circle-outline"
																	size="x-small"
																	variant="text"
																	color="error"
																	@click.stop="
																		removeItemGroupDiscount(group)
																	"
																/>
															</template>
														</v-list-item>
													</v-list>
												</v-menu>
											</div>
											<v-btn
												size="small"
												color="info"
												variant="flat"
												prepend-icon="mdi-plus"
												@click="openItemGroupDiscountDialog"
												class="add-discount-btn"
											>
												{{ __("Add") }}
											</v-btn>
										</div>

										<!-- Total Group Discount Amount -->
										<!-- <v-divider class="my-3" />
										<v-row align="center" no-gutters class="discount-summary">
											<v-col cols="auto">
												<p class="text-caption text-grey-darken-1 mb-0">
													{{ __("Total Discount Value") }}
												</p>
											</v-col>
											<v-spacer></v-spacer>
											<v-col cols="auto" class="text-right">
												<p class="text-h6 font-weight-bold mb-0 text-info">
													{{ currencySymbol(displayCurrency) }}{{
														formatFloat(total_items_discount_amount) }}
												</p>
											</v-col>
										</v-row> -->
									</v-card-text>
								</v-card>
							</v-col>

							<!-- Item Group Discount Dialog -->
							<v-dialog
								v-model="showItemGroupDiscountDialog"
								max-width="480px"
								width="480px"
								persistent
							>
								<v-card :style="isDarkTheme ? 'background-color:#1E1E1E;' : ''">
									<v-card-title class="text-h6 pb-2 pt-4 px-6">
										<v-row align="center" no-gutters>
											<v-avatar color="info" size="36" class="mr-3">
												<v-icon color="white" size="20">mdi-folder-multiple</v-icon>
											</v-avatar>
											<span>{{ __("Apply Group Discount") }}</span>
											<v-spacer></v-spacer>
											<v-btn
												icon
												size="small"
												variant="text"
												@click="showItemGroupDiscountDialog = false"
											>
												<v-icon>mdi-close</v-icon>
											</v-btn>
										</v-row>
									</v-card-title>

									<v-divider></v-divider>

									<v-card-text class="px-6 py-4">
										<!-- Select Item Group -->
										<v-select
											v-model="selectedItemGroupForDiscount"
											:items="itemGroupsList"
											:label="__('Select Item Group')"
											prepend-inner-icon="mdi-folder"
											variant="outlined"
											density="comfortable"
											color="info"
											class="mb-4"
											clearable
										/>

										<!-- Discount Percentage Input -->
										<v-text-field
											v-model.number="discountPercentageByGroup"
											:label="__('Discount Percentage')"
											type="number"
											min="0"
											max="100"
											step="0.5"
											prepend-inner-icon="mdi-percent"
											variant="outlined"
											density="comfortable"
											color="info"
											suffix="%"
											:rules="[
												(v) => v >= 0 || __('Cannot be negative'),
												(v) => v <= 100 || __('Cannot exceed 100%'),
											]"
										/>

										<!-- Preview Alert -->
										<v-alert
											v-if="
												selectedItemGroupForDiscount && discountPercentageByGroup > 0
											"
											type="info"
											variant="tonal"
											density="compact"
											icon="mdi-information-outline"
											class="mt-4 mb-0"
										>
											<p class="text-caption mb-0">
												<strong>{{ selectedItemGroupForDiscount }}</strong>
												{{ __("items will receive a") }}
												<strong>{{ discountPercentageByGroup }}%</strong>
												{{ __("discount") }}
											</p>
										</v-alert>

										<!-- No Selection Alert -->
										<v-alert
											v-else-if="!selectedItemGroupForDiscount"
											type="warning"
											variant="tonal"
											density="compact"
											icon="mdi-alert-outline"
											class="mt-4 mb-0"
										>
											<p class="text-caption mb-0">
												{{
													__(
														"Please select an item group and enter a discount percentage",
													)
												}}
											</p>
										</v-alert>
									</v-card-text>

									<v-divider></v-divider>

									<v-card-actions class="px-6 py-4">
										<v-spacer></v-spacer>
										<v-btn
											color="error"
											variant="text"
											@click="showItemGroupDiscountDialog = false"
										>
											{{ __("Cancel") }}
										</v-btn>
										<v-btn
											color="info"
											variant="flat"
											:disabled="
												!selectedItemGroupForDiscount ||
												discountPercentageByGroup <= 0
											"
											@click="applyItemGroupDiscount"
										>
											<v-icon left>mdi-check</v-icon>
											{{ __("Apply Discount") }}
										</v-btn>
									</v-card-actions>
								</v-card>
							</v-dialog>

							<!-- Max Discount Info -->
							<!-- <v-col cols="12" v-if="$parent.maxDiscountInfo">
								<v-card class="max-discount-display-card" elevation="2">
									<v-card-text class="pa-3">
										<v-row align="center" no-gutters>
											<v-col cols="auto" class="mr-3">
												<v-avatar color="teal" size="40">
													<v-icon color="white" size="22">mdi-percent</v-icon>
												</v-avatar>
											</v-col>

											<v-col>
												<p class="text-caption mb-0 text-grey-darken-1">
													Customer Type
												</p>
												<p class="text-subtitle-1 font-weight-bold mb-0">
													{{ $parent.maxDiscountInfo.customer_type }}
												</p>
											</v-col>

											<v-col cols="auto" class="text-right">
												<p class="text-caption mb-0 text-grey-darken-1">
													Max Discount
												</p>
												<p class="text-h6 font-weight-bold mb-0 text-teal">
													{{ $parent.maxDiscountInfo.invoice_max_discount }}%
												</p>
											</v-col>
										</v-row>
									</v-card-text>
								</v-card>
							</v-col>
							-->

							<!-- Select Sales Order Button (Conditional) -->
							<v-col
								cols="12"
								v-if="pos_profile && pos_profile.custom_allow_select_sales_order == 1"
							>
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
							<v-col
								cols="12"
								v-if="pos_profile && pos_profile.posa_allow_print_draft_invoices"
							>
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

							<!-- Cancel + Pay (Right Side, Highlighted) -->
							<v-col cols="12">
								<v-row dense class="summary-actions">
									<v-col cols="6">
										<v-btn
											block
											color="error"
											theme="dark"
											@click="handleCancelSale"
											class="summary-btn primary-action"
											:loading="cancelLoading"
											style="
												display: flex;
												align-items: center;
												justify-content: center;
											"
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
											class="summary-btn pay-btn primary-action"
											:loading="paymentLoading"
											style="
												display: flex;
												align-items: center;
												justify-content: center;
											"
										>
											<v-icon left size="18">mdi-credit-card</v-icon>
											{{ __("PAY") }}
										</v-btn>
									</v-col>
								</v-row>
							</v-col>
						</v-row>
					</v-col>
				</v-row>
			</v-col>
		</v-row>

		<!-- Loyalty Points Dialog (Redeem Only) -->
		<v-dialog v-model="showLoyaltyDialog" max-width="520px" width="520px" persistent>
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
										{{ formatCurrency(loyaltyPoints * conversionFactor, moneyPrecision) }}
									</p>
								</v-col>
							</v-row>
						</v-alert>

						<!-- Redeem Points Input -->
						<v-text-field
							v-model="pointsToRedeem"
							:label="__('Points to Redeem')"
							prepend-inner-icon="mdi-star-minus"
							variant="outlined"
							density="comfortable"
							color="purple"
							type="number"
							:rules="[
								isNumber,
								(v) => v <= loyaltyPoints || __('Cannot redeem more than available points'),
								(v) => v >= 0 || __('Points must be positive'),
							]"
							:hint="__('Enter points to redeem for a discount')"
							persistent-hint
						/>

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
										{{ formatCurrency(redemptionValue, moneyPrecision) }}
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
					<v-btn
						color="purple"
						variant="flat"
						:disabled="!isValidRedemption || redeemLoading"
						:loading="redeemLoading"
						@click="handleRedeemPoints"
					>
						<v-icon left>mdi-check</v-icon>
						{{ __("Apply Redemption") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>

		<!-- Frequent Cards Dialog (SEPARATE) -->
		<v-dialog v-model="showFrequentCardsDialog" max-width="720px" width="720px" persistent scrollable>
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
						<v-progress-linear
							v-if="loadingFrequentCards"
							indeterminate
							color="orange"
							class="mb-3"
						></v-progress-linear>

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
								<v-card
									:class="[
										'frequent-card',
										card.is_expired ? 'expired-card' : '',
										card.visits >= card.required_visits ? 'completed-card' : '',
									]"
									:elevation="card.visits >= card.required_visits ? 4 : 2"
									@click="handleCardClick(card)"
									:disabled="card.is_expired || applyingCard"
								>
									<v-card-text class="pa-4">
										<v-row align="center" no-gutters>
											<v-col cols="auto" class="mr-3">
												<v-avatar
													:color="
														card.is_expired
															? 'grey'
															: card.visits >= card.required_visits
																? 'success'
																: 'orange'
													"
													size="56"
												>
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
															<v-chip
																size="small"
																:color="
																	card.visits >= card.required_visits
																		? 'success'
																		: 'orange'
																"
															>
																{{ card.visits }}/{{ card.required_visits }}
																visits
															</v-chip>
														</v-col>
														<v-col>
															<v-progress-linear
																:model-value="
																	(card.visits / card.required_visits) * 100
																"
																:color="
																	card.visits >= card.required_visits
																		? 'success'
																		: 'orange'
																"
																height="6"
																rounded
															></v-progress-linear>
														</v-col>
													</v-row>
												</div>

												<!-- Status & Expiry -->
												<div>
													<v-chip
														v-if="card.is_expired"
														size="small"
														color="error"
														variant="flat"
													>
														<v-icon size="small" left>mdi-clock-alert</v-icon>
														{{ __("Expired") }}
													</v-chip>
													<v-chip
														v-else-if="card.visits >= card.required_visits"
														size="small"
														color="success"
														variant="flat"
													>
														<v-icon size="small" left>mdi-gift</v-icon>
														{{ __("Free Service Available!") }}
													</v-chip>
													<v-chip
														v-else
														size="small"
														color="grey"
														variant="outlined"
													>
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
						<v-alert
							v-if="hasCompletedCards"
							type="success"
							variant="tonal"
							density="compact"
							class="mt-4"
							icon="mdi-information"
						>
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
			allEmployees: [],
			selectedEmployee: null,
			selectedEmployeeDetails: null,
			employeeMenu: false,
			employeeSearch: "",
			employeeFieldKey: 0,
			loadingEmployees: false,
			employeeSearchDebounce: null,
			employeeSearchRequestId: 0,
			showEmployeeSelection: false,
			employeeLoadLockUntil: 0,
			employeeSelectionEpoch: 0,

			showOdometerField: false,
			odometerReading: null,
			odometerLoadLockUntil: 0,
			vehicleNumber: "",
			mobileNumber: "",

			manualRoundApplied: false,
			manual_round_off: 0,
			isResetting: false,

			itemGroupDiscounts: {},
			availableItemGroups: [],
			selectedItemGroupForDiscount: null,
			discountPercentageByGroup: 0,
			showItemGroupDiscountDialog: false,
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
		finalTotal() {
			const base = Number(this.subtotal || 0);
			const roundOff = Number(this.manual_round_off || 0);
			return Number((base + roundOff).toFixed(3));
		},

		selectedEmployeeDisplayLabel() {
			const employee =
				this.selectedEmployeeDetails || this.getSelectedEmployeeRecord(this.selectedEmployee);
			return employee ? this.buildEmployeeDisplayLabel(employee) : "";
		},

		filteredEmployees() {
			const query = (this.employeeSearch || "").trim().toLowerCase();
			if (!query || query.length < 3) {
				return this.employees;
			}

			const sourceEmployees = this.allEmployees.length ? this.allEmployees : this.employees;

			return sourceEmployees.filter((employee) => {
				const employeeId = this.normalizeEmployeeValue(
					employee.employee_id || employee.name,
				).toLowerCase();
				const employeeName = this.normalizeEmployeeValue(employee.employee_name).toLowerCase();
				const customEmployeeId = this.normalizeEmployeeValue(
					employee.custom_employee_id,
				).toLowerCase();
				const displayLabel = this.normalizeEmployeeValue(employee.display_label).toLowerCase();
				return (
					employeeId.includes(query) ||
					employeeName.includes(query) ||
					customEmployeeId.includes(query) ||
					displayLabel.includes(query)
				);
			});
		},

		itemGroupsList() {
			const itemBasedGroups = Array.isArray(this.$parent?.items)
				? this.$parent.items.map((item) => (item?.item_group || "").toString().trim()).filter(Boolean)
				: [];

			const sourceGroups =
				itemBasedGroups.length > 0
					? itemBasedGroups
					: Array.isArray(this.items_group) && this.items_group.length
						? this.items_group
						: this.availableItemGroups;

			return [...new Set((sourceGroups || []).map((g) => String(g || "").trim()).filter(Boolean))]
				.filter((group) => group.toUpperCase() !== "ALL")
				.sort((a, b) => a.localeCompare(b));
		},

		itemGroupSummary() {
			// Calculate totals per item group for display
			const summary = {};
			this.items_group.forEach((group) => {
				summary[group] = {
					discount: this.itemGroupDiscounts[group] || 0,
					itemCount: this.countItemsByGroup(group),
				};
			});
			return summary;
		},
		displayItemGroupDiscounts() {
			return Object.fromEntries(
				Object.entries(this.itemGroupDiscounts || {}).filter(([group]) => {
					const name = (group || "").toString().trim();
					return name.length > 0 && name.toLowerCase() !== "null";
				}),
			);
		},
		itemGroupDiscountEntries() {
			return Object.entries(this.displayItemGroupDiscounts);
		},

		maxInvoiceDiscount() {
			return this.$parent.maxDiscountInfo?.invoice_max_discount || 0;
		},
		decimalPrecision() {
			return Number(this.pos_profile?.posa_decimal_precision ?? 2);
		},
		moneyPrecision() {
			const candidates = [
				this.pos_profile?.posa_decimal_precision,
				typeof frappe !== "undefined" && frappe?.defaults?.get_default
					? frappe.defaults.get_default("currency_precision")
					: null,
			];

			for (const candidate of candidates) {
				const precision = Number(candidate);
				if (Number.isFinite(precision)) {
					return Math.max(precision, 3);
				}
			}

			return 3;
		},
		__() {
			return window.__ || ((str) => str);
		},
		isDarkTheme() {
			return this.$vuetify?.theme?.global?.current?.dark;
		},
		redemptionValue() {
			const points = parseFloat(this.pointsToRedeem) || 0;
			return Number((points * this.conversionFactor).toFixed(this.moneyPrecision));
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

		subtotal() {
			this.manual_round_off = 0;

			this.eventBus.emit("update_rounded_total", this.finalTotal);
		},

		additional_discount: {
			immediate: true,
			handler() {
				if (this.isResetting) return;

				const base = this.getAutoRoundedBase();

				if (!this.manualRoundApplied) {
					this.manual_total = base;
				}

				this.emitRoundedTotal();
			},
		},
	},
	methods: {
		getAutoRoundedBase() {
			return this.roundByLastTwoDecimals(this.subtotal || 0);
		},
		emitRoundedTotal() {
			this.eventBus.emit("update_rounded_total", this.manual_total);
		},

		roundByLastTwoDecimals(value) {
			const num = Number(value || 0);

			const intPart = Math.floor(num);
			const decimals = Math.round((num - intPart) * 1000); // 0–999
			const lastTwo = decimals % 100;

			let roundedDecimals;

			if (lastTwo >= 50) {
				// round UP last two digits
				roundedDecimals = decimals + (100 - lastTwo);
			} else {
				// round DOWN last two digits
				roundedDecimals = decimals - lastTwo;
			}

			// handle carry to next integer
			if (roundedDecimals >= 1000) {
				return Number((intPart + 1).toFixed(3));
			}

			return Number((intPart + roundedDecimals / 1000).toFixed(3));
		},

		countItemsByGroup(group) {
			// Count items in specific group
			return this.pos_profile && Array.isArray(this.items_group)
				? this.items_group.filter((g) => g === group).length
				: 0;
		},

		calculateGroupSubtotal(group) {
			// Calculate directly from items instead of emitting event
			if (!this.items || this.items.length === 0) {
				return 0;
			}

			// Access parent's items through $parent reference
			const parentItems = this.$parent?.items || [];

			const groupTotal = parentItems.reduce((sum, item) => {
				if ((item.item_group || "").trim() === group) {
					return sum + Number(item.qty || 0) * Number(item.rate || 0);
				}
				return sum;
			}, 0);

			return groupTotal;
		},

		openItemGroupDiscountDialog() {
			const currentGroup = (this.item_group || "").toString().trim();
			if (
				currentGroup &&
				currentGroup.toUpperCase() !== "ALL" &&
				this.itemGroupsList.includes(currentGroup)
			) {
				this.selectedItemGroupForDiscount = currentGroup;
			}
			this.showItemGroupDiscountDialog = true;
		},

		applyItemGroupDiscount() {
			if (this.selectedItemGroupForDiscount === "Engine Oil") {
				frappe.show_alert({
					message: this.__("Discounts are not allowed for Engine Oil items"),
					indicator: "red",
				});
				return;
			}

			if (!this.selectedItemGroupForDiscount) {
				frappe.show_alert({
					message: this.__("Please select an item group"),
					indicator: "warning",
				});
				return;
			}

			const groupName = (this.selectedItemGroupForDiscount || "").toString().trim();
			if (!groupName || groupName.toLowerCase() === "null") {
				frappe.show_alert({
					message: this.__("Please select a valid item group"),
					indicator: "warning",
				});
				return;
			}
			const discountPct = Number(this.discountPercentageByGroup || 0);

			if (discountPct < 0 || discountPct > 100) {
				frappe.show_alert({
					message: this.__("Discount must be between 0-100%"),
					indicator: "error",
				});
				return;
			}

			// Emit event to parent to apply discount to items (callback handles success/failure)
			this.eventBus.emit("apply_group_discount", {
				group: groupName,
				percentage: discountPct,
				callback: (result = {}) => {
					const applied = Number(result.applied || 0);
					const rejected = Number(result.rejected || 0);

					if (applied <= 0) {
						frappe.show_alert({
							message: this.__("Discount was not applied (validation failed)"),
							indicator: "red",
						});
						return;
					}

					this.itemGroupDiscounts[groupName] = discountPct;

					if (rejected > 0) {
						frappe.show_alert({
							message: this.__(
								`Discount applied to ${applied} items. ${rejected} items rejected due to limits.`,
							),
							indicator: "orange",
						});
					} else {
						frappe.show_alert({
							message: this.__(`${discountPct}% discount applied to ${groupName} items`),
							indicator: "green",
						});
					}
				},
			});

			// Recalculate totals
			this.$emit("update_discount_umount");

			// Reset and close
			this.discountPercentageByGroup = 0;
			this.selectedItemGroupForDiscount = null;
			this.showItemGroupDiscountDialog = false;
		},

		removeItemGroupDiscount(group) {
			// Remove discount from specific group
			delete this.itemGroupDiscounts[group];

			// Emit event to parent to remove discount
			this.eventBus.emit("remove_group_discount", {
				group: group,
			});

			this.$emit("update_discount_umount");

			frappe.show_alert({
				message: this.__(`Discount removed from ${group} items`),
				indicator: "orange",
			});
		},

		onManualRoundOffChange() {
			const roundOff = Number(this.manual_round_off || 0);

			// Manual round off is ONLY a delta
			this.eventBus.emit("update_manual_round_off", roundOff);

			// Tell payment & backend the final total
			this.eventBus.emit("update_rounded_total", this.finalTotal);

			// Refresh payment UI
			this.eventBus.emit("force_payment_refresh");
		},

		resetAfterPayment() {
			// Core sale state
			this.resetEmployeeSelectionState();

			this.showOdometerField = false;
			this.odometerReading = null;
			this.vehicleNumber = "";
			this.mobileNumber = "";

			// Loyalty
			this.loyaltyPoints = null;
			this.pointsToRedeem = 0;
			this.conversionFactor = 0;
			this.customerName = "";

			// Frequent cards
			this.frequentCards = [];
			this.showFrequentCardsDialog = false;
			this.applyingCard = false;

			// Item group discounts
			this.itemGroupDiscounts = {};
			this.selectedItemGroupForDiscount = null;
			this.discountPercentageByGroup = 0;
			this.showItemGroupDiscountDialog = false;

			// UI loaders
			this.saveLoading = false;
			this.paymentLoading = false;

			localStorage.removeItem("pos_selected_employee");

			console.log("[InvoiceSummary] Reset after payment completed");
		},
		formatByPrecision(value) {
			const num = Number(value || 0);
			return num.toFixed(this.decimalPrecision);
		},
		handleAdditionalDiscountUpdate(value) {
			this.$emit("update:additional_discount", value);
		},

		handleAdditionalDiscountPercentageUpdate(value) {
			let val = Math.max(0, Number(value || 0));

			if (this.maxInvoiceDiscount && val > this.maxInvoiceDiscount) {
				frappe.show_alert({
					message: __(`Maximum allowed discount is ${this.maxInvoiceDiscount}%`),
					indicator: "red",
				});
				val = this.maxInvoiceDiscount;

				this.$nextTick(() => {
					this.$emit("update:additional_discount_percentage", val);
				});
				return;
			}

			this.$emit("update:additional_discount_percentage", val);
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
		normalizeOilItemFlag(value) {
			return Boolean(Number(value)) || value === true;
		},
		activateOdometerLoadLock(durationMs = 2000) {
			this.odometerLoadLockUntil = Date.now() + durationMs;
		},
		isOdometerLoadLocked() {
			return Date.now() < (this.odometerLoadLockUntil || 0);
		},
		activateEmployeeLoadLock(durationMs = 2500) {
			this.employeeLoadLockUntil = Date.now() + durationMs;
		},
		isEmployeeLoadLocked() {
			return Date.now() < (this.employeeLoadLockUntil || 0);
		},
		startEmployeeSelectionSync() {
			this.employeeSelectionEpoch += 1;
			return this.employeeSelectionEpoch;
		},
		isCurrentEmployeeSelectionSync(epoch) {
			return epoch === this.employeeSelectionEpoch;
		},
		resetEmployeeSelectionState({ hideSelector = true } = {}) {
			this.employeeSelectionEpoch += 1;
			this.employeeLoadLockUntil = 0;
			this.employeeSearchRequestId += 1;
			this.selectedEmployee = null;
			this.selectedEmployeeDetails = null;
			this.employeeSearch = "";
			if (this.employeeSearchDebounce) {
				clearTimeout(this.employeeSearchDebounce);
				this.employeeSearchDebounce = null;
			}
			this.setEmployeeRecords([]);
			this.allEmployees = [];
			if (hideSelector) {
				this.showEmployeeSelection = false;
			}
			this.closeEmployeeDropdown();
		},
		applyOdometerData(data = {}) {
			this.showOdometerField = this.normalizeOilItemFlag(data.custom_has_oil_item);
			this.odometerReading =
				typeof data.custom_odometer_reading !== "undefined" && data.custom_odometer_reading !== null
					? data.custom_odometer_reading
					: null;
			this.vehicleNumber = data.custom_vehicle_no || this.vehicleNumber || "";
			this.mobileNumber = data.contact_mobile || this.mobileNumber || "";
			this.activateOdometerLoadLock();
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
				if (
					!this.odometerReading ||
					isNaN(this.odometerReading) ||
					Number(this.odometerReading) <= 0
				) {
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
				const redeemedPoints = Number(this.pointsToRedeem || 0);
				const newDiscountAmount = Number(this.redemptionValue || 0);
				const currentDiscount = parseFloat(this.additional_discount || 0);
				const updatedDiscount = currentDiscount + newDiscountAmount;

				this.$emit("update:additional_discount", updatedDiscount);
				this.eventBus.emit("set_loyalty_redemption", {
					points: redeemedPoints,
					amount: newDiscountAmount,
					customer: this.selectedCustomerId,
				});
				this.apply_additional_discount();

				frappe.show_alert({
					message: this.__(
						`Loyalty discount staged: ${this.formatFloat(redeemedPoints, 2)} points = ${this.formatCurrency(newDiscountAmount, this.moneyPrecision)}. Points will be deducted after submit.`,
					),
					indicator: "green",
					title: this.__("Redemption Staged"),
				});

				await this.fetchLoyaltyPoints();
				this.pointsToRedeem = 0;
				this.showLoyaltyDialog = false;
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

		normalizeEmployeeValue(value) {
			if (value === null || typeof value === "undefined") return "";
			if (typeof value === "object") {
				return String(
					value.employee_id ||
						value.custom_employee_id ||
						value.name ||
						value.employee_name ||
						value.display_label ||
						"",
				).trim();
			}
			return String(value).trim();
		},

		formatDate(dateStr) {
			if (!dateStr) return "";
			const date = new Date(dateStr);
			return date.toLocaleDateString();
		},

		buildEmployeeDisplayLabel(employee) {
			if (!employee) return "";
			const employeeId = this.normalizeEmployeeValue(
				employee.custom_employee_id || employee.employee_id || employee.name,
			);
			const employeeName = this.normalizeEmployeeValue(
				employee.employee_name || employee.display_name || employee.full_name,
			);
			return employeeId && employeeName
				? `${employeeId} - ${employeeName}`
				: employeeName || employeeId;
		},

		buildEmployeeSubtitle(employee) {
			if (!employee) return "";
			const details = [];
			if (employee.designation) {
				details.push(employee.designation);
			}
			if (employee.department) {
				details.push(employee.department);
			}
			return details.join(" · ");
		},

		normalizeEmployeeRecord(employee) {
			if (!employee) return null;
			const employeeId = this.normalizeEmployeeValue(employee.employee_id || employee.name);
			const customEmployeeId = this.normalizeEmployeeValue(employee.custom_employee_id);
			const employeeName = this.normalizeEmployeeValue(
				employee.employee_name ||
					employee.display_name ||
					employee.full_name ||
					employeeId ||
					customEmployeeId,
			);
			const displayLabel =
				typeof employee.display_label === "string" && employee.display_label.trim()
					? employee.display_label.trim()
					: this.buildEmployeeDisplayLabel({
							employee_id: employeeId,
							custom_employee_id: customEmployeeId,
							employee_name: employeeName,
						});
			return {
				...employee,
				employee_id: employeeId,
				custom_employee_id: customEmployeeId,
				employee_name: employeeName,
				display_label: displayLabel,
				name: this.normalizeEmployeeValue(employee.name || employeeId || customEmployeeId),
			};
		},

		setEmployeeRecords(employees = [], { cacheAll = false } = {}) {
			const normalizedEmployees = employees
				.map((employee) => this.normalizeEmployeeRecord(employee))
				.filter(Boolean);

			this.employees = normalizedEmployees;
			if (cacheAll) {
				this.allEmployees = normalizedEmployees;
			}
		},

		setAllEmployeeRecords(employees = []) {
			const normalizedEmployees = employees
				.map((employee) => this.normalizeEmployeeRecord(employee))
				.filter(Boolean);

			this.allEmployees = normalizedEmployees;
			this.employees = normalizedEmployees;
		},

		getSelectedEmployeeRecord(employeeId) {
			const normalizedEmployeeId = this.normalizeEmployeeValue(employeeId);
			if (!normalizedEmployeeId) return null;
			return (
				this.selectedEmployeeDetails ||
				this.employees.find(
					(employee) =>
						employee.employee_id === normalizedEmployeeId ||
						employee.custom_employee_id === normalizedEmployeeId ||
						employee.name === normalizedEmployeeId,
				) ||
				null
			);
		},

		async fetchEmployees(searchTerm = "") {
			if (!this.pos_profile?.company) {
				console.warn("[InvoiceSummary] No company in POS profile");
				return [];
			}

			const query = (searchTerm || "").trim();
			const shouldSearch = query.length >= 3;
			const requestId = ++this.employeeSearchRequestId;

			this.loadingEmployees = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.employees.get_active_employees",
					args: {
						company: this.pos_profile.company,
						search_term: shouldSearch ? query : null,
					},
				});

				if (requestId !== this.employeeSearchRequestId) {
					return this.employees;
				}

				const employees = Array.isArray(response?.message) ? response.message : [];
				if (shouldSearch) {
					this.setEmployeeRecords(employees);
				} else {
					this.setAllEmployeeRecords(employees);
				}
				return this.employees;
			} catch (error) {
				if (requestId !== this.employeeSearchRequestId) {
					return this.employees;
				}
				console.error("[InvoiceSummary] Failed to fetch employees:", error);
				frappe.show_alert({
					message: this.__("Failed to load employees. Please try again."),
					indicator: "red",
				});
				this.setEmployeeRecords([]);
				return [];
			} finally {
				if (requestId === this.employeeSearchRequestId) {
					this.loadingEmployees = false;
				}
			}
		},

		async fetchEmployeeById(employeeId) {
			const normalizedEmployeeId = this.normalizeEmployeeValue(employeeId);
			if (!normalizedEmployeeId) return null;

			const existing = this.getSelectedEmployeeRecord(normalizedEmployeeId);
			if (existing && existing.employee_name) {
				return existing;
			}

			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.employees.get_employee_details",
					args: { employee_id: normalizedEmployeeId },
				});
				if (response?.message) {
					const employee = this.normalizeEmployeeRecord(response.message);
					if (employee) {
						const existingIndex = this.employees.findIndex(
							(item) =>
								item.employee_id === employee.employee_id ||
								item.custom_employee_id === employee.custom_employee_id ||
								item.name === employee.employee_id,
						);
						const cachedIndex = this.allEmployees.findIndex(
							(item) =>
								item.employee_id === employee.employee_id ||
								item.custom_employee_id === employee.custom_employee_id ||
								item.name === employee.employee_id,
						);
						if (existingIndex !== -1) {
							this.employees.splice(existingIndex, 1, employee);
						} else {
							this.employees.unshift(employee);
						}
						if (cachedIndex !== -1) {
							this.allEmployees.splice(cachedIndex, 1, employee);
						} else {
							this.allEmployees.unshift(employee);
						}
						return employee;
					}
				}
			} catch (error) {
				console.warn("[InvoiceSummary] Failed to fetch employee details:", error);
			}

			return null;
		},

		handleEmployeeSearchInput(value) {
			const query = (value || "").trim();
			if (this.employeeSearchDebounce) {
				clearTimeout(this.employeeSearchDebounce);
				this.employeeSearchDebounce = null;
			}

			if (query.length < 3) {
				if (this.allEmployees.length) {
					this.setEmployeeRecords(this.allEmployees);
				} else {
					this.fetchEmployees("");
				}
				return;
			}

			this.employeeSearchDebounce = setTimeout(() => {
				this.fetchEmployees(query);
			}, 300);
		},

		handleEmployeeSearchBlur() {
			window.setTimeout(() => {
				const autocomplete = this.$refs.serviceEmployeeAutocomplete;
				const rootElement = autocomplete?.$el;
				if (!rootElement || !rootElement.contains(document.activeElement)) {
					this.closeEmployeeDropdown();
				}
			}, 0);
		},

		employeeFilter(value, query, item) {
			if (!query) return true;

			const searchTerm = query.toLowerCase();
			const employeeName = this.normalizeEmployeeValue(item.raw.employee_name).toLowerCase();
			const employeeCode = this.normalizeEmployeeValue(
				item.raw.custom_employee_id || item.raw.employee_id || item.raw.name,
			).toLowerCase();
			const designation = this.normalizeEmployeeValue(item.raw.designation).toLowerCase();
			const displayLabel = this.normalizeEmployeeValue(item.raw.display_label).toLowerCase();

			// Extract just the number from employee code (e.g., "HR-EMP-00001" -> "00001" or "1")
			const codeNumber = employeeCode.replace(/[^0-9]/g, "");
			const queryNumber = searchTerm.replace(/[^0-9]/g, "");

			return (
				employeeName.includes(searchTerm) ||
				employeeCode.includes(searchTerm) ||
				designation.includes(searchTerm) ||
				displayLabel.includes(searchTerm) ||
				(queryNumber && codeNumber.includes(queryNumber))
			);
		},

		async handleEmployeeChange(employeeId) {
			const normalizedEmployeeId = this.normalizeEmployeeValue(employeeId);
			if (!normalizedEmployeeId) {
				// Employee cleared
				this.selectedEmployee = null;
				this.selectedEmployeeDetails = null;
				this.employeeSearch = "";
				this.closeEmployeeDropdown();
				this.eventBus.emit("employee_selected", {
					employee_id: null,
					employee_name: null,
				});
				return;
			}

			let employee = this.getSelectedEmployeeRecord(normalizedEmployeeId);
			if (!employee) {
				employee = await this.fetchEmployeeById(normalizedEmployeeId);
			}

			if (!employee) {
				console.warn("[InvoiceSummary] Selected employee not found in list:", normalizedEmployeeId);
				this.selectedEmployee = normalizedEmployeeId;
				this.selectedEmployeeDetails = {
					employee_id: normalizedEmployeeId,
					custom_employee_id: normalizedEmployeeId,
					employee_name: normalizedEmployeeId,
					display_label: this.buildEmployeeDisplayLabel({
						employee_id: normalizedEmployeeId,
						custom_employee_id: normalizedEmployeeId,
						employee_name: normalizedEmployeeId,
					}),
				};
				this.eventBus.emit("employee_selected", {
					employee_id: normalizedEmployeeId,
					employee_name: normalizedEmployeeId,
				});
				this.closeEmployeeDropdown();
				return;
			}

			this.selectedEmployee = employee.employee_id;
			this.selectedEmployeeDetails = employee;

			// Emit event to parent component to attach employee to invoice
			this.eventBus.emit("employee_selected", {
				employee_id: employee.employee_id,
				custom_employee_id: employee.custom_employee_id,
				employee_name: employee.employee_name,
				designation: employee.designation,
				department: employee.department,
			});

			this.closeEmployeeDropdown();

			// Show confirmation message
			frappe.show_alert({
				message: this.__(`Service employee set to: ${employee.employee_name}`),
				indicator: "green",
			});
		},

		handleEmployeeClear() {
			this.selectedEmployee = null;
			this.selectedEmployeeDetails = null;
			this.employeeSearch = "";
			this.closeEmployeeDropdown();
			this.eventBus.emit("employee_selected", {
				employee_id: null,
				employee_name: null,
			});
		},

		handleEmployeeMenuToggle(isOpen) {
			this.employeeMenu = isOpen;
			if (isOpen && !this.employees.length && !this.loadingEmployees) {
				this.fetchEmployees(this.employeeSearch);
			}
			if (isOpen && this.selectedEmployee && !this.selectedEmployeeDetails) {
				this.fetchEmployeeById(this.selectedEmployee);
			}
			if (isOpen) {
				this.$nextTick(() => {
					const searchInput = this.$refs.employeeSearchInput;
					const inputElement = searchInput?.$el?.querySelector("input") || searchInput?.$el;
					if (inputElement && typeof inputElement.focus === "function") {
						inputElement.focus();
					}
				});
			}
		},

		checkIfCarWashService() {
			// Emit event to parent to check items
			this.eventBus.emit("check_items_for_service", {
				callback: (hasCarWashService) => {
					if (!hasCarWashService && this.isEmployeeLoadLocked() && this.selectedEmployee) {
						return;
					}

					this.showEmployeeSelection = hasCarWashService;

					// Fetch employees if needed and not already loaded
					// Clear selection if no longer needed
					if (!hasCarWashService && this.selectedEmployee) {
						this.selectedEmployee = null;
						this.selectedEmployeeDetails = null;
						this.handleEmployeeChange(null);
					}
				},
			});
		},

		async handleExternalEmployeeSelected(payload) {
			// payload may be { employee_id, employee_name } or just employee_id (string)
			if (!payload) {
				// Clear only the selected value. The field should remain visible
				// while car wash service is still active.
				this.selectedEmployee = null;
				this.selectedEmployeeDetails = null;
				this.employeeSearch = "";
				this.closeEmployeeDropdown();
				return;
			}

			const syncEpoch = this.startEmployeeSelectionSync();
			const empId = this.normalizeEmployeeValue(payload.employee_id || payload);
			const empNameProvided = this.normalizeEmployeeValue(payload.employee_name);
			const customEmployeeId = this.normalizeEmployeeValue(payload.custom_employee_id);
			const lookupEmployeeId = empId || customEmployeeId;

			if (!lookupEmployeeId && !empNameProvided) {
				this.selectedEmployee = null;
				this.selectedEmployeeDetails = null;
				this.employeeSearch = "";
				this.closeEmployeeDropdown();
				return;
			}

			// show selector
			this.showEmployeeSelection = true;
			this.activateEmployeeLoadLock();

			// if we already have employees loaded, set selection directly
			let resolvedEmployee = null;
			if (empNameProvided) {
				resolvedEmployee = this.normalizeEmployeeRecord({
					employee_id: lookupEmployeeId,
					custom_employee_id: customEmployeeId,
					employee_name: empNameProvided,
				});
			} else {
				resolvedEmployee = await this.fetchEmployeeById(lookupEmployeeId);
			}

			if (!this.isCurrentEmployeeSelectionSync(syncEpoch)) return;

			if (!resolvedEmployee) {
				resolvedEmployee = {
					employee_id: lookupEmployeeId,
					custom_employee_id: customEmployeeId,
					employee_name: empNameProvided || lookupEmployeeId,
					display_label: this.buildEmployeeDisplayLabel({
						employee_id: lookupEmployeeId,
						custom_employee_id: customEmployeeId,
						employee_name: empNameProvided || lookupEmployeeId,
					}),
				};
			}

			const employeeExistsInCache = this.allEmployees.some(
				(item) =>
					item.employee_id === lookupEmployeeId ||
					item.custom_employee_id === lookupEmployeeId ||
					item.name === lookupEmployeeId,
			);
			if (empNameProvided && !employeeExistsInCache) {
				this.employees.unshift(resolvedEmployee);
				this.allEmployees.unshift(resolvedEmployee);
			}

			this.selectedEmployee = resolvedEmployee.employee_id || lookupEmployeeId;
			this.selectedEmployeeDetails = resolvedEmployee;
			this.closeEmployeeDropdown();
		},
		closeEmployeeDropdown() {
			this.employeeSearch = "";
			if (this.employeeSearchDebounce) {
				clearTimeout(this.employeeSearchDebounce);
				this.employeeSearchDebounce = null;
			}
			this.employeeMenu = false;
			this.$nextTick(() => {
				const autocomplete = this.$refs.serviceEmployeeAutocomplete;
				if (autocomplete?.blur) {
					autocomplete.blur();
				}
				const input = autocomplete?.$el?.querySelector("input");
				if (input) {
					input.blur();
				}
				const active = document.activeElement;
				if (active && typeof active.blur === "function") {
					active.blur();
				}
				this.employeeMenu = false;
				this.employeeFieldKey += 1;
			});
		},

		async handleCancelSale() {
			this.cancelLoading = true;
			try {
				// Only emit the cancel-sale event to parent
				// Parent will show the confirmation dialog
				this.$emit("cancel-sale");
			} finally {
				setTimeout(() => {
					this.cancelLoading = false;
				}, 500);
			}
		},

		// Add this NEW method to handle the actual clearing after confirmation
		handleConfirmedCancelSale() {
			console.log("[InvoiceSummary] Cancel sale confirmed by user - clearing data");

			// Reset local state
			this.resetAfterPayment();

			// Emit clear invoice to reset payment data
			this.eventBus.emit("clear_invoice");

			// Close payment dialog if open
			this.eventBus.emit("show_payment", "false");

			// Show success message
			frappe.show_alert({
				message: this.__("Sale cancelled successfully"),
				indicator: "orange",
			});
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
			console.log("[InvoiceSummary] handleShowPayment called - START");
			console.trace("[InvoiceSummary] Call stack:");

			if (!this.selectedCustomerId) {
				frappe.show_alert({
					message: this.__("Please select a customer first"),
					indicator: "warning",
				});
				return;
			}

			this.paymentLoading = true;
			try {
				this.eventBus.emit("show_payment_modal");
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
		this.eventBus.on("reset_manual_total", () => {
			this.manual_round_off = 0;

			this.eventBus.emit("update_rounded_total", this.finalTotal);

			this.eventBus.emit("force_payment_refresh");
		});

		if (this.selectedCustomerId) {
			this.fetchLoyaltyPoints();
			this.fetchFrequentCards();
		}

		// Listen for odometer field visibility
		this.eventBus.on("show_odometer_field", (shouldShow) => {
			this.showOdometerField = shouldShow;

			if (!shouldShow) {
				// During draft/job-order hydration, item-watch can briefly emit false
				// and then true; don't wipe loaded values in that window.
				if (!this.isOdometerLoadLocked()) {
					this.clearOdometerFields();
				}
			}
		});

		// Listen for odometer data from parent (when loading draft)
		this.eventBus.on("load_odometer_data", (data) => {
			if (data) {
				this.applyOdometerData(data);
			}
		});

		this.eventBus.on("set_custom_has_oil_item", (value) => {
			this.showOdometerField = this.normalizeOilItemFlag(value);
			if (this.showOdometerField) {
				this.activateOdometerLoadLock();
			}
		});

		this.eventBus.on("set_custom_odometer_reading", (value) => {
			this.odometerReading =
				typeof value !== "undefined" && value !== null && value !== "" ? value : null;
			if (this.odometerReading !== null) {
				this.activateOdometerLoadLock();
			}
		});

		this.eventBus.on("set_custom_vehicle_no", (value) => {
			this.vehicleNumber = value || "";
			if (this.vehicleNumber) {
				this.activateOdometerLoadLock();
			}
		});

		this.eventBus.on("set_contact_mobile", (value) => {
			this.mobileNumber = value || "";
			if (this.mobileNumber) {
				this.activateOdometerLoadLock();
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
			if (!shouldShow && this.isEmployeeLoadLocked() && this.selectedEmployee) {
				return;
			}

			this.showEmployeeSelection = shouldShow;
		});

		// Listen for clear employee selection event
		this.eventBus.on("clear_employee_selection", () => {
			this.resetEmployeeSelectionState();
		});

		// Check initially if we should show employee selection
		this.checkIfCarWashService();

		this.eventBus.on("employee_selected", this.handleExternalEmployeeSelected);

		this.eventBus.on("payment_completed", this.resetAfterPayment);

		this.eventBus.on("confirm_cancel_sale", this.handleConfirmedCancelSale);

		// Listen for item groups from parent
		this.eventBus.on("register_item_groups", (groups) => {
			if (Array.isArray(groups)) {
				this.availableItemGroups = groups;
			}
		});
	},
	beforeUnmount() {
		if (this.employeeSearchDebounce) {
			clearTimeout(this.employeeSearchDebounce);
			this.employeeSearchDebounce = null;
		}
		this.eventBus.off("item_added_to_invoice", this.checkAutoApplyCard);
		this.eventBus.off("show_employee_selection");
		this.eventBus.off("clear_employee_selection");
		this.eventBus.off("employee_selected", this.handleExternalEmployeeSelected);
		this.eventBus.off("show_odometer_field");
		this.eventBus.off("load_odometer_data");
		this.eventBus.off("set_custom_has_oil_item");
		this.eventBus.off("set_custom_odometer_reading");
		this.eventBus.off("set_custom_vehicle_no");
		this.eventBus.off("set_contact_mobile");
		this.eventBus.off("update_customer_details");
		this.eventBus.off("payment_completed", this.resetAfterPayment);
		this.eventBus.off("confirm_cancel_sale", this.handleConfirmedCancelSale);
		this.eventBus.off("reset_manual_total");
		this.eventBus.off("register_item_groups");
	},
};
</script>

<style scoped>
.cards {
	background-color: #f5f5f5 !important;
	transition: all 0.3s ease;
	display: flex;
	flex-direction: column;
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
	height: 22px !important;
	font-size: 0.75rem !important;
	text-transform: none !important;
	font-weight: 600 !important;
	padding: 0 6px !important;
}

.primary-action {
	height: 26px !important;
	font-size: 0.72rem !important;
	font-weight: 700 !important;
}

.compact-summary {
	height: 100%;
	overflow: hidden;
	margin-top: 12px !important;
	padding-top: 6px !important;
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
	font-size: 0.75rem !important;
	background: linear-gradient(135deg, #4caf50, #45a049) !important;
	height: 22px !important;
}

.loyalty-points-display-card .v-card-text {
	padding: 4px !important;
}

.loyalty-points-display-card p {
	margin: 0 !important;
	line-height: 1.2 !important;
}

.loyalty-points-display-card .text-h6 {
	font-size: 0.9rem !important;
}

.loyalty-currency-value {
	white-space: nowrap;
}

.pay-btn:hover {
	background: linear-gradient(135deg, #45a049, #3d8b40) !important;
	transform: translateY(-2px);
}

.summary-field {
	transition: all 0.2s ease;
	margin-bottom: 1px !important;
}

/* Keep field borders visible in normal state (not only on hover/focus) */
.summary-field :deep(.v-field) {
	border: 1.5px solid #b8c1cc !important;
}

.summary-field :deep(.v-field__overlay) {
	opacity: 0.02 !important;
}

:deep(.v-theme--dark) .summary-field :deep(.v-field),
:deep([data-theme="dark"]) .summary-field :deep(.v-field) {
	border-color: #4b5563 !important;
}

.summary-field:hover {
	transform: translateY(-1px);
}

.v-row.dense {
	row-gap: 1px !important;
}

/* FIX: Prevent label/value overlap */
.summary-field :deep(.v-field-label) {
	font-weight: 600;
	font-size: 0.74rem;
}

.employee-selection {
	display: flex;
	align-items: center;
	gap: 4px;
	width: 100%;
	min-width: 0;
	max-width: 100%;
	overflow: hidden;
	flex-wrap: nowrap;
	white-space: nowrap;
	font-size: clamp(0.66rem, 0.8vw, 0.82rem);
	line-height: 1.1;
}

.employee-selection-name {
	color: #0f9fb3;
	font-weight: 600;
	min-width: 0;
	flex: 1 1 auto;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.employee-selection-placeholder {
	color: #9ca3af;
	font-weight: 500;
	min-width: 0;
	flex: 1 1 auto;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.employee-selection-id {
	color: #48b8c6;
	font-size: 0.88em;
	flex: 0 1 auto;
	min-width: 0;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.employee-search-helper {
	color: #6b7280;
	line-height: 1.2;
}

:deep(.employee-search-input .v-field) {
	min-height: 36px !important;
}

:deep(.employee-search-input .v-field__input) {
	min-height: 36px !important;
	padding-top: 6px !important;
	padding-bottom: 6px !important;
	font-size: 0.9rem !important;
}

:deep(.employee-search-input .v-field__prepend-inner) {
	padding-inline-start: 8px !important;
}

:deep(.employee-search-input .v-field__append-inner) {
	padding-inline-end: 8px !important;
}

:deep(.employee-search-input .v-icon) {
	font-size: 1rem !important;
}

:deep(.v-theme--dark) .employee-search-helper,
:deep([data-theme="dark"]) .employee-search-helper {
	color: #cbd5e1;
}

:deep(.summary-field .v-field__input) .employee-selection-name,
:deep(.summary-field .v-field__input) .employee-selection-id {
	opacity: 1;
}

:deep(.employee-summary-field .v-field__input) {
	flex-wrap: nowrap !important;
	overflow: hidden !important;
}

:deep(.employee-summary-field .v-autocomplete__selection) {
	max-width: 100% !important;
	min-width: 0 !important;
	overflow: hidden !important;
	font-size: inherit !important;
}

:deep(.employee-summary-field .v-field__input) {
	font-size: clamp(0.66rem, 0.8vw, 0.82rem) !important;
}

:deep(.v-theme--dark) .employee-selection-id,
:deep([data-theme="dark"]) .employee-selection-id {
	color: #7fd4dd;
}

:deep(.v-theme--dark) .employee-selection-name,
:deep([data-theme="dark"]) .employee-selection-name {
	color: #55d4e0;
}

.summary-actions {
	margin-top: 20px !important;
}

@media (max-width: 1366px) {
	.summary-actions {
		margin-top: 17px !important;
	}
}

:deep(.compact-summary .v-col) {
	padding-top: 0 !important;
	padding-bottom: 0 !important;
}

:deep(.compact-summary .v-field) {
	min-height: 28px !important;
	height: 28px !important;
}

:deep(.compact-summary .v-field__input) {
	min-height: 24px !important;
	height: 24px !important;
	padding-top: 0 !important;
	padding-bottom: 0 !important;
	font-size: 0.7rem !important;
}

:deep(.compact-summary .v-field__append-inner),
:deep(.compact-summary .v-field__prepend-inner) {
	min-height: 24px !important;
	height: 24px !important;
}

:deep(.compact-summary .v-input__details) {
	min-height: 0 !important;
	padding-top: 0 !important;
	margin-top: 0 !important;
}

:deep(.compact-summary .v-field__prepend-inner .v-icon),
:deep(.compact-summary .v-field__append-inner .v-icon) {
	font-size: 16px !important;
}

/* Keep manual round-off field readable and inside bounds in compact layout */
:deep(.compact-summary .manual-round-off-field .v-field) {
	min-height: 34px !important;
	height: 34px !important;
	overflow: hidden !important;
}

:deep(.compact-summary .manual-round-off-field .v-field__input) {
	min-height: 30px !important;
	height: 30px !important;
	padding-top: 2px !important;
	padding-bottom: 2px !important;
	line-height: 1.2 !important;
	display: flex !important;
	align-items: center !important;
}

:deep(.compact-summary .manual-round-off-field .v-field__prepend-inner),
:deep(.compact-summary .manual-round-off-field .v-field__append-inner) {
	min-height: 30px !important;
	height: 30px !important;
	align-items: center !important;
}

:deep(.compact-summary .manual-round-off-field input[type="number"]::-webkit-outer-spin-button),
:deep(.compact-summary .manual-round-off-field input[type="number"]::-webkit-inner-spin-button) {
	-webkit-appearance: none !important;
	margin: 0 !important;
	display: none !important;
}

:deep(.compact-summary .manual-round-off-field input[type="number"]) {
	-moz-appearance: textfield !important;
	appearance: textfield !important;
	align-self: center !important;
	line-height: 1.1 !important;
	padding-top: 0 !important;
	padding-bottom: 0 !important;
}

:deep(.compact-summary .manual-round-off-field .v-text-field__prefix) {
	align-self: center !important;
	line-height: 1 !important;
	margin-top: 0 !important;
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

/* Item Group Discount Card  */
.item-group-discount-card {
	margin-top: 10px !important;
	background: linear-gradient(135deg, rgba(33, 150, 243, 0.08), rgba(21, 101, 192, 0.06));
	border: 2px solid rgba(33, 150, 243, 0.25);
	border-radius: 12px !important;
	min-height: 44px;
	max-height: 44px;

	padding: 0 !important;

	transition: all 0.3s ease;
}

:deep(.item-group-discount-card .v-avatar) {
	display: inline-flex !important;
	align-items: center !important;
	justify-content: center !important;

	width: 32px !important;
	height: 32px !important;
	min-width: 32px !important;
	min-height: 32px !important;
}

.item-group-discount-card :deep(.v-avatar) {
	width: 28px !important;
	height: 28px !important;
}

.item-group-discount-card :deep(.v-icon) {
	font-size: 17px !important;
}

:deep(.item-group-discount-card .item-group-avatar) {
	background-color: #2196f3 !important;
}

:deep(.item-group-discount-card .v-avatar .v-icon) {
	display: inline-flex !important;
	opacity: 1 !important;
	visibility: visible !important;

	color: #ffffff !important;
	font-size: 20px !important;
	line-height: 1 !important;
}

/* Kill the underlay globally */
:deep(.v-avatar__underlay) {
	display: none !important;
}

/* Force icon above everything */
:deep(.v-avatar .v-icon) {
	position: relative;
	z-index: 2;
}

/* Reduce internal padding to match loyalty card */
.item-group-discount-card .v-card-text {
	padding: 2px 6px !important;
	height: 100% !important;
	display: flex !important;
	align-items: center !important;
}
/* Hide empty state (keeps card compact) */
.item-group-discount-card .text-center {
	display: none !important;
}
.item-group-discount-card .text-caption {
	display: none !important;
}

.item-group-discount-card:hover {
	border-color: rgba(33, 150, 243, 0.45);
	transform: translateY(-2px);
}

:deep(.v-theme--dark) .item-group-discount-card {
	background: linear-gradient(135deg, rgba(33, 150, 243, 0.15), rgba(21, 101, 192, 0.1));
	border-color: rgba(33, 150, 243, 0.35);
}

:deep(.v-theme--dark) .item-group-discount-card:hover {
	border-color: rgba(33, 150, 243, 0.55);
}

/* Discount Chips */
.discount-chip {
	backdrop-filter: blur(10px);
	transition: all 0.2s ease;
	padding: 6px 12px !important;
	font-size: 0.875rem;
}

.discount-chip:hover {
	transform: scale(1.05);
}

.discounts-list {
	display: flex;
	flex-wrap: wrap;
	gap: 8px;
	min-height: 24px;
	align-content: flex-start;
}

/* Compact summary like loyalty card */
.discount-summary {
	background: transparent;
	padding: 0;
	margin: 0;
	font-size: 0.85rem;

	display: flex;
	align-items: center;
}

:deep(.v-theme--dark) .discount-summary {
	background: rgba(33, 150, 243, 0.1);
}

.text-info {
	color: #1976d2 !important;
}

:deep(.v-theme--dark) .text-info {
	color: #64b5f6 !important;
}

/* Add Discount Button */
.add-discount-btn {
	transition: all 0.2s ease !important;
	align-self: center !important;
	margin-top: 3px !important;
	margin-bottom: 0 !important;
	min-height: 32px !important;
}

.add-discount-btn:hover {
	transform: translateY(-2px);
}

.item-group-header-row {
	align-items: center !important;
	margin-bottom: 0 !important;
	width: 100%;
	min-height: 32px;
	gap: 8px;
}

.discounts-list-compact {
	display: flex;
	align-items: center;
	gap: 4px;
	flex: 1;
	min-width: 0;
	overflow-x: auto;
	overflow-y: hidden;
	white-space: nowrap;
	padding: 0 2px;
}

.discount-chip-compact {
	flex-shrink: 0;
	max-width: 170px;
	height: 22px !important;
	font-size: 0.72rem !important;
	padding: 0 6px !important;
}

.discount-chip-compact :deep(.v-chip__content) {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.discount-dropdown-chip {
	cursor: pointer;
}

.discount-dropdown-list {
	min-width: 220px;
	max-width: 280px;
}

/* Dialog Styling */
.item-group-discount-card ~ .v-dialog__content {
	backdrop-filter: blur(4px);
}
.card-container {
	display: flex !important;
	flex-direction: column !important;
	height: 100% !important;
	overflow: hidden !important;
	position: relative !important;
}

.card-content-wrapper {
	display: flex !important;
	flex-direction: column !important;
	height: 100% !important;
	overflow: hidden !important;
}

.card-content-area {
	flex: 1 1 auto !important;
	overflow-y: auto !important;
	overflow-x: hidden !important;
	padding: 8px !important;
	min-height: 0 !important;
}

/* Custom scrollbar for content area */
.card-content-area::-webkit-scrollbar {
	width: 6px;
}

.card-content-area::-webkit-scrollbar-track {
	background: rgba(0, 0, 0, 0.05);
	border-radius: 3px;
}

.card-content-area::-webkit-scrollbar-thumb {
	background: rgba(0, 0, 0, 0.2);
	border-radius: 3px;
}

.card-content-area::-webkit-scrollbar-thumb:hover {
	background: rgba(0, 0, 0, 0.3);
}

:deep(.v-theme--dark) .card-content-area::-webkit-scrollbar-track {
	background: rgba(255, 255, 255, 0.05);
}

:deep(.v-theme--dark) .card-content-area::-webkit-scrollbar-thumb {
	background: rgba(255, 255, 255, 0.2);
}

:deep(.v-theme--dark) .card-content-area::-webkit-scrollbar-thumb:hover {
	background: rgba(255, 255, 255, 0.3);
}

/* FOOTER BUTTONS - FIXED AT BOTTOM */
.card-footer-actions {
	flex: 0 0 auto !important;
	padding: 12px 8px 8px 8px !important;
	border-top: 1px solid rgba(0, 0, 0, 0.12) !important;
	background: inherit !important;
	z-index: 20 !important;
	margin: 0 !important;
	position: relative !important;
}

:deep(.v-theme--dark) .card-footer-actions {
	border-top-color: rgba(255, 255, 255, 0.12) !important;
}

.card-footer-actions .v-row {
	margin: 0 !important;
	padding: 0 !important;
}

.card-footer-actions .v-col {
	padding: 4px !important;
}

.card-footer-actions .summary-actions {
	margin: 0 !important;
}

/* Button sizing in footer */
.card-footer-actions .summary-btn {
	height: 36px !important;
	font-size: 0.75rem !important;
	min-height: 36px !important;
	transition: all 0.2s ease !important;
}

.card-footer-actions .primary-action {
	height: 36px !important;
	font-size: 0.75rem !important;
	font-weight: 700 !important;
}

.card-footer-actions .pay-btn {
	background: linear-gradient(135deg, #4caf50, #45a049) !important;
}

.card-footer-actions .pay-btn:hover {
	background: linear-gradient(135deg, #45a049, #3d8b40) !important;
	transform: translateY(-1px);
}

/* Responsive */
@media (max-width: 960px) {
	.card-footer-actions {
		padding: 8px 4px 4px 4px !important;
	}

	.card-footer-actions .summary-btn {
		height: 32px !important;
		font-size: 0.7rem !important;
	}

	.card-footer-actions .primary-action {
		height: 32px !important;
	}
}

@media (max-width: 600px) {
	.card-footer-actions .summary-btn {
		height: 40px !important;
		font-size: 0.9rem !important;
	}

	.card-footer-actions .primary-action {
		height: 40px !important;
		font-size: 1rem !important;
	}
}

/* Final override: always-visible borders for summary fields */
:deep(.summary-field .v-field) {
	border: 1px solid #121416 !important;
	background-color: #fff !important;
}

:deep(.summary-field .v-field__overlay) {
	opacity: 0 !important;
}
</style>
