<template>
  <v-container>
    <h2 class="text-h5 text-center mb-6">Work Orders</h2>
    <v-data-table
      :items="workOrders"
      :headers="headers"
      item-key="work_order_no"
      @click:row="selectWorkOrder"
    ></v-data-table>
  </v-container>
</template>

<script>
import apiClient from "@/utils/apiclient";

export default {
  name: "Dashboard",
  data() {
    return {
      workOrders: [],
      headers: [
        { text: "Date", value: "date" },
        { text: "Work Order #", value: "work_order_no" },
        { text: "Model", value: "model" },
        { text: "Vehicle #", value: "vehicle_no" },
        { text: "Mob #", value: "mobile_no" },
        { text: "Lift Staff", value: "lift_staff" },
        { text: "Status", value: "status" },
      ],
    };
  },
  created() {
    this.fetchWorkOrders();
  },
  methods: {
    async fetchWorkOrders() {
      const res = await apiClient.get("/pos/work_orders");
      this.workOrders = res.data;
    },
    selectWorkOrder(order) {
      this.$router.push({ name: "Pos", params: { workOrder: order } });
    },
  },
};
</script>
