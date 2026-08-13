(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const isoFromToday = (days) => {
    const base = new Date();
    base.setHours(12, 0, 0, 0);
    base.setDate(base.getDate() + days);
    return base.toISOString().slice(0, 10);
  };

  const preview = $("#foto");
  const frameImg = $("#frame-preview");
  const frameCopy = $(".frame-copy");
  if (preview && frameImg) {
    preview.addEventListener("change", () => {
      const file = preview.files && preview.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      frameImg.src = url;
      frameImg.hidden = false;
      if (frameCopy) frameCopy.style.display = "none";
    });
  }

  const captureForm = $("#form-captura");
  if (captureForm) {
    captureForm.addEventListener("submit", () => {
      document.body.classList.add("is-reading");
      const kicker = $("[data-kicker-label]");
      if (kicker) kicker.textContent = "LEYENDO DOCUMENTO";
    });
  }

  const togglePhoto = $("#toggle-photo");
  const photoPanel = $("#photo-panel");
  if (togglePhoto && photoPanel) {
    togglePhoto.addEventListener("click", () => {
      const open = photoPanel.hasAttribute("hidden");
      if (open) photoPanel.removeAttribute("hidden");
      else photoPanel.setAttribute("hidden", "");
      togglePhoto.textContent = open ? "Ocultar carátula" : "Ver carátula";
    });
  }

  const dateSync = $("[data-sync-date]");
  const dateHidden = $("input[name='document_date']");
  if (dateSync && dateHidden) {
    dateSync.addEventListener("change", () => {
      dateHidden.value = dateSync.value;
    });
  }

  const paintCard = (card) => {
    if (!card) return;
    const exp = $("[data-expires]", card);
    const none = $("[data-novence]", card);
    const isNone = none && none.value === "1";
    const hasDate = !!(exp && exp.value);
    card.classList.toggle("is-none", isNone);
    card.classList.toggle("is-ready", isNone || hasDate);
    $$("[data-line-shift]", card).forEach((btn) => {
      if (!exp || !exp.value || isNone) {
        btn.classList.remove("is-on");
        return;
      }
      const days = Number(btn.getAttribute("data-line-shift"));
      btn.classList.toggle("is-on", exp.value === isoFromToday(days));
    });
    const noneBtn = $("[data-line-none]", card);
    if (noneBtn) noneBtn.classList.toggle("is-on", isNone);
  };

  const refreshProgress = () => {
    const cards = $$("[data-line]");
    const ready = cards.filter((c) => c.classList.contains("is-ready")).length;
    const total = cards.length;
    const node = $("#win-progress");
    if (node) node.textContent = `${ready} / ${total}`;
    const totalNode = $("#line-total");
    if (totalNode) totalNode.textContent = String(total);
    const btn = $("#btn-confirmar");
    if (btn) {
      btn.disabled = total === 0 || ready < total;
      btn.textContent =
        total === 0
          ? "Sin productos"
          : ready < total
            ? `Faltan ${total - ready}`
            : `Confirmar ${total} lote${total === 1 ? "" : "s"}`;
    }
  };

  const setDate = (card, iso) => {
    const exp = $("[data-expires]", card);
    const none = $("[data-novence]", card);
    if (exp) exp.value = iso || "";
    if (none) none.value = "0";
    paintCard(card);
    refreshProgress();
  };

  const setNone = (card) => {
    const exp = $("[data-expires]", card);
    const none = $("[data-novence]", card);
    if (exp) exp.value = "";
    if (none) none.value = "1";
    paintCard(card);
    refreshProgress();
  };

  const lines = $("#lines");
  if (lines) {
    lines.addEventListener("click", (ev) => {
      const card = ev.target.closest("[data-line]");
      if (!card) return;
      const kill = ev.target.closest("[data-remove-line]");
      if (kill) {
        card.remove();
        refreshProgress();
        return;
      }
      const shift = ev.target.closest("[data-line-shift]");
      if (shift) {
        ev.preventDefault();
        setDate(card, isoFromToday(Number(shift.getAttribute("data-line-shift"))));
        return;
      }
      const none = ev.target.closest("[data-line-none]");
      if (none) {
        ev.preventDefault();
        setNone(card);
        return;
      }
      const step = ev.target.closest("[data-step]");
      if (step) {
        ev.preventDefault();
        const input = document.getElementById(step.getAttribute("data-step")) || $("input[name='line_qty']", card);
        if (!input) return;
        const delta = Number(step.getAttribute("data-delta") || 1);
        const cur = Number(String(input.value).replace(",", ".")) || 0;
        input.value = String(Math.max(0, Math.round((cur + delta) * 100) / 100));
      }
    });

    lines.addEventListener("change", (ev) => {
      const card = ev.target.closest("[data-line]");
      if (!card) return;
      if (ev.target.matches("[data-expires]")) {
        const none = $("[data-novence]", card);
        if (none) none.value = ev.target.value ? "0" : none.value;
        paintCard(card);
        refreshProgress();
      }
    });
  }

  $$("[data-fill-rest]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.getAttribute("data-fill-rest");
      $$("[data-line]").forEach((card) => {
        if (card.classList.contains("is-ready")) return;
        if (kind === "none") setNone(card);
        else setDate(card, isoFromToday(Number(kind)));
      });
    });
  });

  const addLine = $("#add-line");
  const tpl = $("#line-template");
  if (addLine && lines && tpl) {
    addLine.addEventListener("click", () => {
      const node = tpl.content.cloneNode(true);
      const n = $$("[data-line]", lines).length + 1;
      const idx = node.querySelector("[data-idx]");
      if (idx) idx.textContent = String(n).padStart(2, "0");
      const qtyId = "qty-n-" + n + "-" + Date.now();
      const qty = node.querySelector("input[name='line_qty']");
      if (qty) qty.id = qtyId;
      node.querySelectorAll("[data-step]").forEach((b) => b.setAttribute("data-step", qtyId));
      lines.appendChild(node);
      refreshProgress();
    });
  }

  $$("[data-line]").forEach(paintCard);
  refreshProgress();

  const confirmForm = $("#form-confirmar");
  if (confirmForm) {
    confirmForm.addEventListener("submit", (ev) => {
      const submitter = ev.submitter;
      const action = (submitter && submitter.getAttribute("formaction")) || confirmForm.action;
      if (action.includes("/confirmar")) {
        const pending = $$("[data-line]").filter((c) => !c.classList.contains("is-ready"));
        if (pending.length) {
          ev.preventDefault();
          pending[0].scrollIntoView({ behavior: "smooth", block: "center" });
          return;
        }
        document.body.classList.add("is-activated");
      }
    });
  }
})();
