<template>
  <div>
    <h2>Cash Counting</h2>
    <table>
      <tr>
        <th>Denomination</th>
        <th>Count</th>
        <th>Total</th>
      </tr>
      <tr v-for="item in cashDenominations" :key="item.denomination">
        <td>{{ item.denomination }}</td>
        <td><input type="number" v-model.number="item.count" @input="calculateTotal" /></td>
        <td>{{ item.total }}</td>
      </tr>
    </table>
    <p>Total Cash: {{ totalCash }}</p>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      cashDenominations: [
        { denomination: 1, count: 0, total: 0 },
        { denomination: 5, count: 0, total: 0 },
        { denomination: 10, count: 0, total: 0 },
        { denomination: 20, count: 0, total: 0 },
        { denomination: 50, count: 0, total: 0 },
        { denomination: 100, count: 0, total: 0 },
      ],
      totalCash: 0,
    };
  },
  methods: {
    calculateTotal() {
      this.totalCash = 0;
      this.cashDenominations.forEach(item => {
        item.total = item.denomination * item.count;
        this.totalCash += item.total;
      });
    },
    async submitCashCount() {
      await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.submit_cash_count", {
         cashDenominations: JSON.stringify(this.cashDenominations)
       });
    },
  },
};
</script>
