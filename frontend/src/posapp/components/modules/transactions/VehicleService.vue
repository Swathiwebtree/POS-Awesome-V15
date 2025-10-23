<template>
  <div class="vehicle-service-pos-container">
    <!-- Work Order & Vehicle Info -->
    <v-row dense class="mb-3">
      <v-col cols="12" md="3">
        <v-text-field
          label="Work Order #"
          v-model="workOrder"
          @blur="fetchWorkOrderDetails"
        />
        <v-text-field label="Vehicle #" v-model="vehicle" readonly />
        <v-text-field label="Customer" v-model="customer" readonly />
      </v-col>

      <v-col cols="12" md="3">
        <v-text-field label="Staff Code" v-model="staffCode" />
        <v-text-field label="Staff Name" v-model="staffName" />
        <v-text-field label="Points" v-model="points" readonly />
      </v-col>

      <v-col cols="12" md="6" class="d-flex align-center justify-end flex-wrap">
        <v-btn color="primary" @click="browseItems">Browse Items</v-btn>
        <v-btn color="success" class="ml-2" @click="saveWorkOrder">Save</v-btn>
        <v-btn color="error" class="ml-2" @click="voidWorkOrder">Void Bill</v-btn>
        <v-btn color="info" class="ml-2" @click="openPaymentModal">Settle</v-btn>
        <v-btn color="secondary" class="ml-2" @click="openCouponDialog">Coupon</v-btn>
        <v-btn color="warning" class="ml-2" @click="applyDiscount">Discount</v-btn>
        <v-btn color="pink" class="ml-2" @click="toggleHold">{{ isHold ? "Unhold" : "Hold" }}</v-btn>
        <v-btn color="dark" class="ml-2" @click="reprintInvoice">Reprint</v-btn>
      </v-col>
    </v-row>

    <!-- Item Selection & Order Summary -->
    <v-row dense>
      <v-col cols="12" md="5">
        <!-- Service/Product Categories -->
        <v-btn
          v-for="cat in categories"
          :key="cat"
          class="mr-2 mb-2"
          outlined
          @click="browseCategory(cat)"
        >
          {{ cat }}
        </v-btn>

        <v-text-field
          label="Scan Barcode"
          v-model="barcode"
          @keyup.enter="onBarcodeScan(barcode)"
        />

        <!-- Selected Items -->
        <v-data-table :items="orderItems" :headers="itemHeaders" item-key="item_code" dense>
          <template #item.qty="{ item }">
            <v-text-field v-model="item.qty" type="number" min="1" @change="updateQty(item)" />
          </template>
          <template #item.actions="{ index }">
            <v-btn icon color="red" @click="voidLine(index)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-col>

      <v-col cols="12" md="7">
        <!-- Order Summary -->
        <div class="summary p-3">
          <p><strong>Discount:</strong> ₹ {{ workOrderDiscount }}</p>
          <p><strong>Net Total:</strong> ₹ {{ netTotal.toFixed(2) }}</p>
          <p><strong>Paid:</strong> ₹ {{ paidAmount.toFixed(2) }}</p>
          <p><strong>Change:</strong> ₹ {{ changeAmount.toFixed(2) }}</p>
        </div>
      </v-col>
    </v-row>

    <!-- Payment Modal -->
    <v-dialog v-model="showPaymentModal" max-width="600px">
      <v-card>
        <v-card-title>Settle Payment</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" v-for="method in paymentMethods" :key="method.name">
              <v-btn block :color="method.color" @click="applyPayment(method.name)">
                {{ method.label }}
              </v-btn>
            </v-col>
          </v-row>

          <v-divider class="my-3"></v-divider>
          <div>
            <p>Total: ₹ {{ netTotal.toFixed(2) }}</p>
            <p>Paid: ₹ {{ paidAmount.toFixed(2) }}</p>
            <p>Balance: ₹ {{ balanceAmount.toFixed(2) }}</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn text color="grey" @click="resetPayment">Reset Payment</v-btn>
          <v-btn text color="grey" @click="resetAllPayments">Reset All</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="success" @click="completePayment">Done</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Coupon & Loyalty Dialogs -->
    <LoyaltyCouponDialog
      :open="showLoyaltyCoupon"
      :staffCode="staffCode"
      :staffName="staffName"
      :points="points"
      @applyCoupon="applyCouponCode"
      @update:open="showLoyaltyCoupon = $event"
    />
    <LoyaltyCardDialog v-model:visible="showLoyaltyDialog" @applyLoyalty="applyLoyaltyCustomer" />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import LoyaltyCouponDialog from "./LoyaltyCouponDialog.vue";
import LoyaltyCardDialog from "./LoyaltyCardDialog.vue";
import axios from "axios";

// Reactive State
const workOrder = ref("");
const vehicle = ref("");
const customer = ref("");
const staffCode = ref("");
const staffName = ref("");
const points = ref(0);
const orderItems = ref([]);
const categories = ref(["Body Wash", "Engine Oil", "Extra Services"]);
const barcode = ref("");
const workOrderDiscount = ref(0);
const paidAmount = ref(0);
const showPaymentModal = ref(false);
const showLoyaltyCoupon = ref(false);
const showLoyaltyDialog = ref(false);
const isHold = ref(false);

