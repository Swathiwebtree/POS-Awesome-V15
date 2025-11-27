<template>
	<div class="drafts-wrapper" v-if="!useAsModal">
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
				:item-class="(item) => (isCurrentDraft(item.name) ? 'v-data-table__tr--active' : '')"
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
					<div class="d-flex align-center">
						<v-chip
							v-if="isCurrentDraft(item.name)"
							color="success"
							size="x-small"
							class="mr-2"
							prepend-icon="mdi-check-circle"
						>
							{{ __("Current") }}
						</v-chip>
						<span class="text-caption font-weight-medium text-primary">{{ item.name }}</span>
					</div>
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
				{{ __("LOAD JOB ORDERS") }}
			</v-btn>
		</div>
	</div>

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
									:item-class="
										(item) =>
											isCurrentDraft(item.name) ? 'v-data-table__tr--active' : ''
									"
								>
									<template v-slot:column.posting_date="{ column }"
										><span class="d-none">{{ column.title }}</span></template
									>
									<template v-slot:item.posting_date="{ item }"
										><span class="text-caption">{{ item.posting_date }}</span></template
									>

									<template v-slot:column.posting_time="{ column }"
										><span class="d-none">{{ column.title }}</span></template
									>
									<template v-slot:item.posting_time="{ item }"
										><span class="text-caption">{{
											item.posting_time ? item.posting_time.split(".")[0] : ""
										}}</span></template
									>

									<template v-slot:item.name="{ item }">
										<div class="d-flex align-center">
											<v-chip
												v-if="isCurrentDraft(item.name)"
												color="success"
												size="x-small"
												class="mr-2"
												prepend-icon="mdi-check-circle"
											>
												{{ __("Current") }}
											</v-chip>
											<span class="text-caption font-weight-medium text-primary">{{
												item.name
											}}</span>
										</div>
									</template>

									<template v-slot:item.grand_total="{ item }"
										>{{ currencySymbol(item.currency)
										}}{{ formatCurrency(item.grand_total) }}</template
									>

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
						>{{ __("Load Sale") }}</v-btn
					>
				</v-card-actions>
			</v-card>
		</v-dialog>
	</v-row>
</template>

<script>
import format from "../../format";

