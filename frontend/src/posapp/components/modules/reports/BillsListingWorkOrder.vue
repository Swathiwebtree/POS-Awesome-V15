<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Bills Listing - Work Order</h2>

    <!-- Filters -->
    <div class="grid grid-cols-3 gap-2 mb-4">
      <input type="date" v-model="dateFrom" placeholder="Date From" class="input"/>
      <input type="date" v-model="dateTo" placeholder="Date To" class="input"/>
      <input v-model="workOrderNo" placeholder="Work Order No." class="input"/>
      <button class="btn col-span-3" @click="generateReport">Generate Report</button>
    </div>

    <!-- Report Table -->
    <table class="table-auto border w-full">
      <thead>
        <tr>
          <th>Work Order No.</th>
          <th>Bill No.</th>
          <th>Date</th>
          <th>Payment Method</th>
          <th>Vehicle No.</th>
          <th>Total Amount</th>
          <th>Discount</th>
          <th>Amount After Discount</th>
          <th>VAT Amount</th>
          <th>Net Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row,index) in reportData" :key="index">
          <td>{{ row.work_order_no }}</td>
          <td>{{ row.bill_no }}</td>
          <td>{{ row.date }}</td>
          <td>{{ row.payment_method }}</td>
          <td>{{ row.vehicle_no }}</td>
          <td>{{ row.total_amount }}</td>
          <td>{{ row.discount_amount }}</td>
          <td>{{ row.amount_after_discount }}</td>
          <td>{{ row.vat_amount }}</td>
          <td>{{ row.net_amount }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="9" class="text-right font-semibold">Grand Total</td>
          <td>{{ grandTotal }}</td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios"; // assuming axios is installed

const dateFrom = ref("");
const dateTo = ref("");
const workOrderNo = ref("");
const reportData = ref([]);

// Compute grand total of net amount
const grandTotal = computed(() => reportData.value.reduce((sum,row) => sum + (row.net_amount || 0), 0));

// Fetch report from API
const generateReport = async () => {
  try {
    const response = await axios.get("/api/method/posawesome.posawesome.api.lazer_pos.get_bills_listing_work_order", {
      params: {
        date_from: dateFrom.value,
        date_to: dateTo.value,
        work_order_no: workOrderNo.value
      }
    });
    reportData.value = response.data.message || [];
  } catch (err) {
    console.error(err);
    alert("Error fetching report!");
  }
};
</script>

<style scoped>
.input { border:1px solid #ccc; padding:4px; width:100%; }
.btn { background:#007bff; color:white; padding:6px 12px; cursor:pointer; margin-top:4px; }
.btn:hover { background:#0056b3; }
.table-auto th, .table-auto td { border:1px solid #ccc; padding:4px; text-align:left; }
</style>
