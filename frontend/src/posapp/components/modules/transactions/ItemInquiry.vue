<template>
  <div class="item-check-dashboard">
    <h3>Item Inquiry</h3>

    <!-- Search Field -->
    <input
      type="text"
      v-model="search"
      placeholder="Search by Barcode, Code or Name"
      class="search-input"
    />

    <!-- Primary Item Table -->
    <table class="item-table">
      <thead>
        <tr>
          <th>Barcode</th>
          <th>Item Code</th>
          <th>Name</th>
          <th>Supplier</th>
          <th>Stock</th>
          <th>Price</th>
          <th>VAT</th>
          <th>Unit</th>
          <th>Scale</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredItems" :key="item.barcode">
          <td>{{ item.barcode }}</td>
          <td>{{ item.item_code }}</td>
          <td>{{ item.item_name }}</td>
          <td>{{ item.supplier_name }}</td>
          <td>{{ item.stock_balance }}</td>
          <td>{{ item.selling_price }}</td>
          <td>{{ item.vat_price }}</td>
          <td>{{ item.unit }}</td>
          <td>{{ item.scale }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Selling Price Level Table -->
    <h4>Selling Price Levels</h4>
    <table class="price-level-table">
      <thead>
        <tr>
          <th>Price ID</th>
          <th>Price Level</th>
          <th>Barcode</th>
          <th>Price</th>
          <th>Price + VAT</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="level in priceLevels" :key="level.price_id">
          <td>{{ level.price_id }}</td>
          <td>{{ level.price_level }}</td>
          <td>{{ level.barcode }}</td>
          <td>{{ level.price }}</td>
          <td>{{ level.price_vat }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Stock in Hand Table -->
    <h4>Stock in Hand</h4>
    <table class="stock-hand-table">
      <thead>
        <tr>
          <th>Location Name</th>
          <th>Balance</th>
          <th>Shelf No</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="stock in stockInHand" :key="stock.location_name">
          <td>{{ stock.location_name }}</td>
          <td>{{ stock.balance }}</td>
          <td>{{ stock.shelf_no }}</td>
        </tr>
      </tbody>
    </table>

    <button @click="printBarcodes" class="print-btn">Print Barcode</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";

const search = ref("");
const items = ref([]);
const priceLevels = ref([]);
const stockInHand = ref([]);

// Filter items by search query
const filteredItems = computed(() =>
  items.value.filter(
    (i) =>
      i.item_code.toLowerCase().includes(search.value.toLowerCase()) ||
      i.item_name.toLowerCase().includes(search.value.toLowerCase()) ||
      i.barcode.toLowerCase().includes(search.value.toLowerCase())
  )
);

// Fetch all items
async function fetchItems() {
  try {
    const res = await axios.get("/api/posawesome.posawesome.api.lazer_pos.get_list");
    items.value = res.data.items || [];
    priceLevels.value = res.data.price_levels || [];
    stockInHand.value = res.data.stock_in_hand || [];
  } catch (err) {
    console.error("Error fetching items:", err);
  }
}

// Print Barcode
function printBarcodes() {
  window.print();
}

// Load data on mount
onMounted(fetchItems);
</script>

<style scoped>
.item-check-dashboard {
  padding: 10px;
}

.search-input {
  width: 100%;
  padding: 6px;
  margin-bottom: 10px;
  font-size: 14px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
}

th,
td {
  border: 1px solid #ccc;
  padding: 6px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

.print-btn {
  padding: 8px 12px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}

.print-btn:hover {
  background-color: #0056b3;
}
</style>
