<template>
	<div class="drafts-wrapper" v-if="!useAsModal">
		<!-- Scrollable Content Area -->
		<div class="drafts-content">
			<v-data-table
				:headers="headers"
				:items="dialog_data"
				item-value="name"
				class="elevation-0 drafts-table"
				:theme="isDarkTheme ? 'dark' : 'light'"
				show-select
				v-model="selected"
				select-strategy="single"
				return-object
				density="compact"
				:items-per-page="100"
			>
				<template v-slot:column.posting_date="{ column }">
					<span class="text-caption font-weight-medium">{{ column.title }}</span>
				</template>
				<template v-slot:item.posting_date="{ item }">
					<span class="text-caption">{{ item.posting_date }}</span>
				</template>

				<template v-slot:column.posting_time="{ column }">
					<span class="text-caption font-weight-medium">{{ column.title }}</span>
				</template>
				<template v-slot:item.posting_time="{ item }">
					<span class="text-caption">{{
						item.posting_time ? item.posting_time.split(".")[0] : ""
					}}</span>
				</template>

				<template v-slot:item.customer="{ item }">
					<span class="text-caption">{{ item.customer }}</span>
				</template>

				<template v-slot:item.name="{ item }">
					<span class="text-caption font-weight-medium text-primary">{{ item.name }}</span>
				</template>

				<template v-slot:item.grand_total="{ item }">
					<span class="text-caption font-weight-bold">
						{{ currencySymbol(item.currency) }}
						{{ formatCurrency(item.grand_total) }}
					</span>
				</template>

				<template v-slot:bottom>
					<div
						class="pa-4 text-center text-caption text-medium-emphasis"
						v-if="dialog_data.length === 0"
					>
						<v-icon size="large" color="grey" class="mb-2">mdi-file-document-outline</v-icon>
						<div>{{ __("No draft invoices found.") }}</div>
						<div class="text-caption mt-1">{{ __("Create a new sale to get started") }}</div>
					</div>
				</template>
			</v-data-table>
		</div>

		<!-- Fixed Footer Button -->
		<div class="drafts-footer">
			<v-btn
				block
				color="success"
				size="large"
				variant="flat"
				prepend-icon="mdi-file-document-check"
				@click="submit_selection"
				:disabled="selected.length === 0"
				class="load-draft-btn"
			>
				{{ __("LOAD SELECTED DRAFT") }}
			</v-btn>
		</div>
	</div>

	<!-- Modal View -->
	<v-row justify="center" v-else>
		<v-dialog
			v-model="draftsDialog"
			:max-width="isMobileModal ? '100%' : maxWidth"
			:fullscreen="isMobileModal"
			:scrollable="true"
		>
			<v-card variant="flat" :color="isDarkTheme ? $vuetify.theme.themes.dark.colors.surface : 'white'">
				<v-card-title class="pb-1 pt-3">
					<span class="text-h6 text-primary">{{ __("Load Sales Invoice") }}</span>
				</v-card-title>
				<v-card-subtitle class="pt-0 pb-2">
					<span class="text-primary">{{ __("Load previously saved invoices") }}</span>
				</v-card-subtitle>
				<v-card-text class="pa-0">
					<v-container fluid class="pa-0">
						<v-row no-gutters>
							<v-col cols="12" class="pa-1">
								<v-data-table
									:headers="headers"
									:items="dialog_data"
									item-value="name"
									class="elevation-0"
									:theme="isDarkTheme ? 'dark' : 'light'"
									show-select
									v-model="selected"
									select-strategy="single"
									return-object
									density="compact"
									:items-per-page="10"
								>
									<template v-slot:column.posting_date="{ column }">
										<span class="d-none">{{ column.title }}</span>
									</template>
									<template v-slot:item.posting_date="{ item }">
										<span class="text-caption">{{ item.posting_date }}</span>
									</template>

									<template v-slot:column.posting_time="{ column }">
										<span class="d-none">{{ column.title }}</span>
									</template>
									<template v-slot:item.posting_time="{ item }">
										<span class="text-caption">{{
											item.posting_time ? item.posting_time.split(".")[0] : ""
										}}</span>
									</template>

									<template v-slot:item.grand_total="{ item }">
										{{ currencySymbol(item.currency) }}
										{{ formatCurrency(item.grand_total) }}
									</template>

									<template v-slot:bottom>
										<div
											class="pa-2 text-caption text-medium-emphasis"
											v-if="dialog_data.length === 0"
										>
											{{ __("No draft invoices found.") }}
										</div>
										<v-pagination
											v-else
											:length="1"
											:total-visible="3"
											size="small"
											class="mt-2"
										></v-pagination>
									</template>
								</v-data-table>
							</v-col>
						</v-row>
					</v-container>
				</v-card-text>
				<v-card-actions class="pt-1">
					<v-spacer></v-spacer>
					<v-btn color="error" variant="text" @click="close_dialog">{{ __("Close") }}</v-btn>
					<v-btn
						color="success"
						variant="flat"
						@click="submit_dialog"
						:disabled="selected.length === 0"
					>
						{{ __("Load Sale") }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";
export default {
	props: {
		maxWidth: {
			type: [String, Number],
			default: "600px",
		},
		useAsModal: {
			type: Boolean,
			default: false,
		},
	},
	mixins: [format],
	data: () => ({
		draftsDialog: false,
		singleSelect: true,
		selected: [],
		dialog_data: [],
		headers: [
			{
				title: __("Customer"),
				value: "customer",
				align: "start",
				sortable: true,
			},
			{
				title: __("Date"),
				align: "start",
				sortable: true,
				value: "posting_date",
				width: "100px",
			},
			{
				title: __("Time"),
				align: "start",
				sortable: true,
				value: "posting_time",
				width: "80px",
			},
			{
				title: __("Invoice"),
				value: "name",
				align: "start",
				sortable: true,
			},
			{
				title: __("Amount"),
				value: "grand_total",
				align: "end",
				sortable: false,
				width: "120px",
			},
		],
	}),
	computed: {
		isDarkTheme() {
			return this.$vuetify.theme.current.dark;
		},
		isMobileModal() {
			return window.innerWidth < 768;
		},
	},
	methods: {
		// Submit selection for inline view
		submit_selection() {
			if (this.selected.length > 0) {
				const draftName = this.selected[0].name;
				console.log("[Drafts] Loading draft:", draftName);
				this.eventBus.emit("draft_selected", draftName);
				this.selected = [];
			} else {
				this.eventBus.emit("show_message", {
					title: __("Select an invoice to load"),
					color: "error",
				});
			}
		},

		// Close and submit for dialog view
		close_dialog() {
			this.draftsDialog = false;
			this.selected = [];
			this.eventBus.emit("close_drafts");
		},

		submit_dialog() {
			if (this.selected.length > 0) {
				const draftName = this.selected[0].name;
				console.log("[Drafts] Loading draft from dialog:", draftName);
				this.eventBus.emit("draft_selected", draftName);
				this.close_dialog();
			} else {
				this.eventBus.emit("show_message", {
					title: `Select an invoice to load`,
					color: "error",
				});
			}
		},
	},
	created: function () {
		this.eventBus.on("open_drafts", (data) => {
			console.log("[Drafts] Received drafts data:", data.length, "items");
			this.dialog_data = data;
			this.selected = [];
			// If useAsModal is TRUE (meaning we are showing the dialog structure), open the dialog
			if (this.useAsModal) {
				this.draftsDialog = true;
			}
			// If useAsModal is FALSE (meaning we are showing the inline structure), it's already visible
		});

		this.eventBus.on("close_drafts", () => {
			this.draftsDialog = false;
			this.selected = [];
		});
	},
	beforeUnmount() {
		this.eventBus.off("open_drafts");
		this.eventBus.off("close_drafts");
	},
};
</script>

<style scoped>
/* Drafts Wrapper - Flex container */
.drafts-wrapper {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	background: white;
}

/* Scrollable Content Area */
.drafts-content {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	background-color: #fafafa;
}

/* Data Table Styling */
.drafts-table {
	background-color: white;
}

:deep(.v-data-table-row td),
:deep(.v-data-table-row th) {
	padding: 8px 12px !important;
}

:deep(.v-data-table) {
	font-size: 0.875rem;
}

:deep(.v-data-table__wrapper) {
	overflow-y: auto;
	max-height: 100%;
}

/* Fixed Footer Button */
.drafts-footer {
	flex-shrink: 0;
	padding: 12px;
	background: white;
	border-top: 2px solid #e0e0e0;
	z-index: 100;
}

.load-draft-btn {
	text-transform: uppercase;
	font-weight: 600;
	letter-spacing: 0.5px;
}

/* Scrollbar Styling */
.drafts-content::-webkit-scrollbar {
	width: 6px;
}

.drafts-content::-webkit-scrollbar-track {
	background: #f1f1f1;
	border-radius: 3px;
}

.drafts-content::-webkit-scrollbar-thumb {
	background: #999;
	border-radius: 3px;
}

.drafts-content::-webkit-scrollbar-thumb:hover {
	background: #666;
}

@media (max-width: 768px) {
	:deep(.v-data-table-row td),
	:deep(.v-data-table-row th) {
		padding: 6px 8px !important;
		font-size: 0.8rem;
	}

	.drafts-footer {
		padding: 8px;
	}
}
</style>
