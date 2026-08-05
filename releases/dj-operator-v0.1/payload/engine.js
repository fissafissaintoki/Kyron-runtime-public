export function createEngine() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const context = AudioCtx ? new AudioCtx() : null;
  const crossfader = document.querySelector("#crossfader");
  const decks = Object.fromEntries(["a", "b"].map((id) => [id, {
    id, audio: new Audio(), source: null, gain: null, url: null, fileName: "",
    buffer: null, peaks: [], taps: [], cues: [null, null, null, null], analysis: null,
  }]));
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const time = (seconds) => {
    const value = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
    return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
  };

  async function graph(deck) {
    if (!context || deck.source) return;
    if (context.state === "suspended") await context.resume();
    deck.source = context.createMediaElementSource(deck.audio);
    deck.gain = context.createGain();
    deck.source.connect(deck.gain).connect(context.destination);
    mix();
  }

  function mix() {
    const angle = (Number(crossfader.value) + 1) * Math.PI / 4;
    const a = Math.cos(angle);
    const b = Math.sin(angle);
    if (decks.a.gain) decks.a.gain.gain.value = a * Number(document.querySelector("#gain-a").value);
    if (decks.b.gain) decks.b.gain.gain.value = b * Number(document.querySelector("#gain-b").value);
    document.querySelector("#gain-readout-a").textContent = `A ${Math.round(a * 100)}%`;
    document.querySelector("#gain-readout-b").textContent = `B ${Math.round(b * 100)}%`;
  }

  function peaks(buffer, buckets = 220) {
    const data = buffer.getChannelData(0);
    const size = Math.max(1, Math.floor(data.length / buckets));
    return Array.from({ length: buckets }, (_, bucket) => {
      let peak = 0;
      const end = Math.min(data.length, (bucket + 1) * size);
      for (let i = bucket * size; i < end; i += 1) peak = Math.max(peak, Math.abs(data[i]));
      return peak;
    });
  }

  function draw(id) {
    const deck = decks[id];
    const canvas = document.querySelector(`#wave-${id}`);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#05090f";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = id === "a" ? "#5ee8ff" : "#ae83ff";
    ctx.lineWidth = 2;
    const bars = deck.peaks.length ? deck.peaks : Array.from({ length: 160 }, (_, i) => .035 + .018 * Math.sin(i / 7));
    const step = canvas.width / bars.length;
    bars.forEach((peak, index) => {
      const height = Math.max(2, peak * canvas.height * .9);
      ctx.beginPath();
      ctx.moveTo(index * step, (canvas.height - height) / 2);
      ctx.lineTo(index * step, (canvas.height + height) / 2);
      ctx.stroke();
    });
    const ratio = deck.audio.duration ? deck.audio.currentTime / deck.audio.duration : 0;
    ctx.fillStyle = "rgba(255,255,255,.17)";
    ctx.fillRect(0, 0, canvas.width * ratio, canvas.height);
    ctx.fillStyle = "white";
    ctx.fillRect(canvas.width * ratio, 0, 2, canvas.height);
  }

  async function load(id, file) {
    if (!file?.type.startsWith("audio/")) return alert("Bitte eine Audiodatei wählen.");
    if (!context) return alert("Web Audio wird von diesem Browser nicht unterstützt.");
    const deck = decks[id];
    await graph(deck);
    if (deck.url) URL.revokeObjectURL(deck.url);
    deck.url = URL.createObjectURL(file);
    deck.fileName = file.name;
    deck.audio.src = deck.url;
    deck.cues = [null, null, null, null];
    deck.analysis = null;
    document.querySelector(`#title-${id}`).textContent = file.name;
    document.querySelector(`#advice-${id}`).textContent = "Audio lokal geladen. Analyse bereit.";
    resetCues(id);
    try {
      deck.buffer = await context.decodeAudioData((await file.arrayBuffer()).slice(0));
      deck.peaks = peaks(deck.buffer);
    } catch (error) {
      console.warn("Local decode failed", error);
      deck.buffer = null;
      deck.peaks = [];
    }
    draw(id);
  }

  async function play(id) {
    const deck = decks[id];
    if (!deck.audio.src) return alert(`Zuerst Track in Deck ${id.toUpperCase()} laden.`);
    await graph(deck);
    if (deck.audio.paused) await deck.audio.play(); else deck.audio.pause();
  }

  function transport(id) {
    const deck = decks[id];
    const ratio = deck.audio.duration ? deck.audio.currentTime / deck.audio.duration : 0;
    document.querySelector(`#seek-${id}`).value = String(Math.round(ratio * 1000));
    document.querySelector(`#time-${id}`).textContent = `${time(deck.audio.currentTime)} / ${time(deck.audio.duration)}`;
    document.querySelector(`#play-${id}`).textContent = deck.audio.paused ? "PLAY" : "PAUSE";
    draw(id);
  }

  function tap(id) {
    const deck = decks[id];
    const now = performance.now();
    deck.taps = deck.taps.filter((value) => now - value < 5000);
    deck.taps.push(now);
    if (deck.taps.length < 2) return;
    const intervals = deck.taps.slice(1).map((value, index) => value - deck.taps[index]).sort((a, b) => a - b);
    const bpm = clamp(60000 / intervals[Math.floor(intervals.length / 2)], 40, 240);
    document.querySelector(`#bpm-${id}`).value = String(Math.round(bpm * 10) / 10);
  }

  function sync(source, target) {
    const from = Number(document.querySelector(`#bpm-${source}`).value);
    const to = Number(document.querySelector(`#bpm-${target}`).value);
    if (!from || !to) return alert("Für beide Decks BPM setzen oder tappen.");
    const rate = clamp(from / to, .85, 1.15);
    decks[target].audio.playbackRate = rate;
    alert(`Deck ${target.toUpperCase()} läuft mit ${rate.toFixed(3)}×.`);
  }

  function resetCues(id) {
    for (let i = 0; i < 4; i += 1) {
      const button = document.querySelector(`[data-cue-set="${id}:${i}"]`);
      button.textContent = `SET CUE ${i + 1}`;
      button.classList.remove("cue-set");
    }
  }

  function setCue(id, index) {
    if (!decks[id].audio.src) return;
    decks[id].cues[index] = decks[id].audio.currentTime;
    const button = document.querySelector(`[data-cue-set="${id}:${index}"]`);
    button.textContent = `CUE ${index + 1} · ${time(decks[id].cues[index])}`;
    button.classList.add("cue-set");
  }

  function analyse(id) {
    const deck = decks[id];
    if (!deck.buffer) return alert("Track konnte nicht lokal analysiert werden.");
    const data = deck.buffer.getChannelData(0);
    const rate = deck.buffer.sampleRate;
    const stride = Math.max(1, Math.floor(data.length / Math.min(data.length, rate * 75)));
    const lowAlpha = Math.exp(-2 * Math.PI * 200 / rate);
    const midAlpha = Math.exp(-2 * Math.PI * 2500 / rate);
    let lp = 0, mp = 0, full = 0, low = 0, mid = 0, high = 0, count = 0;
    for (let i = 0; i < data.length; i += stride) {
      const x = data[i];
      lp = (1 - lowAlpha) * x + lowAlpha * lp;
      mp = (1 - midAlpha) * x + midAlpha * mp;
      const l = lp, m = mp - lp, h = x - mp;
      full += x * x; low += l * l; mid += m * m; high += h * h; count += 1;
    }
    const total = low + mid + high || 1;
    const result = { rms: Math.sqrt(full / Math.max(1, count)), low: low / total, mid: mid / total, high: high / total };
    deck.analysis = result;
    document.querySelector(`#analysis-${id}`).innerHTML = [
      `LEVEL ${Math.round(result.rms * 100)}%`, `LOW ${Math.round(result.low * 100)}%`,
      `MID ${Math.round(result.mid * 100)}%`, `HIGH ${Math.round(result.high * 100)}%`,
    ].map((value) => `<span>${value}</span>`).join("");
    const dominant = [["LOW", result.low], ["MID", result.mid], ["HIGH", result.high]].sort((a, b) => b[1] - a[1])[0][0];
    document.querySelector(`#advice-${id}`).textContent = dominant === "LOW"
      ? "Bassbetont: Basswechsel nacheinander ausführen und Headroom halten."
      : dominant === "HIGH"
        ? "Höhenbetont: klare Attacks; für Cuts geeignet, Resonanz kontrollieren."
        : "Mittenbetont: Melodie und Vocals beim Übergang bewusst staffeln.";
  }

  function bind(id) {
    const deck = decks[id];
    document.querySelector(`#file-${id}`).addEventListener("change", (event) => {
      const file = event.currentTarget.files?.[0];
      if (file) void load(id, file);
      event.currentTarget.value = "";
    });
    document.querySelector(`#play-${id}`).addEventListener("click", () => void play(id));
    document.querySelector(`#back-${id}`).addEventListener("click", () => deck.audio.currentTime = clamp(deck.audio.currentTime - 10, 0, deck.audio.duration || 0));
    document.querySelector(`#forward-${id}`).addEventListener("click", () => deck.audio.currentTime = clamp(deck.audio.currentTime + 10, 0, deck.audio.duration || 0));
    document.querySelector(`#seek-${id}`).addEventListener("input", (event) => {
      if (deck.audio.duration) deck.audio.currentTime = Number(event.currentTarget.value) / 1000 * deck.audio.duration;
    });
    document.querySelector(`#gain-${id}`).addEventListener("input", mix);
    document.querySelector(`#tap-${id}`).addEventListener("click", () => tap(id));
    document.querySelector(`#analyse-${id}`).addEventListener("click", () => analyse(id));
    deck.audio.addEventListener("timeupdate", () => transport(id));
    deck.audio.addEventListener("play", () => transport(id));
    deck.audio.addEventListener("pause", () => transport(id));
    document.querySelector(`#wave-${id}`).addEventListener("pointerdown", (event) => {
      if (!deck.audio.duration) return;
      const rect = event.currentTarget.getBoundingClientRect();
      deck.audio.currentTime = clamp((event.clientX - rect.left) / rect.width, 0, 1) * deck.audio.duration;
    });
    draw(id);
  }

  document.querySelectorAll("[data-cue-set]").forEach((button) => button.addEventListener("click", () => {
    const [id, index] = button.dataset.cueSet.split(":"); setCue(id, Number(index));
  }));
  document.querySelectorAll("[data-cue-go]").forEach((button) => button.addEventListener("click", () => {
    const [id, index] = button.dataset.cueGo.split(":");
    const value = decks[id].cues[Number(index)]; if (value != null) decks[id].audio.currentTime = value;
  }));
  document.querySelector("#sync-a").addEventListener("click", () => sync("a", "b"));
  document.querySelector("#sync-b").addEventListener("click", () => sync("b", "a"));
  crossfader.addEventListener("input", mix);
  bind("a"); bind("b"); mix();

  return { decks, crossfader, mix, resetCues, time };
}
