<template>
  <div class="vehicle-service-pos-container">
    <!-- Work Order & Vehicle Info -->
    <v-row dense class="mb-3">
      <v-col cols="12" md="3">
        <v-text-field label="Work Order #" v-model="workOrder" />
        <v-text-field label="Vehicle #" v-model="vehicle" />
        <v-text-field label="Customer" v-model="customer" />
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
        <v-data-table
          :items="orderItems"
          :headers="itemHeaders"
          item-key="item_code"
          dense
        >
          <template #item.qty="{ item }">
            <v-text-field
              v-model="item.qty"
              type="number"
              min="1"
              @change="updateQty(item)"
            />
          </template>
          <template #item.actions="{ item, index }">
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

    <!-- Coupon Dialog -->
    <LoyaltyCouponDialog
      :open="showLoyaltyCoupon"
      :staffCode="staffCode"
      :staffName="staffName"
      :points="points"
      @applyCoupon="applyCouponCode"
      @update:open="showLoyaltyCoupon = $event"
    />

    <!-- Loyalty Dialog -->
    <LoyaltyCardDialog v-model:visible="showLoyaltyDialog" @applyLoyalty="applyLoyaltyCustomer" />
  </div>
</template>

<script>
import LoyaltyCouponDialog from "./LoyaltyCouponDialog.vue";
import LoyaltyCardDialog from "./LoyaltyCardDialog.vue";

export default {
  name: "VehicleServicePOS",
  components: { LoyaltyCouponDialog, LoyaltyCardDialog },
  data() {
    return {
      workOrder: "",
      vehicle: "",
      customer: "",
      staffCode: "",
      staffName: "",
      points: 0,
      orderItems: [],
      categories: ["Body Wash", "Engine Oil", "Extra Services"],
      barcode: "",
      workOrderDiscount: 0,
      paidAmount: 0,
      showPaymentModal: false,
      showLoyaltyCoupon: false,
      showLoyaltyDialog: false,
      isHold: false,
      paymentMethods: [
        { name: "cash", label: "Cash", color: "green" },
        { name: "credit", label: "Credit Card", color: "blue" },
        { name: "on_account", label: "On Account", color: "orange" },
        { name: "cheque", label: "Cheque", color: "grey" },
        { name: "gift_voucher", label: "Gift Voucher", color: "pink" },
        { name: "loyalty", label: "Loyalty", color: "purple" },
        { name: "mobile_pay", label: "Mobile Easy Pay", color: "cyan" },
      ],
      itemHeaders: [
        { text: "Item Code", value: "item_code" },
        { text: "Quantity", value: "qty" },
        { text: "Actions", value: "actions", sortable: false },
      ],
    };
  },
  computed: {
    netTotal() {
      return this.orderItems.reduce((sum, i) => sum + (i.qty || 0) * (i.price || 0), 0) - this.workOrderDiscount;
    },
    changeAmount() {
      return this.paidAmount - this.netTotal;
    },
    balanceAmount() {
      return this.netTotal - this.paidAmount;
    },
  },
  methods: {
    async browseItems() {
      let allItems = [];
      for (let cat of this.categories) {
        const res = await fetch(`/api/method/posawesome.posawesome.api.lazer_pos.browse_items?category=${encodeURIComponent(cat)}`);
        const data = await res.json();
        if (data.message) allItems = allItems.concat(data.message);
      }
      this.orderItems = allItems;
    },
    browseCategory(category) {
      // Filter items by category
      this.orderItems = this.orderItems.filter(i => i.category === category);
    },
    async onBarcodeScan(barcode) {
      if (!barcode) return;
      const res = await fetch(`/api/method/posawesome.posawesome.api.lazer_pos.get_items_from_barcode?barcode=${barcode}`);
      const data = await res.json();
      if (data.message?.length > 0) {
        const item = data.message[0];
        const existing = this.orderItems.find(i => i.item_code === item.item_code);
        if (existing) existing.qty += 1;
        else this.orderItems.push({ ...item, qty: 1 });
      } else alert("Item not found for barcode: " + barcode);
      this.barcode = "";
    },
    updateQty(item) {
      if (item.qty <= 0) item.qty = 1;
    },
    async saveWorkOrder() {
      if (!this.workOrder || !this.vehicle || !this.customer) return alert("Fill Work Order, Vehicle & Customer!");
      try {
        await fetch("/api/method/posawesome.posawesome.api.lazer_pos.save_work_order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            work_order: this.workOrder,
            vehicle: this.vehicle,
            customer: this.customer,
            staff_code: this.staffCode,
            staff_name: this.staffName,
            items: this.orderItems,
            discount: this.workOrderDiscount,
          }),
        });
        alert("Work Order saved successfully!");
      } catch (err) {
        console.error(err);
        alert("Error saving Work Order");
      }
    },
    async voidWorkOrder() {
      if (!this.workOrder) return;
      try {
        await fetch("/api/method/posawesome.posawesome.api.lazer_pos.void_order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order_no: this.workOrder }),
        });
        this.resetOrder();
        alert("Work Order voided!");
      } catch (err) {
        console.error(err);
      }
    },
    resetOrder() {
      this.workOrder = "";
      this.vehicle = "";
      this.customer = "";
      this.orderItems = [];
      this.workOrderDiscount = 0;
      this.paidAmount = 0;
      this.isHold = false;
    },
    toggleHold() {
      this.isHold = !this.isHold;
      fetch("/api/method/posawesome.posawesome.api.lazer_pos.hold_order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_no: this.workOrder }),
      }).catch(console.error);
    },
    voidLine(index) {
      this.orderItems.splice(index, 1);
    },
    openPaymentModal() {
      if (!this.orderItems.length) return alert("No items to settle!");
      this.showPaymentModal = true;
    },
    applyPayment(method) {
      if (method === "loyalty") {
        this.showLoyaltyDialog = true;
        return;
      }
      this.paidAmount = this.netTotal;
      fetch("/api/method/posawesome.posawesome.api.lazer_pos.settle_order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_no: this.workOrder, payment_info: [{ method, amount: this.paidAmount }] }),
      }).then(() => alert("Payment done")).catch(console.error);
    },
    resetPayment() {
      this.paidAmount = 0;
    },
    resetAllPayments() {
      this.resetOrder();
      this.showPaymentModal = false;
    },
    completePayment() {
      if (this.paidAmount < this.netTotal) return alert("Payment incomplete!");
      this.showPaymentModal = false;
      this.resetOrder();
    },
    openCouponDialog() {
      this.showLoyaltyCoupon = true;
    },
    async applyCouponCode(code) {
      try {
        await fetch("/api/method/posawesome.posawesome.api.lazer_pos.apply_coupon", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order_no: this.workOrder, coupon_code: code }),
        });
        alert("Coupon applied!");
        this.showLoyaltyCoupon = false;
      } catch (err) {
        console.error(err);
      }
    },
    applyDiscount() {
      const discount = prompt("Enter discount amount:");
      if (discount) this.workOrderDiscount = parseFloat(discount);
    },
    reprintInvoice() {
      fetch(`/api/method/posawesome.posawesome.api.lazer_pos.print_invoice?order_no=${this.workOrder}`)
        .then(res => res.json())
        .then(data => console.log("Invoice PDF:", data.message.pdf))
        .catch(console.error);
    },
    applyLoyaltyCustomer(customer) {
      this.customer = customer.customer_name;
      this.points = customer.points;
    },
  },
};
</script>

<style scoped>
.vehicle-service-pos-container {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}
.summary {
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 16px;
}
</style>
