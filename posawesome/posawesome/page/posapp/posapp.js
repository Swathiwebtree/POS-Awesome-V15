frappe.pages['posawesome'].on_page_load = function(wrapper) {
    // Initialize the page
    frappe.make_app_page({
        parent: wrapper,
        title: 'POS Awesome',
        single_column: true
    });

    // Initialize the POS App
    this.page.PosApp = new frappe.PosApp.posapp(this.page);

    // Use a timeout to make sure everything is fully initialized before running
    setTimeout(function() {
        // Call the function to update totals based on the selected POS Profile
        update_totals_based_on_tax_inclusive();
    }, 500);  // Adjust the timeout if necessary
};

// Function to update total based on the `posa_tax_inclusive` from POS Profile
function update_totals_based_on_tax_inclusive() {
    const posProfile = this.page.PosApp.pos_profile;

    // Ensure the POS Profile is correctly set
    if (!posProfile) {
        console.error("POS Profile is not set.");
        return;
    }

    // Fetch the current selected POS Profile's `posa_tax_inclusive` value
    frappe.call({
        method: 'frappe.get_cached_value',
        args: {
            doctype: 'POS Profile',  // POS Profile doctype
            name: posProfile,  // The POS Profile selected for this session
            fieldname: 'posa_tax_inclusive'  // The field we're interested in
        },
        callback: function(response) {
            if (response.message !== undefined) {
                const posa_tax_inclusive = response.message;  // Get the value of the checkbox

                // Target the total amount field and grand total field
                const totalAmountField = document.getElementById('input-v-25');
                const grandTotalField = document.getElementById('input-v-29');

                if (totalAmountField && grandTotalField) {
                    // If `posa_tax_inclusive` is checked in the POS Profile
                    if (posa_tax_inclusive) {
                        // Copy the grand total value to the total amount field
                        totalAmountField.value = grandTotalField.value;
                        console.log("Total amount copied from grand total:", grandTotalField.value);
                    } else {
                        // If unchecked, clear the total amount field
                        totalAmountField.value = "";
                        console.log("Total amount cleared because checkbox is unchecked.");
                    }
                } else {
                    console.error('Could not find total amount or grand total field by ID.');
                }
            } else {
                console.error('Error fetching POS Profile or POS Profile not found.');
            }
        }
    });
}
