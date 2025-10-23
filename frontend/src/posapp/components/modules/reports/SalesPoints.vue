<template>
  <div class="stock-points-dashboard p-4">
    <h2 class="mb-4">Stock Points Report</h2>

    <!-- Filters -->
    <div class="filters grid grid-cols-3 gap-4 mb-4">
      <div>
        <label>From Date</label>
        <input type="date" v-model="filters.from_date" class="input" />
      </div>
      <div>
        <label>To Date</label>
        <input type="date" v-model="filters.to_date" class="input" />
      </div>
      <div>
        <label>Report Group By</label>
        <select v-model="filters.report_group_by" class="input">
          <option value="Date">Date</option>
          <option value="Staff">Staff</option>
          <option value="Terminal">Terminal</option>
        </select>
      </div>
      <div>
        <label>From Staff</label>
        <input type="text" v-model="filters.from_staff" placeholder="Staff Name" class="input" />
      </div>
      <div>
        <label>To Staff</label>
        <input type="text" v-model="filters.to_staff" placeholder="Staff Name" class="input" />
      </div>
      <div>
        <label>From Terminal</label>
        <input type="text" v-model="filters.from_terminal" placeholder="Terminal" class="input" />
      </div>
      <div>
        <label>To Terminal</label>
        <input type="text" v-model="filters.to_terminal" placeholder="Terminal" class="input" />
      </div>
    </div>

    <button class="btn btn-primary mb-4" @click="fetchReport">Generate Report</button>

    <!-- Report Table -->
    <div v-if="items.length" class="overflow-x-auto">
      <table class="table-auto w-full border border-gray-300">
        <thead>
          <tr class="bg-gray-200">
            <th class="px-2 py-1 border">Date</th>
            <th class="px-2 py-1 border">Staff</th>
            <th class="px-2 py-1 border">Terminal</th>
            <th class="px-2 py-1 border">Item</th>
            <th class="px-2 py-1 border">Quantity</th>
            <th class="px-2 py-1 border">Amount</th>
            <th class="px-2 py-1 border">Discount</th>
            <th class="px-2 py-1 border">Net Sales</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="index">
            <td class="px-2 py-1 border">{{ item.date }}</td>
            <td class="px-2 py-1 border">{{ item.staff }}</td>
            <td class="px-2 py-1 border">{{ item.terminal }}</td>
            <td class="px-2 py-1 border">{{ item.item }}</td>
            <td class="px-2 py-1 border text-right">{{ item.quantity }}</td>
            <td class="px-2 py-1 border text-right">{{ item.amount.toFixed(2) }}</td>
            <td class="px-2 py-1 border text-right">{{ item.discount.toFixed(2) }}</td>
            <td class="px-2 py-1 border text-right">{{ item.net_sales.toFixed(2) }}</td>
          </tr>
          <!-- Grand Total -->
          <tr class="font-bold bg-gray-100">
            <td class="px-2 py-1 border" colspan="4">Grand Total</td>
            <td class="px-2 py-1 border text-right">{{ totalQuantity }}</td>
            <td class="px-2 py-1 border text-right">{{ totalAmount.toFixed(2) }}</td>
            <td class="px-2 py-1 border text-right">{{ totalDiscount.toFixed(2) }}</td>
            <td class="px-2 py-1 border text-right">{{ totalNetSales.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-gray-500 mt-4">No data found.</div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "StockPointsReport",
  data() {
    return {
      filters: {
        from_date: "",
        to_date: "",
        from_staff: "",
        to_staff: "",
        from_terminal: "",
        to_terminal: "",
        report_group_by: "Date",
      },
      items: [],
    };
  },
  computed: {
    totalQuantity() {
      return this.items.reduce((sum, i) => sum + i.quantity, 0);
    },
    totalAmount() {
      return this.items.reduce((sum, i) => sum + i.amount, 0);
    },
    totalDiscount() {
      return this.items.reduce((sum, i) => sum + i.discount, 0);
    },
    totalNetSales() {
      return this.items.reduce((sum, i) => sum + i.net_sales, 0);
    },
  },
  methods: {
    async fetchReport() {
      try {
        const query = {
          filters: {
            posting_date: ["between", [this.filters.from_date, this.filters.to_date]],
            staff: ["between", [this.filters.from_staff, this.filters.to_staff]],
            terminal: ["between", [this.filters.from_terminal, this.filters.to_terminal]],
          },
        };

        const response = await axios.get("/api/resource/Stock Points Item", { params: query });
        this.items = response.data.data;
      } catch (err) {
        console.error(err);
        this.items = [];
      }
    },
  },
};
</script>

<style scoped>
.input {
  width: 100%;
  padding: 4px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.btn {
  padding: 6px 12px;
  border-radius: 4px;
}
</style>
