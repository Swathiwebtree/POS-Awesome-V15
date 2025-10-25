<template>
  <div class="p-6">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Vehicle Master</h2>

    <!-- Top Controls -->
    <div class="flex justify-between mb-6">
      <div class="grid grid-cols-4 gap-3 w-full max-w-4xl">
        <input v-model="filters.startDate" type="date" class="input" placeholder="Start Date" />
        <input v-model="filters.endDate" type="date" class="input" placeholder="End Date" />
        <input v-model="filters.vehicle_no" class="input" placeholder="Vehicle No." />
        <input v-model="filters.customer" class="input" placeholder="Customer" />
      </div>
      <div class="flex gap-3">
        <button @click="fetchVehicles" class="btn">Fetch</button>
        <button @click="showNewVehicle = true" class="btn bg-green-600 hover:bg-green-700">New Vehicle</button>
      </div>
    </div>

    <!-- Vehicles Table -->
    <div v-if="vehicles.length" class="overflow-x-auto mb-8 border rounded-lg shadow-sm">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th>Trans #</th>
            <th>Vehicle No.</th>
            <th>Customer</th>
            <th>Model</th>
            <th>Chasis No</th>
            <th>Color</th>
            <th>Reg No</th>
            <th>Odometer</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="vehicle in vehicles"
            :key="vehicle.name"
            @click="selectVehicle(vehicle)"
            class="hover:bg-gray-50 cursor-pointer"
          >
            <td>{{ vehicle.trans_number }}</td>
            <td>{{ vehicle.vehicle_no }}</td>
            <td>{{ vehicle.customer }}</td>
            <td>{{ vehicle.model }}</td>
            <td>{{ vehicle.chasis_no }}</td>
            <td>{{ vehicle.color }}</td>
            <td>{{ vehicle.reg_no }}</td>
            <td>{{ vehicle.odometer }}</td>
            <td>{{ formatDate(vehicle.date) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="text-gray-500 text-sm italic">No Vehicles found.</p>

    <!-- Selected Vehicle Details -->
    <div v-if="selectedVehicle" class="mt-8 border p-4 rounded-lg shadow-sm">
      <h3 class="text-lg font-semibold mb-3 text-gray-700">
        Vehicle Details — {{ selectedVehicle.vehicle_no }}
      </h3>

      <div class="grid grid-cols-3 gap-2 mb-4 text-sm text-gray-700">
        <p><b>Trans #:</b> {{ selectedVehicle.trans_number }}</p>
        <p><b>Vehicle No:</b> {{ selectedVehicle.vehicle_no }}</p>
        <p><b>Customer:</b> {{ selectedVehicle.customer }}</p>
        <p><b>Model:</b> {{ selectedVehicle.model }}</p>
        <p><b>Chasis No:</b> {{ selectedVehicle.chasis_no }}</p>
        <p><b>Color:</b> {{ selectedVehicle.color }}</p>
        <p><b>Reg No:</b> {{ selectedVehicle.reg_no }}</p>
        <p><b>Warranty:</b> {{ selectedVehicle.warranty ? "Yes" : "No" }}</p>
        <p><b>Odometer:</b> {{ selectedVehicle.odometer }}</p>
        <p><b>Engine:</b> {{ selectedVehicle.engine }}</p>
        <p><b>Body:</b> {{ selectedVehicle.body }}</p>
        <p><b>Year:</b> {{ selectedVehicle.year }}</p>
        <p><b>Division:</b> {{ selectedVehicle.division }}</p>
        <p><b>Address:</b> {{ selectedVehicle.address }}</p>
        <p><b>City:</b> {{ selectedVehicle.city }}</p>
        <p><b>TIN:</b> {{ selectedVehicle.tin }}</p>
        <p><b>Tel (Mob):</b> {{ selectedVehicle.tel_mobile }}</p>
        <p><b>Office:</b> {{ selectedVehicle.office_tel }}</p>
        <p><b>Home:</b> {{ selectedVehicle.home_tel }}</p>
        <p><b>Bill To:</b> {{ selectedVehicle.bill_to }}</p>
        <p><b>Stationed:</b> {{ selectedVehicle.stationed }}</p>
        <p><b>Location:</b> {{ selectedVehicle.location }}</p>
        <p><b>Sales Rep:</b> {{ selectedVehicle.sales_rep }}</p>
        <p><b>Comments:</b> {{ selectedVehicle.comments }}</p>
      </div>
    </div>

    <!-- New Vehicle Modal -->
    <div
      v-if="showNewVehicle"
      class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
    >
      <div class="bg-white p-6 rounded-lg w-2/3 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">New Vehicle</h3>
        <div class="grid grid-cols-3 gap-3">
          <input v-model="newVehicle.trans_number" class="input" placeholder="Trans #" />
          <input v-model="newVehicle.vehicle_no" class="input" placeholder="Vehicle No." />
          <input v-model="newVehicle.customer" class="input" placeholder="Customer" />
          <input v-model="newVehicle.model" class="input" placeholder="Model" />
          <input v-model="newVehicle.chasis_no" class="input" placeholder="Chasis No" />
          <input v-model="newVehicle.color" class="input" placeholder="Color" />
          <input v-model="newVehicle.reg_no" class="input" placeholder="Reg No" />
          <input v-model="newVehicle.odometer" class="input" placeholder="Odometer" />
          <input v-model="newVehicle.engine" class="input" placeholder="Engine" />
          <input v-model="newVehicle.body" class="input" placeholder="Body" />
          <input v-model="newVehicle.year" class="input" placeholder="Year" />
          <input v-model="newVehicle.division" class="input" placeholder="Division" />
          <input v-model="newVehicle.address" class="input" placeholder="Address" />
          <input v-model="newVehicle.city" class="input" placeholder="City" />
          <input v-model="newVehicle.tin" class="input" placeholder="TIN" />
          <input v-model="newVehicle.tel_mobile" class="input" placeholder="Tel (Mob)" />
          <input v-model="newVehicle.office_tel" class="input" placeholder="Office" />
          <input v-model="newVehicle.home_tel" class="input" placeholder="Home" />
          <input v-model="newVehicle.bill_to" class="input" placeholder="Bill To" />
          <input v-model="newVehicle.stationed" class="input" placeholder="Stationed" />
          <input v-model="newVehicle.location" class="input" placeholder="Location" />
          <input v-model="newVehicle.sales_rep" class="input" placeholder="Sales Rep" />
          <input v-model="newVehicle.comments" class="input" placeholder="Comments" />
        </div>

        <div class="flex justify-end gap-3 mt-4">
          <button @click="showNewVehicle = false" class="btn bg-gray-400 hover:bg-gray-500">Cancel</button>
          <button @click="createVehicle" class="btn bg-green-600 hover:bg-green-700">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const filters = ref({
  startDate: "",
  endDate: "",
  vehicle_no: "",
  customer: "",
});

const vehicles = ref([]);
const selectedVehicle = ref(null);
const showNewVehicle = ref(false);

const newVehicle = ref({
  trans_number: "",
  vehicle_no: "",
  customer: "",
  model: "",
  chasis_no: "",
  color: "",
  reg_no: "",
  odometer: "",
  engine: "",
  body: "",
  year: "",
  division: "",
  address: "",
  city: "",
  tin: "",
  tel_mobile: "",
  office_tel: "",
  home_tel: "",
  bill_to: "",
  stationed: "",
  location: "",
  sales_rep: "",
  comments: "",
});

// Axios setup
axios.defaults.withCredentials = true;
axios.interceptors.request.use((config) => {
  const csrfToken = frappe.csrf_token;
  if (csrfToken) config.headers["X-Frappe-CSRF-Token"] = csrfToken;
  return config;
});

// Fetch Vehicles
const fetchVehicles = async () => {
  try {
    const filtersObj = {};
    if (filters.value.vehicle_no) filtersObj.vehicle_no = ["like", `%${filters.value.vehicle_no}%`];
    if (filters.value.customer) filtersObj.customer = ["like", `%${filters.value.customer}%`];
    if (filters.value.startDate && filters.value.endDate) {
      filtersObj.date = ["between", [filters.value.startDate, filters.value.endDate]];
    }

    const res = await axios.get("/api/resource/Vehicle Master", {
      params: {
        fields: JSON.stringify([
          "name","trans_number","vehicle_no","customer","model","chasis_no","color",
          "reg_no","warranty","odometer","engine","body","year","division","address",
          "city","tin","tel_mobile","office_tel","home_tel","bill_to","stationed","location","sales_rep","comments","date"
        ]),
        filters: JSON.stringify(filtersObj),
        limit_page_length: 50,
        order_by: "modified desc",
      },
    });

    vehicles.value = res.data.data || [];
    selectedVehicle.value = null;
  } catch (err) {
    console.error("Error fetching vehicles:", err);
  }
};

// Select Vehicle
const selectVehicle = async (vehicle) => {
  try {
    const res = await axios.get(`/api/resource/Vehicle Master/${vehicle.name}`);
    selectedVehicle.value = res.data.data;
  } catch (err) {
    console.error("Error fetching vehicle details:", err);
  }
};

// Create Vehicle
const createVehicle = async () => {
  try {
    const res = await axios.post("/api/resource/Vehicle Master", newVehicle.value);
    alert("Vehicle created successfully!");
    showNewVehicle.value = false;
    Object.keys(newVehicle.value).forEach(k => newVehicle.value[k] = "");
    fetchVehicles();
  } catch (err) {
    console.error("Error creating vehicle:", err);
    alert("Failed to create vehicle.");
  }
};

// Format Date
const formatDate = (date) => date ? new Date(date).toLocaleDateString() : "";
</script>

<style scoped>
.input {
  border: 1px solid #ccc;
  padding: 6px 8px;
  width: 100%;
  border-radius: 4px;
}
.btn {
  background-color: #007bff;
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}
.btn:hover {
  background-color: #0056b3;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}
th {
  font-weight: 600;
}
</style>
