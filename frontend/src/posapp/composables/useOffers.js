import { ref, getCurrentInstance } from "vue";
import { getCachedOffers, saveOffers } from "../../offline/index.js";

export function useOffers() {
	const { proxy } = getCurrentInstance();
	const eventBus = proxy?.eventBus;

	const offers = ref([]);
	const coupons = ref([]); 

	function get_offers(profileName, posProfile) {
		// 1️⃣ Load from cache
		if (posProfile && posProfile.posa_local_storage) {
			const cached = getCachedOffers();
			if (cached?.offers?.length) {
				offers.value = cached.offers;
				eventBus?.emit("set_offers", offers.value);
			}
			if (cached?.coupons?.length) {
				coupons.value = cached.coupons;
				eventBus?.emit("set_coupons", coupons.value);
			}
		}

	
		return frappe
			.call("posawesome.posawesome.api.offers.get_offers", {
				profile: profileName,
			})
			.then((r) => {
				if (!r.message) return;

				console.info("[POS] LoadOffers", r.message);

				// EXPECTED BACKEND RESPONSE
				// {
				//   offers: [],
				//   coupons: []
				// }

				offers.value = r.message.offers || [];
				coupons.value = r.message.coupons || [];

				saveOffers(r.message);

				eventBus?.emit("set_offers", offers.value);
				eventBus?.emit("set_coupons", coupons.value);

				eventBus?.emit("update_offers_counters", {
					offersCount: offers.value.length,
				});
				eventBus?.emit("update_coupons_counters", {
					couponsCount: coupons.value.length,
				});
			})
			.catch((err) => {
				console.error("Failed to fetch offers:", err);
			});
	}

	return {
		offers,
		coupons, 
		get_offers,
	};
}
