<template>
  <v-dialog :model-value="open" @update:model-value="$emit('update:open', $event)" max-width="400">
    <v-card>
      <v-card-title>Loyalty / Coupon</v-card-title>
      <v-card-text>
        <v-text-field label="Vehicle #" v-model="vehicleNo" />
        <v-text-field label="Coupon #" v-model="couponNo" />
        <v-text-field label="Staff Code" :value="staffCode" readonly />
        <v-text-field label="Staff Name" :value="staffName" readonly />
        <v-text-field label="Current Points" :value="points" readonly />

        <v-alert v-if="errorMsg" type="error" dense class="mt-2">{{ errorMsg }}</v-alert>
        <v-alert v-if="successMsg" type="success" dense class="mt-2">{{ successMsg }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn color="primary" @click="validateCoupon" :loading="loading">Validate</v-btn>
        <v-btn text @click="closeDialog">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';

export default {
  props: {
    open: Boolean,
    staffCode: String,
    staffName: String,
    points: Number
  },
  data() {
    return {
      vehicleNo: '',
      couponNo: '',
      loading: false,
      errorMsg: '',
      successMsg: ''
    };
  },
  methods: {
    async validateCoupon() {
      this.loading = true;
      this.errorMsg = '';
      this.successMsg = '';
      try {
        const response = await axios.post('/api/method/posawesome.api.validate_loyalty_coupon', {
          vehicle_no: this.vehicleNo,
          coupon_no: this.couponNo,
          staff_code: this.staffCode
        });

        const data = response.data.message;

        if (data.success) {
          this.successMsg = data.message;
          this.$emit('applyCoupon', this.couponNo); 
          this.$emit('update:points', data.total_points);
        } else {
          this.errorMsg = data.message;
        }
      } catch (error) {
        this.errorMsg = error.response?.data?.message || 'Server error';
      } finally {
        this.loading = false;
      }
    },
    closeDialog() {
      this.$emit('update:open', false);
    }
  }
};
</script>
