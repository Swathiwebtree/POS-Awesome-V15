<template>
  <v-container>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-4">
      <h2 class="text-h5">Work Orders</h2>
      <div>
        <span v-if="cashier">Cashier: <strong>{{ cashier.employee_name }}</strong></span>
        <v-btn small color="error" class="ml-3" @click="logout">Logout</v-btn>
      </div>
    </div>

    <!-- Work Orders Table -->
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
      cashier: null,
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
    this.checkCashier();
    this.fetchWorkOrders();
  },
  methods: {
    async fetchWorkOrders() {
      try {
        const res = await apiClient.get("/pos/work_orders");
        this.workOrders = res.data;
      } catch (err) {
        console.error("Error fetching work orders:", err);
      }
    },
    selectWorkOrder(order) {
      this.$router.push({ name: "Pos", params: { workOrder: order } });
    },
    checkCashier() {
      const savedCashier = localStorage.getItem("cashier");
      if (savedCashier) {
        this.cashier = JSON.parse(savedCashier);
      } else {
        // this.$router.push("/cashier-login");  (commented out)

        //  Bypass cashier login
        this.cashier = {
          name: "Test Cashier",
          employee_name: "Test Employee",
          user: "Administrator",
          terminal: "Default Terminal",
          role: "Cashier",
        };
        localStorage.setItem("cashier", JSON.stringify(this.cashier));
      }
    },

  },
};
</script>
