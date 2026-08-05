(() => {
  "use strict";
  let installPrompt = null;

  async function boot() {
    const [{ createEngine }, { createSession }] = await Promise.all([
      import("./engine.js?v=dj-operator-v1"),
      import("./session.js?v=dj-operator-v1"),
    ]);
    const engine = createEngine();
    createSession(engine);
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
  });

  document.querySelector("#install-app").addEventListener("click", async () => {
    if (installPrompt) {
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      return;
    }
    alert(/iphone|ipad|ipod/i.test(navigator.userAgent)
      ? "Safari: Teilen → Zum Home-Bildschirm"
      : "Browser-Menü: App installieren");
  });

  if ("serviceWorker" in navigator && window.isSecureContext) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("./service-worker.js?v=dj-operator-v1", { scope: "./" })
        .catch((error) => console.warn("DJ Operator service worker failed", error));
    });
  }

  void boot();
})();
