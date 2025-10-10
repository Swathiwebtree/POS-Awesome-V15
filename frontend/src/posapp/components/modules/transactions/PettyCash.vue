<template>
  <div class="petty-cash">
    <h4>Petty Cash Dashboard</h4>
    <table>
      <thead>
        <tr>
          <th>PC #</th><th>Ref</th><th>Station ID</th><th>Date</th>
          <th>Description</th><th>User ID</th><th>Remarks</th>
          <th>Shift Closing</th><th>Count Closing</th><th>Day Closing</th><th>Total</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(entry, idx) in pettyCashList" :key="idx">
          <td>{{entry.pc_no}}</td>
          <td>{{entry.ref}}</td>
          <td>{{entry.station_id}}</td>
          <td>{{entry.date}}</td>
          <td>{{entry.description}}</td>
          <td>{{entry.user_id}}</td>
          <td>{{entry.remarks}}</td>
          <td>{{entry.shift_closing_id}}</td>
          <td>{{entry.count_closing_id}}</td>
          <td>{{entry.day_closing_id}}</td>
          <td>{{entry.total}}</td>
        </tr>
      </tbody>
    </table>

    <div v-for="(entry, idx) in pettyCashList" :key="'items-'+idx">
      <h5>Item Details for {{ entry.pc_no }}</h5>
      <table>
        <thead>
          <tr>
            <th>A/C Code</th><th>Account Name</th><th>Description</th><th>Amount</th>
            <th>Div</th><th>Account ID</th><th>Date</th><th>Typ</th>
            <th>Trans #</th><th>Ref #</th><th>Cur</th><th>Paid (Foreign)</th><th>Paid (Local)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item,i) in entry.items" :key="i">
            <td>{{item.ac_code}}</td>
            <td>{{item.account_name}}</td>
            <td>{{item.description}}</td>
            <td>{{item.amount}}</td>
            <td>{{item.division}}</td>
            <td>{{item.account_id}}</td>
            <td>{{item.date}}</td>
            <td>{{item.typ}}</td>
            <td>{{item.trans_no}}</td>
            <td>{{item.ref_no}}</td>
            <td>{{item.currency}}</td>
            <td>{{item.paid_foreign}}</td>
            <td>{{item.paid_local}}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const pettyCashList = ref([]);

async function fetchPettyCash() {
  try {
    const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_petty_cash_transactions');
    pettyCashList.value = res.data.message || [];
  } catch (err) {
    console.error(err);
  }
}

onMounted(() => fetchPettyCash());
</script>

<style scoped>
table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
th, td { border: 1px solid #ccc; padding: 6px; }
</style>
