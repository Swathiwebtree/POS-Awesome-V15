<template>
  <div class="item-check">
    <h4>Item Inquiry / Check</h4>
    <input type="text" v-model="search" placeholder="Search by code or name"/>
    
    <table>
      <thead>
        <tr>
          <th>Barcode</th><th>Item Code</th><th>Name</th><th>Stock</th><th>Price</th><th>VAT</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item,index) in filteredItems" :key="index">
          <td>{{item.barcode}}</td>
          <td>{{item.code}}</td>
          <td>{{item.name}}</td>
          <td>{{item.stock_balance}}</td>
          <td>{{item.selling_price}}</td>
          <td>{{item.vat_price}}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const search = ref('');
const items = ref([]);

const filteredItems = computed(() => {
  return items.value.filter(i =>
    i.code.toLowerCase().includes(search.value.toLowerCase()) ||
    i.name.toLowerCase().includes(search.value.toLowerCase())
  )
});

async function fetchItems() {
  try {
    const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.');
    items.value = res.data.message || [];
  } catch (err) { console.error(err); }
}

onMounted(fetchItems);
</script>

<style scoped>
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #ccc; padding: 5px; }
input { width: 100%; padding: 5px; margin-bottom: 10px; }
</style>
