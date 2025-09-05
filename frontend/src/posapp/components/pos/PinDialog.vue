<template>
  <v-dialog v-model="model" max-width="420">
    <v-card>
      <v-card-title>Enter Cashier Code</v-card-title>

      <v-card-text>
        <v-text-field
          v-model="pin"
          label="Cashier Code"
          type="password"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="6"
          autocomplete="off"
          autofocus
          @keyup.enter="submit"
        />
        <div v-if="error" class="text-error text-caption mt-2">
          {{ error }}
        </div>
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
  },
  emits: ["update:modelValue", "success"],
  data() {
    return {
      pin: "",
      error: "",
    };
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
  watch: {
    model(newVal) {
      if (!newVal) {
        this.pin = "";
        this.error = "";
      }
    },
  },
  methods: {
    close() {
      this.model = false;
    },
    async submit() {
      // ================================
      // Original code commented for testing
      // ================================
      /*
      if (!this.pin) {
        this.error = "Please enter your cashier code";
        return;
      }

      try {
        // Fetch current POS Settings (single)
        const r = await frappe.call({
          method: "frappe.client.get",
          args: {
            doctype: "POS Settings",
            name: "POS Settings",
          },
        });

        const settings = r.message || {};
        if (settings.custom_cashier_code_ && settings.custom_cashier_code_ === String(this.pin).trim()) {
          this.$emit("success");
          this.close();
        } else {
          this.error = "Invalid cashier code.";
        }
      } catch (e) {
        console.error(e);
        this.error = "Error verifying cashier code.";
      }
      */

      // ================================
      // Bypass cashier code for testing
      // ================================
      this.$emit("success");
      this.close();
    },
  },
};
</script>

<style scoped>
.text-error {
  color: red;
}
</style>
