<template>
  <v-dialog v-model="model" width="420">
    <v-card>
      <v-card-title>Coupon Validate</v-card-title>
      <v-card-text>
        <v-text-field v-model="vehicle_no" label="Vehicle #" />
        <v-text-field v-model="coupon_no" label="Coupon #" />
        <div class="text-caption">Shows Staff Code, Staff Name, Points after validate.</div>
        <div v-if="result" class="mt-2">
          <div><b>Staff Code:</b> {{ result.staff_code }}</div>
          <div><b>Staff Name:</b> {{ result.staff_name }}</div>
          <div><b>Points:</b> {{ result.points }}</div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="model=false">Cancel</v-btn>
        <v-btn color="primary" @click="validate">Validate & Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import api from "@/utils/apiclient";

export default {
  name: "CouponDialog",
  props: { modelValue: Boolean },
  emits: ["update:modelValue"],
  data() {
    return { vehicle_no: "", coupon_no: "", result: null };
  },
  computed: {
    model: {
      get() { return this.modelValue; },
      set(v) { this.$emit("update:modelValue", v); },
    },
  },
  methods: {
    async validate() {
      const { data } = await api.post("/posawesome.api.lazer_pos.validate_coupon", {
        vehicle_no: this.vehicle_no,
        coupon_no: this.coupon_no,
      });
      this.result = data.message || data;
      if (this.result?.saved) {
        alert("Coupon saved.");
        this.model = false;
      }
    },
  },
};
</script>