const paymentMethods = ref([
  { name: "cash", label: "Cash", color: "green" },
  { name: "credit", label: "Credit Card", color: "blue" },
  { name: "on_account", label: "On Account", color: "orange" },
  { name: "cheque", label: "Cheque", color: "grey" },
  { name: "gift_voucher", label: "Gift Voucher", color: "pink" },
  { name: "loyalty", label: "Loyalty", color: "purple" },
  { name: "mobile_pay", label: "Mobile Easy Pay", color: "cyan" },
]);

const itemHeaders = ref([
  { text: "Item Code", value: "item_code" },
  { text: "Quantity", value: "qty" },
  { text: "Actions", value: "actions", sortable: false },
]);

// Computed totals
const netTotal = computed(() => orderItems.value.reduce((sum, i) => sum + (i.qty || 0) * (i.price || 0), 0) - workOrderDiscount.value);
const changeAmount = computed(() => paidAmount.value - netTotal.value);
const balanceAmount = computed(() => netTotal.value - paidAmount.value);

// Fetch Work Order Details
async function fetchWorkOrderDetails() {
  if (!workOrder.value) return;
  try {
    const res = await axios.get(`/api/method/frappe.client.get?doctype=Vehicle Service Work Order&name=${workOrder.value}`);
    if (res.data.message) {
      const data = res.data.message;
      vehicle.value = data.vehicle || "";
      customer.value = data.customer || "";
      orderItems.value = (data.items || []).map(i => ({ ...i, qty: i.qty || 1 }));
      workOrderDiscount.value = data.discount || 0;
    }
  } catch (err) {
    console.error(err);
    alert("Work Order not found!");
  }
}

// Browse Items
async function browseItems() {
  try {
    const res = await axios.get("/api/method/posawesome.posawesome.api.items.get_items");
    if (res.data.message) orderItems.value = res.data.message.map(i => ({ ...i, qty: 1 }));
  } catch (err) { console.error(err); }
}

function browseCategory(category) {
  orderItems.value = orderItems.value.filter(i => i.category === category);
}

// Barcode scan
async function onBarcodeScan(code) {
  if (!code) return;
  try {
    const res = await axios.get(`/api/method/posawesome.posawesome.api.lazer_pos.get_items_from_barcode?barcode=${code}`);
    const item = res.data.message?.[0];
    if (item) {
      const existing = orderItems.value.find(i => i.item_code === item.item_code);
      if (existing) existing.qty += 1;
      else orderItems.value.push({ ...item, qty: 1 });
    } else alert("Item not found!");
    barcode.value = "";
  } catch (err) { console.error(err); }
}

function updateQty(item) { if (item.qty <= 0) item.qty = 1; }

// Save Work Order
async function saveWorkOrder() {
  if (!workOrder.value || !vehicle.value || !customer.value) return alert("Fill Work Order, Vehicle & Customer!");
  try {
    await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.save_work_order", {
      work_order: workOrder.value,
      vehicle: vehicle.value,
      customer: customer.value,
      staff_code: staffCode.value,
      staff_name: staffName.value,
      items: orderItems.value.filter(i => i.qty > 0),
      discount: workOrderDiscount.value,
    });
    alert("Work Order saved successfully!");
  } catch (err) { console.error(err); alert("Error saving Work Order"); }
}

// Void Line Item
function voidLine(index) { orderItems.value.splice(index, 1); }

// Void Work Order
async function voidWorkOrder() {
  if (!workOrder.value) return;
  try {
    await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.void_order", { order_no: workOrder.value });
    resetOrder();
    alert("Work Order voided!");
  } catch (err) { console.error(err); }
}

// Hold / Unhold
function toggleHold() { isHold.value = !isHold.value; }

// Payment Modal
function openPaymentModal() { if (!orderItems.value.length) return alert("No items to settle!"); showPaymentModal.value = true; }
function applyPayment(method) { paidAmount.value = netTotal.value; alert(`${method} payment applied for ₹${paidAmount.value}`); }
function resetPayment() { paidAmount.value = 0; }
function resetAllPayments() { resetOrder(); showPaymentModal.value = false; }
function completePayment() { if (paidAmount.value < netTotal.value) return alert("Payment incomplete!"); showPaymentModal.value = false; resetOrder(); }

// Coupon / Loyalty
function openCouponDialog() { showLoyaltyCoupon.value = true; }
async function applyCouponCode(code) { alert("Coupon applied: " + code); showLoyaltyCoupon.value = false; }
function applyLoyaltyCustomer(customerObj) { customer.value = customerObj.customer_name; points.value = customerObj.points; }

// Discount
function applyDiscount() {
  const discount = prompt("Enter discount amount:");
  if (discount) workOrderDiscount.value = parseFloat(discount);
}

// Reprint
function reprintInvoice() { alert("Invoice reprinted for " + workOrder.value); }

// Reset Order
function resetOrder() {
  workOrder.value = "";
  vehicle.value = "";
  customer.value = "";
  orderItems.value = [];
  workOrderDiscount.value = 0;
  paidAmount.value = 0;
  isHold.value = false;
}
</script>

<style scoped>
.vehicle-service-pos-container { padding: 16px; height: 100%; overflow-y: auto; }
.summary { border: 1px solid #ccc; border-radius: 6px; padding: 16px; margin-top: 16px; }
</style>
