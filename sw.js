/* Service Worker — Fragoso Bot
 * Estratégias:
 *   - Navegação (o HTML)      -> rede primeiro, cache como recurso de reserva
 *   - App shell (ícones, etc) -> precarregado na instalação
 *   - CDNs (Tailwind, FA...)  -> cache primeiro, atualiza em segundo plano
 *   - Pedidos à API / Space   -> nunca em cache (passam sempre pela rede)
 *
 * Ao alterar ficheiros, incrementar VERSION para forçar a atualização.
 */

const VERSION = "v12";
const SHELL_CACHE = `fragoso-bot-shell-${VERSION}`;
const CDN_CACHE = `fragoso-bot-cdn-${VERSION}`;

// Essenciais: se algum falhar, a instalação falha (e deve mesmo falhar).
const SHELL_CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest"
];

// Opcionais: ícones. Se ainda não existirem, não podem abortar a instalação.
const SHELL_OPTIONAL = [
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/maskable-192.png",
  "./icons/maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-64.png"
];

const CDN_HOSTS = [
  "cdn.tailwindcss.com",
  "cdnjs.cloudflare.com",
  "fonts.googleapis.com",
  "fonts.gstatic.com",
  "cdn.jsdelivr.net"
];

// --- Instalação: precarrega o app shell ---
// cache.addAll() é atómico: um único 404 (ex.: um ícone em falta) rejeita tudo
// e o Service Worker nunca chega a instalar. Por isso os ícones vão um a um.
self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(SHELL_CACHE);
      await cache.addAll(SHELL_CORE);
      await Promise.all(
        SHELL_OPTIONAL.map((url) =>
          cache.add(url).catch(() => console.warn("[sw] recurso opcional em falta:", url))
        )
      );
      await self.skipWaiting();
    })()
  );
});

// --- Ativação: limpa caches de versões anteriores ---
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key !== SHELL_CACHE && key !== CDN_CACHE)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// Guarda em cache respostas normais e opacas (os scripts de CDN vêm em modo no-cors)
function isCacheable(response) {
  return response && (response.ok || response.type === "opaque");
}

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Só GET. POST para a API/Space passa sempre pela rede.
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Nunca interceptar chamadas de inferência (Hugging Face, APIs próprias, localhost)
  if (
    url.hostname.endsWith("hf.space") ||
    url.hostname.endsWith("huggingface.co") ||
    url.hostname === "localhost" ||
    url.hostname === "127.0.0.1"
  ) {
    return;
  }

  // 1. Navegação: rede primeiro, index.html em cache como reserva
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put("./index.html", copy));
          return response;
        })
        .catch(() => caches.match("./index.html").then((r) => r || caches.match("./")))
    );
    return;
  }

  // 2. CDNs: cache primeiro, revalida em segundo plano
  if (CDN_HOSTS.includes(url.hostname)) {
    event.respondWith(
      caches.open(CDN_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        const network = fetch(request)
          .then((response) => {
            if (isCacheable(response)) cache.put(request, response.clone());
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // 3. Ficheiros próprios: cache primeiro, com atualização oportunista
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (isCacheable(response)) {
            const copy = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        });
      })
    );
  }
});

// Permite que a página force a ativação imediata de uma nova versão
self.addEventListener("message", (event) => {
  if (event.data === "skip-waiting") self.skipWaiting();
});
