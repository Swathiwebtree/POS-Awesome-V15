<template>
  <v-row justify="center">
    <!-- attach to body so dialog overlay appears above complex POS UI -->
    <v-dialog v-model="closingDialog" max-width="900px" persistent attach="body">
      <v-card elevation="8" class="closing-dialog-card">
        <!-- Header -->
        <v-card-title class="closing-header pa-6 d-flex align-center">
          <div class="header-content">
            <div class="header-icon-wrapper">
              <v-icon class="header-icon" size="40">mdi-store-clock-outline</v-icon>
            </div>
            <div class="header-text">
              <h3 class="header-title">{{ __("Closing POS Shift") }}</h3>
              <p class="header-subtitle">{{ __("Reconcile payment methods and close shift") }}</p>
            </div>
          </div>

          <v-spacer />

          <v-btn
            icon="mdi-close"
            variant="text"
            density="comfortable"
            class="header-close-btn"
            :title="__('Close')"
            @click="close_dialog"
          />
        </v-card-title>

        <v-divider class="header-divider" />

        <!-- Body: fixed max-height, scroll inside so overlay stays centered -->
        <v-card-text class="pa-0 white-background dialog-body">
          <v-container class="pa-6">
            <v-row>
              <v-col cols="12" class="pa-1">
                <div class="table-header mb-4">
                  <h4 class="text-h6 text-grey-darken-2 mb-1">{{ __("Payment Reconciliation") }}</h4>
                  <p class="text-body-2 text-grey">{{ __("Verify closing amounts for each payment method") }}</p>
                </div>

                <!-- Data table -->
                <v-data-table
                  :headers="headers"
                  :items="dialog_data.payment_reconciliation"
                  item-key="mode_of_payment"
                  class="elevation-0 rounded-lg white-table"
                  :items-per-page="itemsPerPage"
                  hide-default-footer
                  density="compact"
                >
                  <!-- mode label cell -->
                  <template v-slot:item.mode_of_payment="{ item }">
                    <div class="mode-cell">{{ item.mode_of_payment }}</div>
                  </template>

                  <!-- editable closing amount with number modifier -->
                  <template v-slot:item.closing_amount="props">
                    <v-text-field
                      v-model.number="props.item.closing_amount"
                      :rules="[closingAmountRule]"
                      single-line
                      type="number"
                      density="compact"
                      variant="outlined"
                      color="primary"
                      class="pos-themed-input closing-input"
                      hide-details
                      :prefix="companyCurrencySymbol"
                    />
                  </template>

                  <template v-slot:item.opening_amount="{ item }">
                    {{ companyCurrencySymbol }}{{ formatCurrency(item.opening_amount) }}
                  </template>

                  <template v-slot:item.expected_amount="{ item }">
                    {{ companyCurrencySymbol }}{{ formatCurrency(item.expected_amount) }}
                  </template>

                  <template v-slot:item.difference="{ item }">
                    {{ companyCurrencySymbol }}{{ formatCurrency((Number(item.expected_amount) || 0) - (Number(item.closing_amount) || 0)) }}
                  </template>
                </v-data-table>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>

        <v-divider />

        <v-card-actions class="dialog-actions-container">
          <!-- keep buttons to the right with comfortable spacing -->
          <v-spacer />
          <v-btn theme="dark" @click="submit_dialog" class="pos-action-btn submit-action-btn" size="large" elevation="2">
            <v-icon start>mdi-check-circle-outline</v-icon>
            <span>{{ __("Submit") }}</span>
          </v-btn>

          <!-- small gap between Submit and Close -->
          <div style="width:12px;"></div>

          <v-btn theme="dark" @click="close_dialog" class="pos-action-btn cancel-action-btn" size="large" elevation="2">
            <v-icon start>mdi-close-circle-outline</v-icon>
            <span>{{ __("Close") }}</span>
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
    // default to an object with array so template doesn't error before payload arrives
    dialog_data: { payment_reconciliation: [] },
    pos_profile: null,

    // Vuetify expects `text` keys in headers (some versions) — translations applied at runtime
    headers: [
      { text: "Mode of Payment", value: "mode_of_payment", align: "start" },
      { text: "Opening Amount", value: "opening_amount", align: "end" },
      { text: "Closing Amount", value: "closing_amount", align: "end" },
      // expected + difference may be appended dynamically
    ],

    extendedHeaders: [
      { text: "Expected Amount", value: "expected_amount", align: "end" },
      { text: "Difference", value: "difference", align: "end" },
    ],

    closingAmountRule: (v) => {
      if (v === "" || v === null || v === undefined) return true;
      const value = typeof v === "number" ? v : Number(String(v).trim());
      if (!Number.isFinite(value)) return "Please enter a valid number";
      const stringValue = String(v);
      const [integerPart, fractionalPart] = stringValue.split(".");
      if (integerPart.replace(/^-/, "").length > 20) return "Number is too large";
      if (fractionalPart && fractionalPart.length > 2) return "Maximum of 2 decimal places";
      return true;
    },

    pagination: {}
  }),

  computed: {
    isDarkTheme() {
      return this.$theme && this.$theme.current === "dark";
    },
    companyCurrencySymbol() {
      const currency = this.dialog_data?.currency || this.pos_profile?.currency || "";
      const symbol = this.currencySymbol(currency);
      return symbol || currency || "";
    }
  },

  methods: {
    close_dialog() {
      this.closingDialog = false;
    },

    async submit_dialog() {
      const reconciliation = this.dialog_data?.payment_reconciliation || [];
      const invalid = reconciliation.some((p) => isNaN(parseFloat(p.closing_amount)));
      if (invalid) {
        alert(this.__("Invalid closing amount"));
        return;
      }

      const balance_details = reconciliation.map((p) => ({
        mode_of_payment: p.mode_of_payment,
        closing_amount: Number(p.closing_amount) || 0,
        opening_amount: Number(p.opening_amount) || 0,
        expected_amount: Number(p.expected_amount) || 0,
        currency: p.currency || (this.pos_profile?.currency || "")
      }));

      try {
        const resp = await frappe.call({
          method: "posawesome.posawesome.api.shifts.close_shift_with_reconciliation",
          args: { balance_details: JSON.stringify(balance_details) }
        });

        const result = resp?.message ?? resp;
        if (result && (result.success === true || result === true)) {
          this.closingDialog = false;

          // emit event so other components can react
          try {
            this.eventBus?.emit("shift_closed", result);
          } catch (e) {
            // ignore
          }

          // try to open opening dialog, else fallback to reload
          try {
            const openingResp = await frappe.call({ method: "posawesome.posawesome.api.shifts.get_opening_dialog_data" });
            const openingData = openingResp?.message ?? openingResp;
            if (openingData) {
              if (this.eventBus && typeof this.eventBus.emit === "function") {
                this.eventBus.emit("open_OpeningDialog", openingData);
              } else {
                frappe.set_route("/");
                location.reload();
              }
            } else {
              frappe.set_route("/");
              location.reload();
            }
          } catch (errFetch) {
            console.error("Failed to fetch opening dialog data:", errFetch);
            frappe.set_route("/");
            location.reload();
          }

        } else {
          const errMsg = result?.message || this.__("Failed to close shift");
          console.error("close_shift_with_reconciliation failed:", result);
          alert(errMsg);
        }
      } catch (err) {
        console.error("submit_dialog error:", err);
        alert(this.__("Failed to close shift: ") + (err?.message || err));
      }
    }
  },

  created() {
    // robust eventBus resolution + DOM fallback
    this.eventBus = this.eventBus || window.eventBus || window.app_event_bus || null;

    // store handlers so we can remove them later
    this._onOpenClosingDialog = (raw) => {
      let data = raw && raw.detail ? raw.detail : raw;
      if (data && data.message && typeof data.message === "object") data = data.message;

      console.log("open_ClosingDialog payload:", data);

      if (!data) {
        console.warn("open_ClosingDialog called without payload");
        return;
      }

      // normalize reconciliation arrays (server may send different shapes)
      let recon = Array.isArray(data.payment_reconciliation) ? data.payment_reconciliation.slice() : Array.isArray(data.payments) ? data.payments.slice() : [];

      // fallback: if no reconciliation but payments_method provided, map to rows
      if ((!Array.isArray(recon) || recon.length === 0) && Array.isArray(data.payments_method) && data.payments_method.length) {
        recon = data.payments_method.map((pm) => ({
          mode_of_payment: pm.mode_of_payment || pm.name || pm.mode || pm.payment_name || String(pm.name || pm.mode || ""),
          opening_amount: Number(pm.opening_amount ?? pm.amount ?? 0),
          expected_amount: Number(pm.expected_amount ?? pm.amount ?? pm.total ?? 0),
          closing_amount: Number(pm.closing_amount ?? 0),
          currency: pm.currency || data.currency || (this.pos_profile && this.pos_profile.currency) || ""
        }));
      }

      // ensure numeric types and canonical keys
      recon = (recon || []).map((p) => ({
        mode_of_payment: p.mode_of_payment || p.mode || p.name || "",
        opening_amount: Number(p.opening_amount || p.amount || 0),
        expected_amount: Number(p.expected_amount || p.amount || 0),
        closing_amount: Number(p.closing_amount || 0),
        currency: p.currency || data.currency || (this.pos_profile && this.pos_profile.currency) || ""
      }));

      data.payment_reconciliation = recon;

      // set dialog data and open
      this.dialog_data = data;
      this.closingDialog = true;

      // translate and configure headers (Vuetify expects `text`)
      const base = [
        { text: this.__("Mode of Payment"), value: "mode_of_payment", align: "start" },
        { text: this.__("Opening Amount"), value: "opening_amount", align: "end" },
        { text: this.__("Closing Amount"), value: "closing_amount", align: "end" }
      ];
      const extended = [
        { text: this.__("Expected Amount"), value: "expected_amount", align: "end" },
        { text: this.__("Difference"), value: "difference", align: "end" }
      ];

      this.headers = (!this.pos_profile || !this.pos_profile.hide_expected_amount) ? [...base, ...extended] : base;
    };

    this._onRegisterPosProfile = (data) => {
      this.pos_profile = data.pos_profile || data;
      // update headers accordingly
      const base = [
        { text: this.__("Mode of Payment"), value: "mode_of_payment", align: "start" },
        { text: this.__("Opening Amount"), value: "opening_amount", align: "end" },
        { text: this.__("Closing Amount"), value: "closing_amount", align: "end" }
      ];
      const extended = [
        { text: this.__("Expected Amount"), value: "expected_amount", align: "end" },
        { text: this.__("Difference"), value: "difference", align: "end" }
      ];
      this.headers = (!this.pos_profile || !this.pos_profile.hide_expected_amount) ? [...base, ...extended] : base;
    };

    if (!window._closingDialogListenersRegistered) {
    if (this.eventBus && typeof this.eventBus.on === "function") {
      this.eventBus.on("open_ClosingDialog", this._onOpenClosingDialog);
      this.eventBus.on("register_pos_profile", this._onRegisterPosProfile);
    }

    window.addEventListener("open_ClosingDialog", this._onOpenClosingDialog);
    window.addEventListener("register_pos_profile", this._onRegisterPosProfile);
    
    // Mark as registered
    window._closingDialogListenersRegistered = true;
  }
},

  beforeUnmount() {
    if (this.eventBus && typeof this.eventBus.off === "function") {
      this.eventBus.off("open_ClosingDialog", this._onOpenClosingDialog);
      this.eventBus.off("register_pos_profile", this._onRegisterPosProfile);
    }
    window.removeEventListener("open_ClosingDialog", this._onOpenClosingDialog);
    window.removeEventListener("register_pos_profile", this._onRegisterPosProfile);
  }
};
</script>

