<template>
  <v-container class="d-flex flex-column align-center justify-center" style="height:100vh">
    <v-text-field
      v-model="loginCode"
      label="Cashier Login Code"
      type="password"
      class="mb-4"
    />
    <v-btn color="primary" @click="loginCashier">Login</v-btn>
    <div v-if="error" class="text-error mt-2">{{ error }}</div>
  </v-container>
</template>

<script>
import apiClient from "@/utils/apiclient";

export default {
  name: "CashierLogin",
  data() {
    return {
      loginCode: "",
      cashiers: [],
      error: "",
    };
  },
  async mounted() {
    try {
      const res = await apiClient.get(
        "/api/method/posawesome.posawesome.api.posapp.get_cashiers"
      );
      if (res.data.message) {
        this.cashiers = res.data.message;
      }
    } catch (err) {
      console.error("Error fetching cashiers:", err);
    }
  },
  methods: {
    async loginCashier() {
      if (!this.loginCode) {
        this.error = "Please enter a cashier code";
        return;
      }

      const cashier = this.cashiers.find(c => String(c.code) === String(this.loginCode));

      if (cashier) {
        //  Success
        this.$router.push("/dashboard");
      } else {
        this.error = "Invalid login code";
      }
    },
  },
};
</script>
