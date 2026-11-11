(() => {
  "use strict";

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* Header: transparent at top, solid after scrolling */
  const header = document.querySelector("[data-header]");
  const onScroll = () => header?.classList.toggle("is-scrolled", window.scrollY > 12);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* Desktop dropdowns: click/keyboard toggle, hover on fine pointers, Esc and outside click close */
  const dropdowns = [...document.querySelectorAll("[data-dropdown]")];
  const setOpen = (dd, open) => {
    const btn = dd.querySelector("[data-dropdown-toggle]");
    const panel = dd.querySelector("[data-dropdown-panel]");
    btn.setAttribute("aria-expanded", String(open));
    panel.hidden = !open;
  };
  const closeAll = (except) => dropdowns.forEach((dd) => dd !== except && setOpen(dd, false));
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");

  dropdowns.forEach((dd) => {
    const btn = dd.querySelector("[data-dropdown-toggle]");
    let timer;
    let openedByHover = false;
    btn.addEventListener("click", () => {
      const isOpen = btn.getAttribute("aria-expanded") === "true";
      const open = isOpen && openedByHover ? true : !isOpen;
      openedByHover = false;
      closeAll(dd);
      setOpen(dd, open);
    });
    dd.addEventListener("mouseenter", () => {
      if (!finePointer.matches) return;
      clearTimeout(timer);
      if (btn.getAttribute("aria-expanded") !== "true") openedByHover = true;
      closeAll(dd);
      setOpen(dd, true);
    });
    dd.addEventListener("mouseleave", () => {
      if (!finePointer.matches) return;
      timer = setTimeout(() => setOpen(dd, false), 140);
    });
    dd.addEventListener("focusout", (e) => {
      if (!dd.contains(e.relatedTarget)) setOpen(dd, false);
    });
    dd.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        setOpen(dd, false);
        btn.focus();
      }
    });
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-dropdown]")) closeAll();
  });

  /* Mobile drawer with focus containment */
  const drawer = document.querySelector("[data-drawer]");
  const openBtn = document.querySelector("[data-drawer-open]");
  const focusables = () => [...drawer.querySelectorAll("a[href], button, summary")].filter((el) => el.offsetParent !== null);
  const openDrawer = () => {
    drawer.hidden = false;
    openBtn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    focusables()[0]?.focus();
  };
  const closeDrawer = () => {
    drawer.hidden = true;
    openBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    openBtn.focus({ preventScroll: true });
  };
  openBtn?.addEventListener("click", openDrawer);
  drawer?.addEventListener("click", (e) => {
    if (e.target.closest("[data-drawer-close], [data-drawer-link]")) closeDrawer();
  });
  drawer?.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return closeDrawer();
    if (e.key !== "Tab") return;
    const items = focusables();
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
  window.matchMedia("(min-width: 1024px)").addEventListener("change", (e) => {
    if (e.matches && drawer && !drawer.hidden) closeDrawer();
  });

  /* Scroll reveal */
  const revealAll = (root = document) => root.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
  if (reducedMotion.matches || !("IntersectionObserver" in window)) {
    revealAll();
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
  }

  /* Collapsible card lists ("Show all") on small screens; delegated so HTMX swaps keep working */
  document.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-collapsible-toggle]");
    if (!toggle) return;
    const wrap = toggle.closest("[data-collapsible]");
    const open = !wrap.classList.contains("is-open");
    wrap.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.querySelector("[data-label-closed]").hidden = open;
    toggle.querySelector("[data-label-open]").hidden = !open;
    if (!open) wrap.scrollIntoView({ block: "start", behavior: reducedMotion.matches ? "auto" : "smooth" });
  });

  /* AI mentor sample prompts: reflect the selected prompt */
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-mentor-prompt]");
    if (!btn) return;
    document.querySelectorAll("[data-mentor-prompt]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  });

  /* Roadmap tabs: arrow-key navigation per WAI-ARIA tabs pattern */
  document.addEventListener("keydown", (e) => {
    const tab = e.target.closest("[data-roving-tabs] [role=tab]");
    if (!tab || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
    const tabs = [...tab.parentElement.querySelectorAll("[role=tab]")];
    let i = tabs.indexOf(tab);
    if (e.key === "ArrowRight") i = (i + 1) % tabs.length;
    if (e.key === "ArrowLeft") i = (i - 1 + tabs.length) % tabs.length;
    if (e.key === "Home") i = 0;
    if (e.key === "End") i = tabs.length - 1;
    e.preventDefault();
    tabs[i].focus();
    tabs[i].click();
  });

  document.body.addEventListener("htmx:afterSwap", (e) => {
    revealAll(e.detail.target.parentElement || document);
    if (e.detail.target.id === "roadmap-browser" || e.target.id === "roadmap-browser") {
      document.querySelector('#roadmap-browser [aria-selected="true"]')?.focus({ preventScroll: true });
    }
  });

  /* SOC preview: rotate clearly-labelled demo events */
  const stream = document.querySelector("[data-soc-stream]");
  if (stream && !reducedMotion.matches) {
    const demo = [
      ["CRIT", "text-zt-error", "Ransomware-like file renames", "FS-02"],
      ["HIGH", "text-zt-warn", "Suspicious LSASS access", "WS-031"],
      ["MED", "text-zt-neon", "Scheduled task created", "WS-014"],
      ["LOW", "text-zt-muted", "Unsigned binary executed", "WS-022"],
      ["HIGH", "text-zt-warn", "Impossible travel sign-in", "IdP"],
      ["MED", "text-zt-neon", "Outbound SMB to internet", "SRV-03"],
    ];
    let i = 0;
    let visible = false;
    new IntersectionObserver(([entry]) => (visible = entry.isIntersecting)).observe(stream);
    const pad = (n) => String(n).padStart(2, "0");
    setInterval(() => {
      if (!visible || document.hidden) return;
      const [sev, cls, text, host] = demo[i++ % demo.length];
      const d = new Date();
      const row = document.createElement("tr");
      row.className = "border-t border-zt-border animate-slide-in";
      row.innerHTML = `<td class="py-1.5 pr-3 text-zt-muted">${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}</td><td class="py-1.5 pr-3 ${cls}">${sev}</td><td class="py-1.5 pr-3"></td><td class="py-1.5"></td>`;
      row.children[2].textContent = text;
      row.children[3].textContent = host;
      stream.prepend(row);
      stream.lastElementChild?.remove();
    }, 2800);
  }

  /* Hero: sparse drifting data points on a canvas */
  const canvas = document.querySelector("[data-hero-canvas]");
  if (canvas && !reducedMotion.matches) {
    const ctx = canvas.getContext("2d");
    let w = 0, h = 0, dpr = 1, points = [], raf = 0, running = true;
    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.round(Math.min(46, (w * h) / 26000));
      points = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.18,
        vy: -0.08 - Math.random() * 0.22,
        r: Math.random() * 1.3 + 0.4,
        a: Math.random() * 0.5 + 0.2,
      }));
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (const p of points) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,255,117,${p.a})`;
        ctx.fill();
      }
      for (let i = 0; i < points.length; i++) {
        for (let j = i + 1; j < points.length; j++) {
          const a = points[i], b = points[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 110) {
            ctx.strokeStyle = `rgba(0,255,117,${0.08 * (1 - dist / 110)})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
      if (running) raf = requestAnimationFrame(draw);
    };
    resize();
    draw();
    window.addEventListener("resize", () => { cancelAnimationFrame(raf); resize(); if (running) draw(); }, { passive: true });
    new IntersectionObserver(([entry]) => {
      running = entry.isIntersecting;
      cancelAnimationFrame(raf);
      if (running) draw();
    }).observe(canvas);
  }
})();
