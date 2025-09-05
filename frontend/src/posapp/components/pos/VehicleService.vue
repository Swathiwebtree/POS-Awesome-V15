<template>
  <v-container class="pa-2">
    <div class="d-flex align-center mb-2">
      <v-btn variant="text" @click="$emit('back')">← Back</v-btn>
      <h2 class="text-h6 ml-4">Vehicle Service</h2>
      <v-spacer />
      <v-text-field
        v-model="barcode"
        label="Barcode"
        density="compact"
        style="max-width: 260px"
        @keydown.enter="onBarcodeEnter"
      />
      <v-btn class="ml-2" @click="openListings">Listings</v-btn>
      <v-btn class="ml-2" @click="openCoupon">Coupon Validate</v-btn>
    </div>

    <v-row>
      <!-- Left: categories + sizes -->
      <v-col cols="12" md="3">
        <v-card class="mb-3">
          <v-card-title>Car Care (Categories)</v-card-title>
          <v-card-text>
            <v-text-field v-model="search" label="Search items" density="compact" />
            <div class="mt-3">
              <v-chip-group v-model="size" column>
                <v-chip value="Small">Small</v-chip>
                <v-chip value="Medium">Medium</v-chip>
                <v-chip value="Large">Large</v-chip>
              </v-chip-group>
            </div>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title>Quick Actions</v-card-title>
          <v-card-text>
            <v-btn block class="mb-2" @click="sell">Sell</v-btn>
            <v-btn block class="mb-2" @click="openChangePrice" :disabled="!selectedRow">Change Price</v-btn>
            <v-btn block class="mb-2" color="error" @click="voidLine" :disabled="!selectedRow">Void Line</v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Center: items grid -->
      <v-col cols="12" md="5">
        <v-card>
          <v-card-title>Products & Services</v-card-title>
          <v-data-table
            :headers="itemHeaders"
            :items="filteredItems"
            item-key="item_code"
            density="compact"
            @click:row="addItemFromRow"
            class="cursor-pointer"
            height="520"
            fixed-header
          >
            <template #item.price_options="{ item }">
              <div class="d-flex flex-wrap" style="gap:4px">
                <v-chip
                  v-for="p in item.price_options || []"
                  :key="p.label + p.rate"
                  size="small"
                  @click.stop="addItemWithPrice(item, p)"
                >
                  {{ p.label }} {{ currency(p.rate) }}
                </v-chip>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <!-- Right: bill -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Work Order</v-card-title>
          <v-card-text>
            <v-text-field v-model="workOrderNo" label="Work Order #" density="compact" readonly />
            <v-text-field v-model="vehicleNo" label="Vehicle #" density="compact" />

            <v-data-table
              :headers="billHeaders"
              :items="bill"
              item-key="row_id"
              density="compact"
              height="360"
              fixed-header
              :items-per-page="-1"
              @click:row="selectRow"
            >
              <template #item.qty="{ item }">
                <v-text-field
                  v-model.number="item.qty"
                  type="number"
                  min="1"
                  density="compact"
                  @change="recalc"
                />
              </template>
              <template #item.rate="{ item }">
                <div class="d-flex align-center">
                  <span class="mr-2">{{ currency(item.rate) }}</span>
                  <v-btn icon variant="text" density="comfortable" @click.stop="openChangePriceFromRow(item)">
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                </div>
              </template>
              <template #item.amount="{ item }">
                {{ currency(item.qty * item.rate) }}
              </template>
            </v-data-table>

            <div class="mt-3">
              <div class="d-flex justify-space-between"><span>Sales Amount</span><b>{{ currency(totals.sales) }}</b></div>
              <div class="d-flex justify-space-between"><span>VAT</span><b>{{ currency(totals.vat) }}</b></div>
              <div class="d-flex justify-space-between"><span>Discount</span><b>- {{ currency(totals.discount) }}</b></div>
              <v-divider class="my-2" />
              <div class="d-flex justify-space-between text-h6"><span>Net Total</span><b>{{ currency(totals.net) }}</b></div>
            </div>

            <div class="mt-4 d-flex" style="gap:8px">
              <v-btn color="primary" @click="settle">Settle</v-btn>
              <v-btn variant="outlined" @click="hold">Hold</v-btn>
              <v-btn variant="outlined" @click="unhold">Unhold</v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Change Price Dialog -->
    <v-dialog v-model="dialogs.changePrice" width="420">
      <v-card>
        <v-card-title>Change Price</v-card-title>
        <v-card-text>
          <div v-if="rowForPrice">
            <div class="mb-2">Item: <b>{{ rowForPrice.item_name }}</b></div>
            <v-text-field v-model.number="newPrice" type="number" label="New Price" />
            <div class="text-caption">Only valid selling prices are accepted.</div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialogs.changePrice=false">Cancel</v-btn>
          <v-btn color="primary" @click="confirmChangePrice">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Listings Sheet -->
    <ListingsSheet v-model="dialogs.listings" />

    <!-- Coupon Validate -->
    <CouponDialog v-model="dialogs.coupon" />
  </v-container>
</template>

<script>
import api from "@/utils/apiclient";
import ListingsSheet from "./ListingsSheet.vue";
import CouponDialog from "./dialogs/CouponDialog.vue";

let rid = 1;

