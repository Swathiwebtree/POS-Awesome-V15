<template>
  <div class="vehicles-master">
    <div class="header">
      <h3>Vehicles Master</h3>
      <button @click="newVehicle" class="btn-new">+ New Vehicle</button>
    </div>

    <!-- Vehicles Table -->
    <table>
      <thead>
        <tr>
          <th>Trans #</th>
          <th>Vehicle No</th>
          <th>Customer</th>
          <th>Model</th>
          <th>Chasis No</th>
          <th>Color</th>
          <th>Reg No</th>
          <th>Warranty</th>
          <th>Odometer</th>
          <th>Year</th>
          <th>Division</th>
          <th>TIN</th>
          <th>Mobile</th>
          <th>Address</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(veh, index) in vehicles" :key="veh.name">
          <td>{{ index + 1 }}</td>
          <td>{{ veh.vehicle_no }}</td>
          <td>{{ veh.customer }}</td>
          <td>{{ veh.model }}</td>
          <td>{{ veh.chasis_no }}</td>
          <td>{{ veh.color }}</td>
          <td>{{ veh.reg_no }}</td>
          <td>{{ veh.warranty }}</td>
          <td>{{ veh.odometer }}</td>
          <td>{{ veh.year }}</td>
          <td>{{ veh.division }}</td>
          <td>{{ veh.tin }}</td>
          <td>{{ veh.mobile_no }}</td>
          <td>{{ veh.address }}</td>
          <td>
            <button class="btn-view" @click="viewVehicle(veh.vehicle_no)">View</button>
          </td>
        </tr>

        <tr v-if="vehicles.length === 0">
          <td colspan="15" class="no-data">No vehicles found</td>
        </tr>
      </tbody>
    </table>

    <!-- Vehicle Details Modal -->
    <div v-if="selectedVehicle" class="vehicle-details">
      <div class="modal-content">
        <h4>Vehicle Details - {{ selectedVehicle.vehicle.vehicle_no }}</h4>

        <div class="details-grid">
          <div><b>Model:</b> {{ selectedVehicle.vehicle.model }}</div>
          <div><b>Color:</b> {{ selectedVehicle.vehicle.color }}</div>
          <div><b>Odometer:</b> {{ selectedVehicle.vehicle.odometer }}</div>
          <div><b>Warranty:</b> {{ selectedVehicle.vehicle.warranty }}</div>
          <div><b>Customer:</b> {{ selectedVehicle.customer.customer_name }}</div>
          <div><b>Mobile:</b> {{ selectedVehicle.customer.mobile_no }}</div>
          <div><b>Email:</b> {{ selectedVehicle.customer.email }}</div>
          <div><b>Address:</b> {{ selectedVehicle.customer.address }}</div>
        </div>

        <h5>Recent History</h5>
        <table class="history-table">
          <thead>
            <tr>
              <th>Bill No</th>
              <th>Date</th>
              <th>Item</th>
              <th>Amount</th>
              <th>Points</th>
              <th>Staff</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(h, i) in selectedVehicle.history" :key="i">
              <td>{{ h.bill_no }}</td>
              <td>{{ h.date }}</td>
              <td>{{ h.item_name }}</td>
              <td>{{ h.amount }}</td>
              <td>{{ h.points }}</td>
              <td>{{ h.staff_name }}</td>
            </tr>
          </tbody>
        </table>

        <button class="btn-close" @click="selectedVehicle = null">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const vehicles = ref([]);
const selectedVehicle = ref(null);

// Fetch vehicle list
async function fetchVehicles() {
  try {
    const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_vehicle_master')
    vehicles.value = res.data.message || []
  } catch (err) {
    console.error('Error fetching vehicles:', err)
  }
}

// Fetch vehicle details by vehicle_no
async function viewDetails(vehicle_no) {
  try {
    const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_vehicle_details', {
      params: { vehicle_no }
    })
    selectedVehicle.value = res.data.message
  } catch (err) {
    console.error('Error fetching vehicle details:', err)
  }
}

function newVehicle() {
  alert("Open new vehicle form");
}

onMounted(() => {
  fetchVehicles();
});
</script>

<style scoped>
.vehicles-master {
  padding: 20px;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.btn-new {
  background-color: #1976d2;
  color: white;
  border: none;
  padding: 8px 14px;
  cursor: pointer;
  border-radius: 4px;
}
.btn-new:hover {
  background-color: #125aa5;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}
th, td {
  border: 1px solid #ccc;
  padding: 8px;
  font-size: 14px;
}
th {
  background-color: #f5f5f5;
}
.no-data {
  text-align: center;
  font-style: italic;
  color: #777;
}

.btn-view {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 4px 10px;
  cursor: pointer;
  border-radius: 3px;
}
.btn-view:hover {
  background-color: #43a047;
}

/* Modal */
.vehicle-details {
  position: fixed;
  inset: 0;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: white;
  padding: 20px;
  width: 70%;
  border-radius: 8px;
  max-height: 90vh;
  overflow-y: auto;
}
.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
}
.history-table th, .history-table td {
  border: 1px solid #ddd;
  padding: 6px;
  font-size: 13px;
}
.btn-close {
  margin-top: 10px;
  background-color: #d32f2f;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-close:hover {
  background-color: #b71c1c;
}
</style>
