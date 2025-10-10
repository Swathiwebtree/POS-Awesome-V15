<template>
  <div class="grn-dashboard">
    <h2>Goods Receipt Notes (GRN)</h2>

    <!-- Filters -->
    <div class="filters mb-4">
      <input type="date" v-model="startDate" placeholder="From Date" class="input"/>
      <input type="date" v-model="endDate" placeholder="To Date" class="input"/>
      <input v-model="supplier" placeholder="Supplier" class="input"/>
      <input v-model="itemCode" placeholder="Item Code" class="input"/>
      <button @click="fetchGRNs" class="btn">Search</button>
    </div>

    <!-- GRN List Table -->
    <table>
      <thead>
        <tr>
          <th>GRN #</th><th>Date</th><th>Supplier</th><th>Total Qty</th>
          <th>Grand Total</th><th>Company</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="grn in grnList" :key="grn.name" @click="selectGRN(grn)">
          <td>{{ grn.name }}</td>
          <td>{{ grn.posting_date }}</td>
          <td>{{ grn.supplier_name }}</td>
          <td>{{ grn.total_qty }}</td>
          <td>{{ grn.grand_total }}</td>
          <td>{{ grn.company }}</td>
          <td>{{ grn.status }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Selected GRN Details -->
    <div v-if="selectedGRN" class="grn-details mt-4">
      <h3>GRN Details: {{ selectedGRN.name }}</h3>
      
      <!-- Items Tab -->
      <h4>Items</h4>
      <table>
        <thead>
          <tr>
            <th>Item Code</th><th>Item Name</th><th>Qty</th><th>Rate</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item,index) in selectedGRN.items" :key="index">
            <td>{{ item.item_code }}</td>
            <td>{{ item.item_name }}</td>
            <td>{{ item.qty }}</td>
            <td>{{ item.rate }}</td>
            <td>{{ item.amount }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const startDate = ref('');
const endDate = ref('');
const supplier = ref('');
const itemCode = ref('');

const grnList = ref([]);
const selectedGRN = ref(null);

const fetchGRNs = async () => {
  try {
    const res = await axios.get('/api/method/posawesome.posawesome.api.get_grn_list', {
      params: {
        start_date: startDate.value,
        end_date: endDate.value,
        supplier: supplier.value,
        item_code: itemCode.value
      }
    });
    grnList.value = res.data.message || [];
    selectedGRN.value = null;
  } catch (err) {
    console.error(err);
  }
}

const selectGRN = async (grn) => {
  if (!grn.items) {
    // Fetch items if not already loaded
    try {
      const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_grn_list', {
        params: { item_code: '', start_date: '', end_date: '', supplier: '', grn_no: grn.name }
      });
      selectedGRN.value = res.data.message[0] || grn;
    } catch (err) {
      console.error(err);
      selectedGRN.value = grn;
    }
  } else {
    selectedGRN.value = grn;
  }
}
</script>

<style scoped>
.grn-dashboard { padding: 10px; }
.filters { display: flex; gap: 10px; flex-wrap: wrap; }
.input { border: 1px solid #ccc; padding: 4px; width: 150px; }
.btn { background: #007bff; color: white; padding: 6px 12px; cursor: pointer; }
.btn:hover { background: #0056b3; }
table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
th, td { border: 1px solid #ccc; padding: 5px; text-align: left; }
tr:hover { background-color: #f5f5f5; cursor: pointer; }
.grn-details { margin-top: 20px; padding: 10px; border: 1px solid #ddd; background: #fafafa; }
</style>
