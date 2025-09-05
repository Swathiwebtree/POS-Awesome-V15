<template>
  <div>
    <!-- Main menu wrapper -->
    <component :is="page" v-bind="pageProps" @go-to-page="goToPage" />
  </div>
</template>

<script>
import Dashboard from "./components/pos/Dashboard.vue";
import POS from "./components/pos/Pos.vue";
//  Removed CashierLogin import

export default {
  name: "Home",
  components: {
    Dashboard,
    POS,
    // CashierLogin removed
  },
  data() {
    return {
      page: "Dashboard", // default page
      pageProps: {},
    };
  },
  created() {
    this.setPageFromUrl();
    window.addEventListener("popstate", this.setPageFromUrl);
  },
  beforeUnmount() {
    window.removeEventListener("popstate", this.setPageFromUrl);
  },
  methods: {
    setPageFromUrl() {
      const path = window.location.pathname;

      if (path.startsWith("/dashboard")) {
        this.page = "Dashboard";
        this.pageProps = {};
      } else if (path.startsWith("/pos")) {
        this.page = "POS";
        const parts = path.split("/");
        const workOrder = parts[2] || null;
        this.pageProps = { workOrder };
      } else {
        // Default page if no match
        this.page = "Dashboard";
        this.pageProps = {};
      }
    },
    goToPage(pageName, props = {}) {
      this.page = pageName;
      this.pageProps = props;

      // update browser URL (no /login anymore)
      let url = "/";
      if (pageName === "Dashboard") url = "/dashboard";
      if (pageName === "POS") {
        url = "/pos";
        if (props.workOrder) url += `/${props.workOrder}`;
      }
      window.history.pushState({}, "", url);
    },
  },
};
</script>
