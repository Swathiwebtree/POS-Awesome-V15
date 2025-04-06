<template>
  <div>
    <v-autocomplete
      ref="customerDropdown"
      density="compact"
      clearable
      variant="outlined"
      color="primary"
      :label="frappe._('Customer')"
      v-model="internalCustomer"
      :items="customers"
      item-title="customer_name"
      item-value="name"
      bg-color="white"
      :no-data-text="__('Customers not found')"
      hide-details
      :customFilter="customFilter"
      :disabled="readonly"
      append-icon="mdi-plus"
      @click:append="new_customer"
      prepend-inner-icon="mdi-account-edit"
      @click:prepend-inner="edit_customer"
      @update:menu="onCustomerMenuToggle"
      @update:modelValue="onCustomerChange"
      @keydown.enter="handleEnter"
    >
      <template v-slot:item="{ props, item }">
        <v-list-item v-bind="props">
          <v-list-item-subtitle v-if="item.raw.customer_name != item.raw.name">
            <div v-html="`ID: ${item.raw.name}`"></div>
          </v-list-item-subtitle>
          <v-list-item-subtitle v-if="item.raw.tax_id">
            <div v-html="`TAX ID: ${item.raw.tax_id}`"></div>
          </v-list-item-subtitle>
          <v-list-item-subtitle v-if="item.raw.email_id">
            <div v-html="`Email: ${item.raw.email_id}`"></div>
          </v-list-item-subtitle>
          <v-list-item-subtitle v-if="item.raw.mobile_no">
            <div v-html="`Mobile No: ${item.raw.mobile_no}`"></div>
          </v-list-item-subtitle>
          <v-list-item-subtitle v-if="item.raw.primary_address">
            <div v-html="`Primary Address: ${item.raw.primary_address}`"></div>
          </v-list-item-subtitle>
        </v-list-item>
      </template>
    </v-autocomplete>

    <div class="mb-8">
      <UpdateCustomer></UpdateCustomer>
    </div>
  </div>
</template>

<script>
import UpdateCustomer from './UpdateCustomer.vue';

export default {
  props: {
    pos_profile: Object
  },

  data: () => ({
    pos_profile: '',
    customers: [],
    customer: '',
    internalCustomer: null,
    tempSelectedCustomer: null,
    isMenuOpen: false,
    readonly: false,
    customer_info: {},
  }),

  components: {
    UpdateCustomer,
  },

  methods: {
    onCustomerMenuToggle(isOpen) {
      this.isMenuOpen = isOpen;

      if (isOpen) {
        this.internalCustomer = null;

        this.$nextTick(() => {
          setTimeout(() => {
            const dropdown = this.$refs.customerDropdown?.$el?.querySelector('.v-overlay__content .v-select-list');
            if (dropdown) dropdown.scrollTop = 0;
          }, 50);
        });
      } else {
        if (this.tempSelectedCustomer) {
          this.internalCustomer = this.tempSelectedCustomer;
          this.customer = this.tempSelectedCustomer;
          this.eventBus.emit('update_customer', this.customer);
        }
        this.tempSelectedCustomer = null;
      }
    },

    onCustomerChange(val) {
      this.tempSelectedCustomer = val;

      if (!this.isMenuOpen) {
        this.customer = val;
        this.eventBus.emit('update_customer', val);
      }
    },

    handleEnter(event) {
      const inputText = event.target.value?.toLowerCase() || '';

      const matched = this.customers.find(cust => {
        return (
          cust.customer_name?.toLowerCase().includes(inputText) ||
          cust.name?.toLowerCase().includes(inputText)
        );
      });

      if (matched) {
        this.tempSelectedCustomer = matched.name;
        this.internalCustomer = matched.name;
        this.customer = matched.name;
        this.eventBus.emit('update_customer', matched.name);
        this.isMenuOpen = false;

        // force close the menu
        event.target.blur();
      }
    },

    get_customer_names() {
      var vm = this;
      if (this.customers.length > 0) return;

      if (vm.pos_profile.posa_local_storage && localStorage.customer_storage) {
        vm.customers = JSON.parse(localStorage.getItem('customer_storage'));
      }

      this.loadingCustomers = true;
      frappe.call({
        method: 'posawesome.posawesome.api.posapp.get_customer_names',
        args: {
          pos_profile: this.pos_profile.pos_profile,
        },
        callback: function (r) {
          if (r.message) {
            vm.customers = r.message;
            vm.loadingCustomers = false;

            if (vm.pos_profile.posa_local_storage) {
              localStorage.setItem('customer_storage', '');
              localStorage.setItem('customer_storage', JSON.stringify(r.message));
            }
          }
        },
      });
    },

    new_customer() {
      this.eventBus.emit('open_update_customer', null);
    },

    edit_customer() {
      this.eventBus.emit('open_update_customer', this.customer_info);
    },

    customFilter(itemText, queryText, itemRow) {
      const item = itemRow.raw;
      const textOne = item.customer_name ? item.customer_name.toLowerCase() : '';
      const textTwo = item.tax_id ? item.tax_id.toLowerCase() : '';
      const textThree = item.email_id ? item.email_id.toLowerCase() : '';
      const textFour = item.mobile_no ? item.mobile_no.toLowerCase() : '';
      const textFifth = item.name.toLowerCase();
      const searchText = queryText.toLowerCase();

      return (
        textOne.includes(searchText) ||
        textTwo.includes(searchText) ||
        textThree.includes(searchText) ||
        textFour.includes(searchText) ||
        textFifth.includes(searchText)
      );
    },
  },

  created() {
    this.$nextTick(() => {
      this.eventBus.on('register_pos_profile', (pos_profile) => {
        this.pos_profile = pos_profile;
        this.get_customer_names();
      });
      this.eventBus.on('payments_register_pos_profile', (pos_profile) => {
        this.pos_profile = pos_profile;
        this.get_customer_names();
      });
      this.eventBus.on('set_customer', (customer) => {
        this.customer = customer;
        this.internalCustomer = customer;
      });
      this.eventBus.on('add_customer_to_list', (customer) => {
        this.customers.push(customer);
      });
      this.eventBus.on('set_customer_readonly', (value) => {
        this.readonly = value;
      });
      this.eventBus.on('set_customer_info_to_edit', (data) => {
        this.customer_info = data;
      });
      this.eventBus.on('fetch_customer_details', () => {
        this.get_customer_names();
      });
    });
  },
};
</script>
