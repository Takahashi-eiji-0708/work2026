// 付箋（スティッキーノート）アドオン — 画面側
// 右下のボタンで付箋を追加。ドラッグで移動、右下の角でサイズ変更、色の切り替え・削除ができる。
// 内容は /api/stickies 経由で data/stickies.json に自動保存される。
(function () {
  if (window.__stickiesLoaded) return;
  window.__stickiesLoaded = true;

  const API = "/api/stickies";
  const COLORS = [
    ["yellow", "黄"],
    ["pink", "ピンク"],
    ["blue", "青"],
    ["green", "緑"],
    ["purple", "紫"],
  ];
  const state = { notes: [], hidden: false };
  const els = new Map();
  let layer, fab, toggle, saveTimer, topZ = 1, loaded = false;

  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  const now = () => new Date().toISOString();
  const h = (tag, cls, attrs) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (attrs) for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  };

  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 400);
  }

  function save(keepalive) {
    clearTimeout(saveTimer);
    if (!loaded) return;
    return fetch(API, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
      keepalive: !!keepalive,
    }).catch(() => {});
  }

  function clamp(note) {
    const vw = window.innerWidth, vh = window.innerHeight;
    note.x = Math.max(0, Math.min(note.x, vw - 80));
    note.y = Math.max(0, Math.min(note.y, vh - 40));
  }

  function place(note) {
    const el = els.get(note.id);
    if (!el) return;
    el.style.left = note.x + "px";
    el.style.top = note.y + "px";
    el.style.width = note.w + "px";
    el.style.height = note.h + "px";
    el.style.zIndex = String(1000 + note.z);
    el.dataset.color = note.color;
  }

  function bringToFront(note) {
    if (note.z === topZ) return;
    note.z = ++topZ;
    place(note);
    scheduleSave();
  }

  function render(note) {
    const el = h("div", "stk-note", { role: "note" });
    const bar = h("div", "stk-bar", { title: "ドラッグで移動" });
    const dots = h("div", "stk-colors");
    for (const [key, label] of COLORS) {
      const b = h("button", "stk-dot", { type: "button", "data-c": key, title: label, "aria-label": "色: " + label });
      b.addEventListener("click", (e) => {
        e.stopPropagation();
        note.color = key;
        note.updatedAt = now();
        place(note);
        scheduleSave();
      });
      dots.appendChild(b);
    }
    const del = h("button", "stk-del", { type: "button", title: "削除", "aria-label": "付箋を削除" });
    del.textContent = "×";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      if (note.text.trim() && !confirm("この付箋を削除しますか？")) return;
      removeNote(note.id);
    });
    bar.append(dots, del);

    const ta = h("textarea", "stk-text", { placeholder: "メモを入力…", "aria-label": "付箋の内容" });
    ta.value = note.text;
    ta.addEventListener("input", () => {
      note.text = ta.value;
      note.updatedAt = now();
      scheduleSave();
    });

    el.append(bar, ta);
    el.addEventListener("pointerdown", () => bringToFront(note));
    makeDraggable(el, bar, note);
    observeResize(el, note);
    els.set(note.id, el);
    layer.appendChild(el);
    place(note);
    return el;
  }

  function makeDraggable(el, handle, note) {
    handle.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || e.target.closest("button")) return;
      e.preventDefault();
      const sx = e.clientX - note.x, sy = e.clientY - note.y;
      handle.setPointerCapture(e.pointerId);
      el.classList.add("stk-dragging");
      const move = (ev) => {
        note.x = ev.clientX - sx;
        note.y = ev.clientY - sy;
        clamp(note);
        place(note);
      };
      const up = () => {
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", up);
        handle.removeEventListener("pointercancel", up);
        el.classList.remove("stk-dragging");
        scheduleSave();
      };
      handle.addEventListener("pointermove", move);
      handle.addEventListener("pointerup", up);
      handle.addEventListener("pointercancel", up);
    });
  }

  function observeResize(el, note) {
    if (!window.ResizeObserver) return;
    new ResizeObserver(() => {
      const w = Math.round(el.offsetWidth), hh = Math.round(el.offsetHeight);
      if (!w || !hh || (w === note.w && hh === note.h)) return;
      note.w = w;
      note.h = hh;
      scheduleSave();
    }).observe(el);
  }

  function addNote() {
    if (state.hidden) setHidden(false);
    const n = state.notes.length;
    const note = {
      id: uid(),
      text: "",
      color: COLORS[n % COLORS.length][0],
      x: window.innerWidth - 300 - (n % 6) * 24,
      y: 120 + (n % 6) * 24,
      w: 220,
      h: 180,
      z: ++topZ,
      updatedAt: now(),
    };
    clamp(note);
    state.notes.push(note);
    render(note).querySelector("textarea").focus();
    updateFab();
    scheduleSave();
  }

  function removeNote(id) {
    state.notes = state.notes.filter((n) => n.id !== id);
    const el = els.get(id);
    if (el) el.remove();
    els.delete(id);
    updateFab();
    scheduleSave();
  }

  function setHidden(hidden) {
    state.hidden = hidden;
    layer.classList.toggle("stk-hidden", hidden);
    updateFab();
    scheduleSave();
  }

  function updateFab() {
    const count = state.notes.length;
    toggle.hidden = count === 0;
    toggle.textContent = state.hidden ? "付箋を表示 (" + count + ")" : "付箋を隠す";
    toggle.setAttribute("aria-pressed", String(state.hidden));
  }

  function mount() {
    layer = h("div", "stk-layer");
    const dock = h("div", "stk-dock");
    toggle = h("button", "stk-toggle", { type: "button" });
    toggle.addEventListener("click", () => setHidden(!state.hidden));
    fab = h("button", "stk-fab", { type: "button", title: "付箋を追加 (Alt+N)" });
    fab.innerHTML = '<span aria-hidden="true">＋</span> 付箋';
    fab.addEventListener("click", addNote);
    dock.append(toggle, fab);
    document.body.append(layer, dock);
    updateFab();

    window.addEventListener("resize", () => state.notes.forEach((n) => { clamp(n); place(n); }));
    window.addEventListener("pagehide", () => saveTimer && save(true));
    document.addEventListener("keydown", (e) => {
      if (e.altKey && !e.ctrlKey && !e.metaKey && (e.key === "n" || e.key === "N")) {
        e.preventDefault();
        addNote();
      }
    });

    fetch(API, { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => {
        state.notes = Array.isArray(data.notes) ? data.notes : [];
        state.hidden = !!data.hidden;
        topZ = state.notes.reduce((m, n) => Math.max(m, n.z || 1), 1);
        state.notes.forEach((n) => { clamp(n); render(n); });
        layer.classList.toggle("stk-hidden", state.hidden);
        loaded = true;
        updateFab();
      })
      // 読み込みに失敗したまま保存すると既存の付箋を消してしまうので、保存は止めたままにする
      .catch(() => {});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
