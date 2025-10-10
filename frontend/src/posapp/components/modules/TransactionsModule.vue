<template>
  <ModuleShell title="Transactions">
    <component :is="activeComponent" v-if="activeComponent" />
    <div v-else class="pa-4">Select a transaction submodule</div>
  </ModuleShell>
</template>

<script>
import { defineAsyncComponent, computed } from "vue";
import ModuleShell from "./ModuleShell.vue";

// Lazy-load all transaction submodules
const VehicleService = defineAsyncComponent(() => import("./transactions/VehicleService.vue"));
const VehiclesMaster = defineAsyncComponent(() => import("./transactions/VehiclesMaster.vue"));
const ServiceIssueNote = defineAsyncComponent(() => import("./transactions/ServiceIssueNote.vue"));
const Quotation = defineAsyncComponent(() => import("./transactions/Quotation.vue"));
const PettyCash = defineAsyncComponent(() => import("./transactions/PettyCash.vue"));
const ReceiptVoucher = defineAsyncComponent(() => import("./transactions/ReceiptVoucher.vue"));
const ItemInquiry = defineAsyncComponent(() => import("./transactions/ItemInquiry.vue"));
const SalesByPayment = defineAsyncComponent(() => import("./transactions/SalesByPayment.vue"));
const VehicleHistory = defineAsyncComponent(() => import("./transactions/VehicleHistory.vue"));
const RedeemedCouponPoints = defineAsyncComponent(() => import("./transactions/RedeemedCouponPoints.vue"));

export default {
  name: "TransactionsModule",
  components: {
    ModuleShell,
  },
  props: {
    defaultSubmodule: {
      type: String,
      default: "VehicleService", // default after cashier login
    },
  },
  setup(props) {
    const componentMap = {
      VehicleService,
      VehiclesMaster,
      ServiceIssueNote,
      Quotation,
      PettyCash,
      ReceiptVoucher,
      ItemInquiry,
      SalesByPayment,
      VehicleHistory,
      RedeemedCouponPoints,
    };

    const activeComponent = computed(() => componentMap[props.defaultSubmodule] || null);

    return { activeComponent };
  },
};
</script>

<style scoped>
</style>
