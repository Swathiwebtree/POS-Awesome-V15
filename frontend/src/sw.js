const SW_VERSION = new URL(self.location.href).searchParams.get("v") || "1";

if (!self.define) {
	try {
		importScripts("https://storage.googleapis.com/workbox-cdn/releases/6.5.4/workbox-sw.js");
	} catch (e) {
		importScripts(`/assets/posawesome/dist/js/libs/workbox-sw.js?v=${encodeURIComponent(SW_VERSION)}`);
	}
}

self.addEventListener("message", (event) => {
	if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

workbox.core.clientsClaim();

const SW_REVISION = SW_VERSION;
workbox.precaching.precacheAndRoute([
	{
		url: `/assets/posawesome/dist/js/posawesome.umd.js?v=${encodeURIComponent(SW_VERSION)}`,
		revision: SW_REVISION,
	},
	{
		url: `/assets/posawesome/dist/js/offline/index.js?v=${encodeURIComponent(SW_VERSION)}`,
		revision: SW_REVISION,
	},
	{ url: "/manifest.json", revision: SW_REVISION },
	{ url: "/offline.html", revision: SW_REVISION },
]);

workbox.routing.registerRoute(
	({ url }) => url.pathname.startsWith("/api/"),
	new workbox.strategies.NetworkFirst({ cacheName: "api-cache", networkTimeoutSeconds: 3 }),
);

workbox.routing.registerRoute(
	({ request }) => ["script", "style", "document"].includes(request.destination),
	new workbox.strategies.StaleWhileRevalidate(),
);
