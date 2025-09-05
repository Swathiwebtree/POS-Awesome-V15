<template>
  <v-dialog v-model="model" fullscreen scrollable>
    <v-card>
      <v-toolbar density="compact">
        <v-toolbar-title>Listings</v-toolbar-title>
        <v-spacer/>
        <v-text-field v-model="search" label="Search" density="compact" style="max-width:260px"/>
        <v-btn variant="text" @click="model=false">Close</v-btn>
      </v-toolbar>

      <v-card-text class="pa-0">
        <v-data-table
          :headers="headers"
          :items="filtered"
          item-key="bill_no"
          density="comfortable"
          fixed-header
          height="80vh"
          :items-per-page="50"
        />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import api from "@/utils/apiclient";

export default {
  name: "ListingsSheet",
  props: { modelValue: Boolean },
  emits: ["update:modelValue"],
  data() {
    return {
      rows: [],
      search: "",
      headers: [
        { title: "Sales", key: "sales" },
        { title: "Hold Remarks", key: "hold_remarks" },
        { title: "Customer ID", key: "customer_id" },
        { title: "Default Disc Stock", key: "default_disc_stock" },
        { title: "Stock Disc", key: "stock_discount" },
        { title: "Discount %", key: "discount_percent" },
        { title: "Is Hold", key: "is_hold" },
        { title: "Max Disc Stock", key: "max_disc_stock" },
        { title: "Pay Type", key: "pay_type" },
        { title: "Service Discount", key: "service_discount" },
        { title: "Customer Name", key: "customer_name" },
        { title: "Default Disc Service", key: "default_disc_service" },
        { title: "Time", key: "time" },
        { title: "Lift Code", key: "lift_code" },
        { title: "Discount", key: "discount" },
        { title: "Tel No", key: "telephone_no" },
        { title: "VAT", key: "vat" },
        { title: "Max Disc Service", key: "max_disc_service" },
        { title: "Net", key: "net" },
        { title: "Is Open", key: "is_open" },
        { title: "Paid", key: "paid" },
        { title: "Change", key: "change" },
        { title: "Loyalty Card No.", key: "loyalty_card_no" },
        { title: "WA EXPDATE", key: "wa_expdate" },
        { title: "Customer", key: "customer" },
        { title: "Loyalty Card Name", key: "loyalty_card_name" },
        { title: "R Bill Points", key: "r_bill_points" },
        { title: "Bill Points", key: "bill_points" },
        { title: "Closing ID", key: "closing_id" },
        { title: "Shift Closing ID", key: "shift_closing_id" },
        { title: "FC Used", key: "fc_used" },
        { title: "Return No", key: "return_no" },
        { title: "Bill No.", key: "bill_no" },
        { title: "Date", key: "date" },
        { title: "Disc Voucher #", key: "disc_voucher_no" },
        { title: "Station No", key: "station_no" },
        { title: "Work Order #", key: "work_order_no" },
        { title: "FC No", key: "fc_no" },
        { title: "Is Additional No", key: "is_additional_no" },
        { title: "Cashier", key: "cashier" },
        { title: "Next Service", key: "next_service" },
        { title: "Salespoint", key: "salespoint" },
        { title: "Table", key: "table_no" },
        { title: "Vehicle #", key: "vehicle_no" },
        { title: "Model #", key: "model_no" },
        { title: "Time In", key: "time_in" },
        { title: "Make", key: "make" },
        { title: "Mileage (KMs)", key: "mileage" },
        { title: "Tel (Mobile No.)", key: "mobile_no" },
        { title: "Customer", key: "customer2" },
        { title: "Customer Name", key: "customer_name2" },
      ],
    };
  },
  computed: {
    model: {
      get() { return this.modelValue; },
      set(v) { this.$emit("update:modelValue", v); },
    },
    filtered() {
      const q = (this.search || "").toLowerCase();
      return this.rows.filter(r => Object.values(r).some(v => String(v ?? "").toLowerCase().includes(q)));
    },
  },
  async mounted() {
    const { data } = await api.get("/posawesome.api.lazer_pos.sales_listings", { params: { limit: 500 } });
    this.rows = data.message || data || [];
  },
};
</script>