<style scoped>
/* Card header */
.closing-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e0e0e0;
  padding: 16px 24px !important;
}
.header-content { display:flex; align-items:center; gap:18px; width:100%; }
.header-icon-wrapper { width:56px; height:56px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  background: linear-gradient(135deg,#1976d2 0%,#1565c0 100%); box-shadow:0 8px 18px rgba(25,118,210,0.16); }
.header-icon { color:#fff !important; }
.header-text { flex:1; }
.header-title { font-size:1.25rem; margin:0; font-weight:600; color:#111; }
.header-subtitle { margin:0; color:#666; font-size:0.9rem; }

/* close button style */
.header-close-btn { color:#6b7280 !important; }

/* Body - limit height and allow internal scrolling so overlay remains centered and not huge */
.dialog-body {
  max-height: calc(100vh - 220px);
  overflow: auto;
  padding: 0;
  background: var(--pos-card-bg, #fff);
}

/* Table visuals */
.white-table {
  background-color: var(--pos-card-bg, #fff);
  border: 1px solid var(--pos-border, #e6e6e6);
  border-radius: 8px;
  overflow: visible;
}

/* Ensure the table header wraps nicely on small screens */
.white-table th, .white-table td {
  padding: 10px 14px;
  vertical-align: middle;
  white-space: nowrap;
}

/* mode cell */
.mode-cell { font-weight:600; }

/* Text field inside table should fill available space and sit above other elements */
.closing-input {
  min-width: 220px;
  max-width: 100%;
  width: 260px;
}

/* Action buttons */
.dialog-actions-container {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-top: 1px solid var(--pos-border, #e6e6e6);
  padding: 14px 20px;
  gap: 12px;
}

/* button styles */
.pos-action-btn { border-radius: 12px; text-transform:none; font-weight:600; padding: 10px 26px; color:#fff !important; }
.submit-action-btn { background: linear-gradient(135deg,#388e3c 0%,#2e7d32 100%) !important; }
.cancel-action-btn { background: linear-gradient(135deg,#d32f2f 0%,#c62828 100%) !important; }

/* z-index fixes so dialog sits above complex app UI */
:deep(.v-overlay__scrim) { z-index: 100999 !important; }
:deep(.v-overlay__content) { z-index: 101000 !important; }
:deep(.v-dialog) { z-index: 101001 !important; }

/* smaller screens adjustments */
@media (max-width: 900px) {
  .closing-input { width: 100%; min-width: unset; }
  .dialog-body { max-height: calc(100vh - 140px); padding-left:12px; padding-right:12px; }
  .header-title { font-size: 1.1rem; }
}

/* ensure overlay visually hides underlying UI a bit more */
:deep(.v-overlay__scrim) { background-color: rgba(0,0,0,0.45) !important; }
</style>
