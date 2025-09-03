<template>
  <v-dialog v-model="model" max-width="420">
    <v-card>
      <v-card-title>Enter Cashier Code</v-card-title>
      <v-card-text>
        <v-text-field
          v-model="pin"
          label="Cashier Code"
          type="password"
          @keyup.enter="submit"
        />
        <div v-if="error" class="text-error text-caption mt-2">{{ error }}</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">Cancel</v-btn>
        <v-btn color="primary" @click="submit">Continue</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "PinDialog",
  props: {
    modelValue: { type: Boolean, default: false },
    expectedPin: { type: [String, Number], default: "" },
  },
  emits: ["update:modelValue", "success"],
  data() {
    return { pin: "", error: "" };
  },
  computed: {
    model: {
      get() {
        return this.modelValue;
      },
      set(v) {
        this.$emit("update:modelValue", v);
      },
    },
  },
  methods: {
    close() {
      this.model = false;
      this.pin = "";
      this.error = "";
    },
    submit() {
      if (!this.expectedPin) {
        frappe.msgprint("Missing cashier code in POS Settings.");
        return;
      }
      if (String(this.pin) === String(this.expectedPin)) {
        this.$emit("success");
        this.close();
      } else {
        this.error = "Invalid code";
      }
    },
  },
};
</script>
