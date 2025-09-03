<template>
  <v-container class="pa-4">
    <div class="d-flex align-center mb-4">
      <v-btn variant="text" @click="$emit('back')">← Back</v-btn>
      <h2 class="text-h6 ml-4">Transactions</h2>
    </div>
    <v-list>
      <v-list-item v-for="m in modules" :key="m.key" @click="$emit('select', m.key)">
        <v-list-item-title>{{ m.title }}</v-list-item-title>
        <v-list-item-subtitle>{{ m.desc }}</v-list-item-subtitle>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script>
export default {
  name: "TransactionsMenu",
  emits: ["back", "select"],
  data() {
    return {
      modules: [
        { key: "vehicle_service", title: "Vehicle Service", desc: "" },
        { key: "vehicles_master", title: "Vehicles Master", desc: "" },
        { key: "service_issue_note", title: "Service Issue Note", desc: "" },
        { key: "quotation", title: "Quotation", desc: "" },
        { key: "petty_cash", title: "Petty Cash", desc: "" },
        { key: "receipt_voucher", title: "Receipt Voucher", desc: "" },
        { key: "item_inquiry", title: "Item Inquiry", desc: "(goes to item selector)" },
        { key: "sales_by_payment", title: "Sales by Payment", desc: "" },
        { key: "vehicle_history", title: "Vehicle History", desc: "" },
        { key: "redeemed_coupon_points", title: "Redeemed Coupon Points", desc: "" },
      ],
    };
  },
};
</script>
