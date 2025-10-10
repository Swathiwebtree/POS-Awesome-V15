<!-- src/posapp/components/modules/transactions/LoyaltyCardDialog.vue --> 
<template>
  <v-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" max-width="400px">
    <v-card>
      <v-card-title>Loyalty Card</v-card-title>
      <v-card-text>
        <v-text-field
          v-model="cardNumber"
          label="Enter Loyalty Card Number"
          autofocus
        />
        <div class="mt-2">
          <v-btn small @click="backspace">Backspace</v-btn>
          <v-btn small @click="clear">Clear</v-btn>
          <v-btn small color="success" @click="finish">Finish</v-btn>
          <v-btn small color="error" @click="cancel">Cancel</v-btn>
        </div>
        <div v-if="error" class="red--text mt-2">{{ error }}</div>
        <div v-if="customer" class="mt-2">
          <strong>Customer:</strong> {{ customer.customer_name }}<br>
          <strong>Points:</strong> {{ customer.points }}
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "LoyaltyCardDialog",
  props: {
    visible: Boolean, // prop passed from parent
  },
  data() {
    return {
      cardNumber: "",
      customer: null,
      error: "",
    };
  },
  methods: {
    backspace() {
      this.cardNumber = this.cardNumber.slice(0, -1);
    },
    clear() {
      this.cardNumber = "";
      this.customer = null;
      this.error = "";
    },
    cancel() {
      this.clear();
      this.$emit("update:visible", false); // close dialog
    },
    async finish() {
      if (!this.cardNumber) return;
      try {
        const res = await fetch("/api/method/posawesome.api.get_loyalty_customer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ card_number: this.cardNumber }),
        });
        const data = await res.json();
        if (data.message) {
          this.customer = data.message;
          this.error = "";
          this.$emit("applyLoyalty", this.customer);
        } else {
          this.error = "Invalid Loyalty Card Number";
          this.customer = null;
        }
      } catch (e) {
        this.error = "Error fetching customer";
      }
    },
  },
};
</script>

<style scoped>
.v-card-text div {
  display: flex;
  gap: 4px;
}
</style>