export default {
  name: "VehicleService",
  components: { ListingsSheet, CouponDialog },
  data() {
    return {
      barcode: "",
      search: "",
      size: "Medium",
      items: [],
      itemHeaders: [
        { title: "Barcode", key: "barcode", width: 120 },
        { title: "Code", key: "item_code", width: 120 },
        { title: "Name", key: "item_name" },
        { title: "Price(s)", key: "price_options", width: 220 },
        { title: "In Hand", key: "in_hand", width: 90 },
        { title: "Unit", key: "stock_uom", width: 80 },
      ],
      billHeaders: [
        { title: "Qty", key: "qty", width: 72 },
        { title: "Description", key: "item_name" },
        { title: "Rate", key: "rate", width: 120 },
        { title: "VAT", key: "vat_rate", width: 80 },
        { title: "Amount", key: "amount", width: 120 },
      ],
      bill: [],
      selectedRow: null,
      workOrderNo: "AUTO",
      vehicleNo: "",
      dialogs: {
        changePrice: false,
        listings: false,
        coupon: false,
      },
      rowForPrice: null,
      newPrice: null,
      totals: { sales: 0, vat: 0, discount: 0, net: 0 },
    };
  },
  computed: {
    filteredItems() {
      const q = (this.search || "").toLowerCase();
      return this.items.filter(
        (i) =>
          i.item_code.toLowerCase().includes(q) ||
          (i.item_name || "").toLowerCase().includes(q) ||
          (i.barcode || "").toLowerCase().includes(q)
      );
    },
  },
  created() {
    this.loadItems();
  },
  methods: {
    async loadItems() {
      const { data } = await api.get("/posawesome.api.lazer_pos.get_items");
      // Expecting: [{ item_code, item_name, barcode, stock_uom, in_hand, price_options:[{label:'Small',rate:100},{...}] , vat_rate }]
      this.items = data.message || data; // supports frappe or axios direct
    },
    addItemWithPrice(item, p) {
      this.bill.push({
        row_id: rid++,
        item_code: item.item_code,
        item_name: `${item.item_name} - ${p.label}`,
        qty: 1,
        rate: p.rate,
        vat_rate: item.vat_rate || 0,
      });
      this.recalc();
    },
    addItemFromRow(_, row) {
      // choose by current size (Small/Medium/Large) if available, else first price
      const item = row.item;
      const match = (item.price_options || []).find((x) => x.label === this.size) || (item.price_options || [])[0];
      if (!match) return;
      this.addItemWithPrice(item, match);
    },
    selectRow(_, row) {
      this.selectedRow = row.item;
    },
    currency(v) {
      if (v == null || isNaN(v)) return "₹0.00";
      return new Intl.NumberFormat(undefined, { style: "currency", currency: "INR" }).format(v);
    },
    recalc() {
      const sales = this.bill.reduce((s, r) => s + r.qty * r.rate, 0);
      const vat = this.bill.reduce((s, r) => s + r.qty * r.rate * (r.vat_rate / 100), 0);
      const discount = 0; // plug your discount logic later
      const net = sales + vat - discount;
      this.totals = { sales, vat, discount, net };
    },
    voidLine() {
      if (!this.selectedRow) return;
      this.bill = this.bill.filter((r) => r.row_id !== this.selectedRow.row_id);
      this.selectedRow = null;
      this.recalc();
    },
    openChangePrice() {
      if (!this.selectedRow) return;
      this.openChangePriceFromRow(this.selectedRow);
    },
    openChangePriceFromRow(row) {
      this.rowForPrice = row;
      this.newPrice = row.rate;
      this.dialogs.changePrice = true;
    },
    async confirmChangePrice() {
      if (!this.rowForPrice) return;
      // Backend validation: price must match an allowed Item Price
      const { data } = await api.post("/posawesome.api.lazer_pos.validate_selling_price", {
        item_code: this.rowForPrice.item_code,
        price: this.newPrice,
      });
      const ok = data.message?.ok ?? data.ok;
      if (!ok) {
        alert(data.message?.error || "This is not selling price");
        return;
      }
      this.rowForPrice.rate = Number(this.newPrice);
      this.dialogs.changePrice = false;
      this.recalc();
    },
    openListings() {
      this.dialogs.listings = true;
    },
    openCoupon() {
      this.dialogs.coupon = true;
    },
    async onBarcodeEnter() {
      if (!this.barcode) return;
      const { data } = await api.get("/posawesome.api.lazer_pos.get_item_by_barcode", {
        params: { barcode: this.barcode },
      });
      const item = data.message || data;
      if (!item || !item.item_code) {
        alert("Item not found");
        this.barcode = "";
        return;
      }
      // Use Medium by default or first price
      const p = (item.price_options || []).find((x) => x.label === this.size) || (item.price_options || [])[0];
      if (!p) {
        alert("No price configured for this item");
        this.barcode = "";
        return;
      }
      this.addItemWithPrice(item, p);
      this.barcode = "";
    },
    sell() {
      const billNo = prompt("Enter Bill No.");
      if (!billNo) return;
      alert("Sell submitted (stub). Hook to create Sales Invoice with bill no: " + billNo);
      // Later: POST to /create_sell
    },
    settle() {
      alert("Open settlement popup here (stub).");
    },
    hold() {
      alert("Transaction held (stub).");
    },
    unhold() {
      alert("Transaction resumed (stub).");
    },
  },
};
</script>

<style scoped>
.cursor-pointer tbody tr { cursor: pointer; }
</style>
