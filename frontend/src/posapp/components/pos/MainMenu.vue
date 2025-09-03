<template>
  <v-container class="pa-4">
    <!-- Top-right fixed button -->
    <v-btn
      color="primary"
      class="back-to-desk-btn"
      @click="goToDesk"
    >
      Back to Desk
    </v-btn>

    <h2 class="text-h5 text-center mb-6">Main Screen Modules</h2>
    <v-row dense>
      <v-col v-for="tile in tiles" :key="tile.key" cols="12" sm="6" md="3">
        <v-card
          :class="['pa-4 hover-elevate', tile.key==='exit' ? 'exit-tile' : '']"
          @click="open(tile)"
        >
          <v-icon v-if="tile.key==='exit'" start>mdi-exit-to-app</v-icon>
          <div class="text-h6 mb-2">{{ tile.title }}</div>
          <div class="text-caption">{{ tile.desc }}</div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>


<script>
export default {
  name: "MainMenu",
  emits: ["open-transactions", "open-module"],
  data() {
    return {
      tiles: [
        { key: "transactions", title: "Transactions", desc: "Sales & related" },
        { key: "inventory", title: "Inventory", desc: "Stock & items" },
        { key: "reports", title: "Reports", desc: "Sales & analytics" },
        { key: "system", title: "System", desc: "Settings & tools" },
        { key: "cash_counting", title: "Cash Counting", desc: "Count drawer" },
        { key: "cashier_out", title: "Cashier Out", desc: "Sign-out workflow" },
        { key: "day_end", title: "Day End Closing", desc: "Close the day" },
        { key: "exit", title: "Exit", desc: "Back to Desk" },
      ],
    };
  },
  methods: {
    open(tile) {
      if (tile.key === "transactions") {
        this.$emit("open-transactions");
      } else if (tile.key === "exit") {
        this.goToDesk();
      } else {
        this.$emit("open-module", tile.key);
      }
    },
    goToDesk() {
      window.location.href = "/app";
    },
  },
};
</script>

<style scoped>
.hover-elevate {
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}
.hover-elevate:hover {
  box-shadow: var(--v-shadow-6);
}

/* Highlight the Exit tile */
.exit-tile {
  background-color: #f5f5f5;
  color: #1976d2;
  font-weight: bold;
}

/* Top-right fixed button */
.back-to-desk-btn {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
}
</style>

