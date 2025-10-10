<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Physical Count</h2>

    <!-- Main Fields -->
    <div class="grid grid-cols-4 gap-2 mb-4">
      <input v-model="phyNumber" placeholder="Phy #" class="input"/>
      <input type="date" v-model="date" class="input"/>
      <input v-model="shiftClosingId" placeholder="Shift Closing ID" class="input"/>
      <input v-model="stationId" placeholder="Station ID" class="input"/>
      <input v-model="location" placeholder="Location" class="input"/>
      <input v-model="reference" placeholder="Reference (Ref)" class="input"/>
      <input v-model="dayClosingId" placeholder="Day Closing ID" class="input"/>
      <input v-model="userId" placeholder="User ID" class="input"/>
    </div>

    <!-- Inventory Items Table -->
    <table class="table-auto border w-full mb-4">
      <thead>
        <tr>
          <th>Barcode</th>
          <th>Item Code</th>
          <th>Item Name</th>
          <th>Unit</th>
          <th>Factor</th>
          <th>Qty</th>
          <th>Net Qty</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in items" :key="index">
          <td><input v-model="item.barcode" class="input"/></td>
          <td><input v-model="item.code" class="input"/></td>
          <td><input v-model="item.name" class="input"/></td>
          <td><input v-model="item.unit" class="input"/></td>
          <td><input v-model.number="item.factor" class="input"/></td>
          <td><input v-model.number="item.qty" class="input"/></td>
          <td>{{ (item.qty * item.factor).toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>

    <button class="btn" @click="savePhysicalCount">Save Physical Count</button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const phyNumber = ref("");
const date = ref("");
const shiftClosingId = ref("");
const stationId = ref("");
const location = ref("");
const reference = ref("");
const dayClosingId = ref("");
const userId = ref("");

const items = ref([
  { barcode: "", code: "", name: "", unit: "", factor: 1, qty: 0 }
]);

// Save function to post the physical count
const savePhysicalCount = async () => {
  try {
    const payload = {
      phyNumber: phyNumber.value,
      date: date.value,
      shiftClosingId: shiftClosingId.value,
      stationId: stationId.value,
      location: location.value,
      reference: reference.value,
      dayClosingId: dayClosingId.value,
      userId: userId.value,
      items: items.value
    };

    // Replace the URL with your actual Frappe endpoint
    await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.get_physical_count_list", payload);

    alert("Physical Count saved successfully!");
  } catch (error) {
    console.error(error);
    alert("Error saving Physical Count");
  }
};
</script>

<style scoped>
.input {
  border: 1px solid #ccc;
  padding: 4px;
  width: 100%;
  margin-bottom: 4px;
}
.btn {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  cursor: pointer;
}
.btn:hover {
  background: #0056b3;
}
</style>
