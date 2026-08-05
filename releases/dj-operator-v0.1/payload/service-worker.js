"use strict";

const CACHE = "kyron-dj-operator-v2";
const asset = (path) => new URL(path, self.registration.scope).toString();
const HOME = asset("./");
const SHELL = [
  "./",
  "index.html",
  "styles.css?v=dj-operator-v1",
  "app.js?v=dj-operator-v1",
  "engine.js?v=dj-operator-v1",
  "session.js?v=dj-operator-v1",
  "manifest.webmanifest?v=dj-operator-v1",
  "icon.svg"
].map(asset);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)),
    )),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !url.href.startsWith(self.registration.scope)) return;
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(HOME, copy));
          return response;
        })
        .catch(() => caches.match(HOME)),
    );
    return;
  }
  event.respondWith(
    caches.match(request).then((cached) => {
      const refresh = fetch(request)
        .then((response) => {
          if (response.ok) caches.open(CACHE).then((cache) => cache.put(request, response.clone()));
          return response;
        })
        .catch(() => cached);
      return cached || refresh;
    }),
  );
});
