{% load static %}
// Keeps the calendar usable offline: pages and events come from the network when possible,
// and from the last saved copy otherwise. Bump the version to drop old caches.
const CACHE = "carpe-v1";
const OFFLINE_PAGES = ["{% url 'calendar' %}"];

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(OFFLINE_PAGES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
            .then(() => self.clients.claim())
    );
});

async function networkFirst(request) {
    const cache = await caches.open(CACHE);
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        if (request.mode === "navigate") {
            return cache.match("{% url 'calendar' %}");
        }
        throw error;
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(request);
    const network = fetch(request).then((response) => {
        // CDN scripts and styles load without CORS, so their responses are opaque (status 0)
        if (response.ok || response.type === "opaque") {
            cache.put(request, response.clone());
        }
        return response;
    });
    return cached || network;
}

const STATIC_HOSTS = ["cdn.jsdelivr.net", "cdnjs.cloudflare.com", "unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com"];

self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);
    if (request.method !== "GET") {
        return;
    }
    if (url.origin === self.location.origin) {
        // Admin, edit links and downloads always go to the network
        if (url.pathname.startsWith("/admin") || url.pathname.includes("/edit/") || url.pathname.endsWith(".ics")) {
            return;
        }
        if (url.pathname.startsWith("{% get_static_prefix %}")) {
            event.respondWith(staleWhileRevalidate(request));
        } else {
            event.respondWith(networkFirst(request));
        }
    } else if (STATIC_HOSTS.includes(url.hostname)) {
        event.respondWith(staleWhileRevalidate(request));
    }
});
