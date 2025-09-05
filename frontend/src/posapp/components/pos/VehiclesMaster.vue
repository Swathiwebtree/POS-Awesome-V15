<template>
  <v-container class="pa-4">
    <div class="d-flex align-center mb-2">
      <v-btn variant="text" @click="$emit('back')">← Back</v-btn>
      <h2 class="text-h6 ml-4">Vehicles Master</h2>
      <v-spacer/>
      <v-text-field v-model="search" label="Search" density="compact" style="max-width:280px"/>
    </div>

    <v-data-table
      :headers="headers"
      :items="filtered"
      item-key="trans_no"
      density="compact"
      fixed-header
      height="75vh"
      :items-per-page="50"
    />
  </v-container>
</template>

<script>
import api from "@/utils/apiclient";

export default {
  name: "VehiclesMaster",
  data() {
    return {
      search: "",
      rows: [],
      headers: [
        { title: "Trans #", key: "trans_no", width: 120 },
        { title: "Vehicle No.", key: "vehicle_no", width: 160 },
        { title: "Customer", key: "customer" },
        { title: "Model", key: "model" },
        { title: "Chasis No", key: "chasis_no" },
        { title: "Color", key: "color" },
        { title: "Reg No", key: "reg_no" },
        { title: "Warranty", key: "warranty" },
        { title: "Odometer", key: "odometer" },
        { title: "Date", key: "date" },
        { title: "Engine", key: "engine" },
        { title: "Body", key: "body" },
        { title: "Year", key: "year" },
        { title: "Division", key: "division" },
        { title: "Address", key: "address" },
        { title: "PO Box", key: "po_box" },
        { title: "City", key: "city" },
        { title: "TIN", key: "tin" },
        { title: "Tel (Mob)", key: "tel_mob" },
        { title: "Office", key: "office" },
        { title: "Home", key: "home" },
        { title: "Bill To", key: "bill_to" },
        { title: "Stationed", key: "stationed" },
        { title: "Loc", key: "loc" },
        { title: "Sales Rep", key: "sales_rep" },
        { title: "Comments", key: "comments" },
        { title: "Created By", key: "created_by" },
        { title: "On", key: "on" },
        { title: "Modified", key: "modified" },
        { title: "Last Modified", key: "last_modified" },
      ],
    };
  },
  computed: {
    filtered() {
      const q = (this.search || "").toLowerCase();
      return this.rows.filter(r => Object.values(r).some(v => String(v ?? "").toLowerCase().includes(q)));
    },
  },
  async mounted() {
    const { data } = await api.get("/posawesome.api.lazer_pos.vehicles_master_list", { params: { limit: 500 } });
    this.rows = data.message || data || [];
  },
};
</script>
