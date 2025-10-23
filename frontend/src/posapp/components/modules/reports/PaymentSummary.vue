<template>
  <div class="p-4">
    <h2 class="text-xl font-semibold mb-4">Payment Summary</h2>

    <!-- Filters -->
    <div class="grid grid-cols-4 gap-2 mb-4">
      <input type="date" v-model="dateFrom" class="input" placeholder="Date From" />
      <input type="date" v-model="dateTo" class="input" placeholder="Date To" />
      <select v-model="paymentType" class="input">
        <option value="">All Payment Types</option>
        <option v-for="p in paymentMethods" :key="p" :value="p">{{ p }}</option>
      </select>
      <button class="btn" @click="generateReport">Generate Report</button>
    </div>

    <!-- Report Table -->
    <table class="table-auto border w-full" v-if="reportData.length">
      <thead>
        <tr>
          <th>Date</th>
          <th>Transaction Number</th>
          <th>Payment Code</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in reportData" :key="idx">
          <td>{{ row.date }}</td>
          <td>{{ row.transaction_no }}</td>
          <td>{{ row.payment_code }}</td>
          <td>{{ row.amount }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="3" class="text-right font-semibold">Grand Total</td>
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
const paymentType = ref("");
const reportData = ref([]);
const paymentMethods = ref(["Cash", "Credit Card", "Coupon"]); // Adjust as per your system

// Generate report using global frappe.call
const generateReport = () => {
  if (!dateFrom.value || !dateTo.value) {
    alert("Please select both Date From and Date To");
    return;
  }

  frappe.call({
   method: "posawesome.posawesome.api.lazer_pos.get_payment_summary",
    args: {
      date_from: dateFrom.value,
      date_to: dateTo.value,
      payment_type: paymentType.value
    },
    callback: (r) => {
      reportData.value = r.message?.payments || [];
    }
  });
};

// Compute grand total
const grandTotal = computed(() =>
  reportData.value.reduce((sum, row) => sum + (row.amount || 0), 0)
);
</script>

<style scoped>
.input {
  border: 1px solid #ccc;
  padding: 6px;
  width: 100%;
  border-radius: 4px;
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
  width: 100%;
}

th, td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: center;
}

tfoot td {
  font-weight: bold;
}
</style>
