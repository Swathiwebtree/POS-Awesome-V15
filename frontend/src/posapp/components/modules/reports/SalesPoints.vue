<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Sales Points</h2>

    <!-- Filters -->
    <div class="grid grid-cols-4 gap-2 mb-4">
      <input type="date" v-model="dateFrom" class="input" placeholder="From Date"/>
      <input type="date" v-model="dateTo" class="input" placeholder="To Date"/>
      <input v-model="staffFrom" placeholder="Staff From" class="input"/>
      <input v-model="staffTo" placeholder="Staff To" class="input"/>
      <input v-model="terminalFrom" placeholder="Terminal From" class="input"/>
      <input v-model="terminalTo" placeholder="Terminal To" class="input"/>
      <button class="btn col-span-4" @click="generateReport">Generate Report</button>
    </div>

    <!-- Grouping Options -->
    <div class="mb-4">
      <label class="mr-2">Group By:</label>
      <select v-model="groupBy" class="input w-1/4">
        <option value="">None</option>
        <option value="date">Date</option>
        <option value="staff">Staff</option>
        <option value="terminal">Terminal</option>
      </select>
    </div>

    <!-- Report Table -->
    <table class="table-auto border w-full">
      <thead>
        <tr>
          <th>Date</th>
          <th>Staff</th>
          <th>Terminal</th>
          <th>Sales Amount</th>
          <th>Discount</th>
          <th>Net Sales</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row,index) in reportData" :key="index">
          <td>{{ row.date }}</td>
          <td>{{ row.staff }}</td>
          <td>{{ row.terminal }}</td>
          <td>{{ row.amount }}</td>
          <td>{{ row.discount }}</td>
          <td>{{ row.netSales }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="5" class="text-right font-semibold">Grand Total</td>
          <td>{{ grandTotal }}</td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios";

const dateFrom = ref("");
const dateTo = ref("");
const staffFrom = ref("");
const staffTo = ref("");
const terminalFrom = ref("");
const terminalTo = ref("");
const groupBy = ref("");

const reportData = ref([]);

// Calculate grand total of Net Sales
const grandTotal = computed(() =>
  reportData.value.reduce((sum, row) => sum + (row.netSales || 0), 0)
);

// Fetch report data from API
const generateReport = async () => {
  try {
    const params = {
      start_date: dateFrom.value,
      end_date: dateTo.value,
      staff: staffFrom.value || undefined, // pass only if value exists
      terminal: terminalFrom.value || undefined,
      group_by: groupBy.value || undefined,
    };

    const response = await axios.get("/api/method/posawesome.posawesome.api.lazer_pos.get_sales_points_list", { params });
    
    // Assuming API returns an array of rows
    reportData.value = response.data.message.map(row => ({
      date: row.date,
      staff: row.staff_name || row.staff_code,
      terminal: row.terminal,
      amount: row.total_points || 0,
      discount: row.discount || 0,       // replace with actual field if exists
      netSales: row.total_points || 0    // replace with actual net field if exists
    }));
  } catch (error) {
    console.error("Failed to fetch Sales Points report:", error);
    alert("Error fetching report. Check console for details.");
  }
};
</script>

<style scoped>
.input { border:1px solid #ccc; padding:4px; width:100%; margin-bottom:4px; }
.btn { background:#007bff; color:white; padding:6px 12px; cursor:pointer; margin-top:4px; }
.btn:hover { background:#0056b3; }
.table-auto { border-collapse: collapse; }
.table-auto th, .table-auto td { border:1px solid #ccc; padding:6px; }
</style>
