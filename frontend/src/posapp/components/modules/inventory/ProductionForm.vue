<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Production Form</h2>

    <div class="grid grid-cols-3 gap-2 mb-4">
      <input v-model="prodNumber" placeholder="Prod #" class="input"/>
      <input v-model="division" placeholder="Division" class="input"/>
      <input type="date" v-model="date" class="input"/>
      <input v-model="stationId" placeholder="Station ID" class="input"/>
      <input v-model="userId" placeholder="User ID" class="input"/>
    </div>

    <table class="table-auto border w-full mb-4">
      <thead>
        <tr>
          <th>Barcode</th><th>Item Code</th><th>Item Name</th><th>Qty</th>
          <th>Unit</th><th>Factor</th><th>Net Qty</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item,index) in items" :key="index">
          <td><input v-model="item.barcode" class="input"/></td>
          <td><input v-model="item.code" class="input"/></td>
          <td><input v-model="item.name" class="input"/></td>
          <td><input v-model.number="item.qty" class="input"/></td>
          <td><input v-model="item.unit" class="input"/></td>
          <td><input v-model.number="item.factor" class="input"/></td>
          <td>{{ item.qty * item.factor }}</td>
        </tr>
      </tbody>
    </table>

    <button class="btn" @click="saveProductionForm">Save Production Form</button>
  </div>
</template>

<script setup>
import { ref } from "vue";

const prodNumber = ref(""); 
const division = ref(""); 
const date = ref(""); 
const stationId = ref(""); 
const userId = ref(""); 

const items = ref([
  { barcode:"", code:"", name:"", qty:0, unit:"", factor:1 }
]);

const saveProductionForm = () => alert("Production Form Saved!");
</script>

<style scoped>
.input { border:1px solid #ccc; padding:4px; width:100%; margin-bottom:4px; }
.btn { background:#007bff; color:white; padding:6px 12px; cursor:pointer; }
.btn:hover { background:#0056b3; }
</style>
