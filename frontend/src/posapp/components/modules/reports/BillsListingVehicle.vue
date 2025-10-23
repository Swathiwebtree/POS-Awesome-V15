<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Bills Listing - Vehicle</h2>

    <!-- Filters -->
    <div class="grid grid-cols-3 gap-2 mb-4">
      <input type="date" v-model="dateFrom" class="input" placeholder="Date From" />
      <input type="date" v-model="dateTo" class="input" placeholder="Date To" />
      <input v-model="vehicleNo" placeholder="Vehicle No." class="input" />
      <button class="btn" @click="generateReport">Generate Report</button>
    </div>

    <!-- Report Table -->
    <table class="table-auto border w-full" v-if="reportData.length">
      <thead>
        <tr>
          <th>Vehicle No.</th>
          <th>Bill No.</th>
          <th>Work Order No.</th>
          <th>Date</th>
          <th>Payment Method</th>
          <th>Time In</th>
          <th>Time Out</th>
          <th>Vehicle Count</th>
          <th>Total Amount</th>
          <th>Discount</th>
          <th>Amount After Discount</th>
          <th>VAT Amount</th>
          <th>Net Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in reportData" :key="index">
          <td>{{ row.vehicle_no }}</td>
          <td>{{ row.bill_no }}</td>
          <td>{{ row.work_order_no }}</td>
          <td>{{ row.date }}</td>
          <td>{{ row.payment_method }}</td>
          <td>{{ row.time_in }}</td>
          <td>{{ row.time_out }}</td>
          <td>{{ row.vehicle_count || 1 }}</td>
          <td>{{ row.total_amount }}</td>
          <td>{{ row.discount_amount }}</td>
          <td>{{ row.amount_after_discount }}</td>
          <td>{{ row.vat_amount }}</td>
          <td>{{ row.net_amount }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="12" class="text-right font-semibold">Grand Total</td>
          <td>{{ grandTotal }}</td>
        </tr>
      </tfoot>
    </table>

    <div v-else class="text-center mt-4 text-gray-600">No records found.</div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const dateFrom = ref("");
const dateTo = ref("");
const vehicleNo = ref("");
const reportData = ref([]);

// Fetch report using frappe.call
const generateReport = () => {
  if (!vehicleNo.value) {
    alert("Please enter Vehicle No.");
    return;
  }

  frappe.call({
    method: "posawesome.posawesome.api.lazer_pos.get_bills_listing_vehicle",
    args: {
      vehicle_no: vehicleNo.value,
      from_date: dateFrom.value,
      to_date: dateTo.value,
    },
    callback: (r) => {
      reportData.value = r.message?.bills || [];
    },
    error: (err) => {
      console.error(err);
      alert("Error fetching report.");
    },
  });
};

// Compute Grand Total
const grandTotal = computed(() =>
  reportData.value.reduce((sum, row) => sum + (row.net_amount || 0), 0)
);
</script>

<style scoped>
.input {
  border: 1px solid #ccc;
  padding: 4px;
  width: 100%;
}
.btn {
  background: #007bff;
  color: white;
  padding: 4px 8px; 
  cursor: pointer;
  margin-top: 4px;
  font-size: 0.875rem;
}
.btn:hover {
  background: #0056b3;
}
table {
  border-collapse: collapse;
}
th,
td {
  border: 1px solid #ccc;
  padding: 6px;
  text-align: center;
}
tfoot td {
  font-weight: bold;
}
</style>
