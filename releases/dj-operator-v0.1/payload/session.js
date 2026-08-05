export function createSession(engine) {
  const KEY = "kyron.dj-operator.session.v1";
  const notes = document.querySelector("#session-notes");
  const list = document.querySelector("#set-list");
  const empty = document.querySelector("#set-empty");
  let state;
  try {
    state = JSON.parse(localStorage.getItem(KEY) || "null");
  } catch {
    state = null;
  }
  if (!state || state.schema_version !== KEY) state = { schema_version: KEY, setlist: [], notes: "" };
  notes.value = state.notes || "";

  const persist = () => {
    state.notes = notes.value;
    localStorage.setItem(KEY, JSON.stringify(state));
  };

  function render() {
    list.replaceChildren();
    empty.hidden = state.setlist.length > 0;
    state.setlist.forEach((item, index) => {
      const row = document.createElement("li");
      row.innerHTML = `<strong>${String(index + 1).padStart(2, "0")}</strong><div><div class="set-title"></div><div class="set-meta"></div></div>`;
      row.querySelector(".set-title").textContent = item.title;
      row.querySelector(".set-meta").textContent = `${item.deck} · ${item.bpm ? `${item.bpm} BPM` : "BPM offen"}`;
      const remove = document.createElement("button");
      remove.textContent = "×";
      remove.addEventListener("click", () => {
        state.setlist = state.setlist.filter((entry) => entry.id !== item.id);
        persist(); render();
      });
      row.append(remove);
      list.append(row);
    });
  }

  function add(id) {
    const deck = engine.decks[id];
    if (!deck.fileName) return alert(`Deck ${id.toUpperCase()} enthält keinen Track.`);
    state.setlist.push({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      title: deck.fileName,
      deck: id.toUpperCase(),
      bpm: Number(document.querySelector(`#bpm-${id}`).value) || null,
    });
    state.setlist = state.setlist.slice(-100);
    persist(); render();
  }

  const deckData = (id) => ({
    file_name: engine.decks[id].fileName || null,
    bpm: Number(document.querySelector(`#bpm-${id}`).value) || null,
    cues_seconds: engine.decks[id].cues,
    playback_rate: engine.decks[id].audio.playbackRate,
    analysis: engine.decks[id].analysis,
  });

  function exportSession() {
    const payload = {
      schema_version: KEY,
      created_at: new Date().toISOString(),
      privacy: "LOCAL_METADATA_ONLY_NO_AUDIO",
      decks: { a: deckData("a"), b: deckData("b") },
      crossfader: Number(engine.crossfader.value),
      setlist: state.setlist,
      notes: notes.value,
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `KYRON_DJ_SESSION_${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function importSession(file) {
    try {
      const payload = JSON.parse(await file.text());
      if (payload.schema_version !== KEY) throw new Error("Unbekanntes Session-Schema.");
      state.setlist = Array.isArray(payload.setlist) ? payload.setlist.slice(0, 100) : [];
      notes.value = typeof payload.notes === "string" ? payload.notes : "";
      for (const id of ["a", "b"]) {
        const source = payload.decks?.[id] || {};
        document.querySelector(`#bpm-${id}`).value = Number(source.bpm) || "";
        engine.decks[id].cues = Array.isArray(source.cues_seconds) ? source.cues_seconds.slice(0, 4) : [null, null, null, null];
        engine.resetCues(id);
        engine.decks[id].cues.forEach((value, index) => {
          if (value == null) return;
          const button = document.querySelector(`[data-cue-set="${id}:${index}"]`);
          button.textContent = `CUE ${index + 1} · ${engine.time(value)}`;
          button.classList.add("cue-set");
        });
      }
      engine.crossfader.value = String(Math.max(-1, Math.min(1, Number(payload.crossfader) || 0)));
      persist(); render(); engine.mix();
    } catch (error) {
      alert(`Import blockiert: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  function clear() {
    if (!confirm("Setliste, Notizen, BPM und Cue-Punkte leeren? Audiodateien werden nicht gelöscht.")) return;
    state.setlist = [];
    notes.value = "";
    for (const id of ["a", "b"]) {
      engine.decks[id].cues = [null, null, null, null];
      document.querySelector(`#bpm-${id}`).value = "";
      engine.resetCues(id);
    }
    persist(); render();
  }

  document.querySelector("#add-a").addEventListener("click", () => add("a"));
  document.querySelector("#add-b").addEventListener("click", () => add("b"));
  document.querySelector("#export-session").addEventListener("click", exportSession);
  document.querySelector("#import-session").addEventListener("change", (event) => {
    const file = event.currentTarget.files?.[0];
    if (file) void importSession(file);
    event.currentTarget.value = "";
  });
  document.querySelector("#clear-session").addEventListener("click", clear);
  notes.addEventListener("input", persist);
  render();
}