// IMPORTANT: this component expects your invoice code to emit `draft_saved`
// with an object containing at least: name, customer, posting_date, posting_time, grand_total, currency
export default {
	props: {
		maxWidth: { type: [String, Number], default: "600px" },
		useAsModal: { type: Boolean, default: false },
	},
	mixins: [format],
	data: () => ({
		draftsDialog: false,
		selected: [],
		dialog_data: [],
		refreshing: false,
		headers: [
			{ title: __("Customer"), value: "customer", align: "start", sortable: true },
			{ title: __("Date"), value: "posting_date", align: "start", sortable: true, width: "100px" },
			{ title: __("Time"), value: "posting_time", align: "start", sortable: true, width: "80px" },
			{ title: __("Invoice"), value: "name", align: "start", sortable: true },
			{ title: __("Amount"), value: "grand_total", align: "end", sortable: false, width: "120px" },
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
		isCurrentDraft(draftName) {
			return this.$parent?.loaded_draft_name === draftName;
		},

		submit_selection() {
			if (this.selected.length > 0) {
				const draftName = this.selected[0].name;
				this.eventBus.emit("draft_selected", draftName);
				this.selected = [];
			} else {
				this.eventBus.emit("show_message", {
					title: __("Select an invoice to load"),
					color: "error",
				});
			}
		},

		close_dialog() {
			this.draftsDialog = false;
			this.selected = [];
			this.eventBus.emit("close_drafts");
		},

		submit_dialog() {
			if (this.selected.length > 0) {
				const draftName = this.selected[0].name;
				this.eventBus.emit("draft_selected", draftName);
				this.close_dialog();
			} else {
				this.eventBus.emit("show_message", { title: `Select an invoice to load`, color: "error" });
			}
		},

		// manual / initial fetch (keeps old Refresh behavior)
		async fetchDrafts() {
			const payload = {
				doctype: "Sales Invoice",
				filters: { docstatus: 0, company: "webtree", pos_profile: "pos" },
				fields: ["name", "customer", "posting_date", "posting_time", "grand_total", "currency"],
				limit_page_length: 500,
				order_by: "modified desc",
			};
			try {
				this.refreshing = true;
				const resp = await fetch("/api/method/frappe.client.get_list", {
					method: "POST",
					credentials: "same-origin",
					headers: {
						"Content-Type": "application/json",
						"X-Requested-With": "XMLHttpRequest",
					},
					body: JSON.stringify(payload),
				});
				if (!resp.ok) {
					console.warn(`[Drafts] fetchDrafts HTTP ${resp.status}`);
					return;
				}
				const json = await resp.json();
				if (json && Array.isArray(json.message)) {
					this.dialog_data = this._normalizeAndSort(json.message);
				} else {
					console.warn("[Drafts] Unexpected response shape from frappe.client.get_list", json);
				}
			} catch (err) {
				console.error("[Drafts] fetchDrafts error:", err);
			} finally {
				this.refreshing = false;
			}
		},

		// FAST PATH: merge a single saved draft object (no network)
		mergeDraft(newDraft) {
			if (!newDraft || !newDraft.name) return;

			const nd = this._normalizeSingle(newDraft);

			// remove any existing item with same name
			this.dialog_data = this.dialog_data.filter((d) => d.name !== nd.name);

			// prepend the new one
			this.dialog_data.unshift(nd);

			// sort by date/time (newest first) to keep UI consistent
			this.dialog_data = this._sortByDateTime(this.dialog_data);
		},

		_normalizeSingle(item) {
			// ensure minimal fields exist so table renders correctly
			const posting_date = item.posting_date || "";
			// posting_time might be a timestamp or null
			const posting_time =
				typeof item.posting_time !== "undefined" && item.posting_time !== null
					? String(item.posting_time)
					: "";
			return {
				name: item.name,
				customer: item.customer || "",
				posting_date,
				posting_time,
				grand_total: item.grand_total != null ? item.grand_total : 0,
				currency: item.currency || "INR",
			};
		},

		_normalizeAndSort(list) {
			const normalized = (list || []).map((i) => this._normalizeSingle(i));
			return this._sortByDateTime(normalized);
		},

		_sortByDateTime(arr) {
			return arr.slice().sort((a, b) => {
				const da = `${a.posting_date || ""} ${a.posting_time || ""}`.trim();
				const db = `${b.posting_date || ""} ${b.posting_time || ""}`.trim();
				if (da > db) return -1;
				if (da < db) return 1;
				if ((a.name || "") > (b.name || "")) return -1;
				if ((a.name || "") < (b.name || "")) return 1;
				return 0;
			});
		},
	},

	created() {
		// accept externally provided list (keep old behavior)
		this.eventBus.on("open_drafts", (data) => {
			this.dialog_data = Array.isArray(data) ? this._normalizeAndSort(data) : [];
			this.selected = [];
			if (this.useAsModal) this.draftsDialog = true;
		});

		this.eventBus.on("close_drafts", () => {
			this.draftsDialog = false;
			this.selected = [];
		});

		// FAST PATH: when invoice emits draft_saved we merge the object into the list
		this.eventBus.on("draft_saved", (payload) => {
			console.log("[Drafts] draft_saved received -> merging", payload && payload.name);
			try {
				this.mergeDraft(payload);
			} catch (e) {
				console.warn("[Drafts] mergeDraft failed", e);
			}
		});

		// keep invoice_saved_successfully for compatibility but do NOT auto-fetch here
		// (commented-out fetch to avoid 400 errors in some environments)
		this.eventBus.on("invoice_saved_successfully", (payload) => {
			console.log(
				"[Drafts] invoice_saved_successfully received -> merging if payload provided",
				payload,
			);
			// if caller prefers authoritative reload they can emit 'drafts_updated' explicitly
			// but we avoid fetch here to prevent bad-request races.
		});

		// initial load
		this.fetchDrafts();
	},

	beforeUnmount() {
		this.eventBus.off("open_drafts");
		this.eventBus.off("close_drafts");
		this.eventBus.off("draft_saved");
		this.eventBus.off("invoice_saved_successfully");
	},
};
</script>

<style scoped>
/* keep your existing styles unchanged */
.drafts-wrapper {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	background: white;
}
.drafts-content {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	background-color: #fafafa;
}
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
:deep(.v-data-table__tr--active) {
	background-color: rgba(76, 175, 80, 0.08) !important;
}
:deep(.v-data-table__tr--active:hover) {
	background-color: rgba(76, 175, 80, 0.12) !important;
}
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
