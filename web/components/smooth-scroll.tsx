"use client";

import Lenis from "lenis";
import { useEffect } from "react";

// Scroll feel for every page (approved 2026-11-20, after jasonedward.dev): Lenis eases the scroll,
// `[data-parallax]` elements drift at their own speed against it, and `.reveal` blocks rise in once
// as they enter the viewport (the stagger is in CSS). Under prefers-reduced-motion none of this
// runs: the browser scrolls natively and every block is simply there.

const RESCAN_MS = 300;
const GIVE_UP_MS = 3000; // after this, reveal blocks React has not claimed yet are shown anyway

/** Page content streams in and hydrates after this layout component, so an element is touched only
 * once React has hydrated it; changing a server-rendered attribute earlier is a hydration mismatch. */
function hydrated(el: Element): boolean {
  return Object.keys(el).some((key) => key.startsWith("__reactFiber$"));
}

export function SmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const root = document.documentElement;
    root.classList.add("motion");

    const lenis = new Lenis({
      autoRaf: true,
      lerp: 0.09,
      anchors: { offset: -96 }, // clear the sticky top bar
      allowNestedScroll: true, // text areas, tables, and menus keep their own scroll
      prevent: (node) => node.nodeName === "DIALOG",
    });

    // Parallax: each element moves by how far the page has scrolled past the point where it rests,
    // times its speed (positive lags behind the page, negative runs ahead). An element in the first
    // screen rests at scroll 0, so the page opens exactly as designed; one further down rests when it
    // reaches the viewport's middle. The offset is written as --py on the element itself, so only its
    // own subtree recalculates.
    let parallax: { el: HTMLElement; speed: number; py: number }[] = [];
    const backdrop = document.querySelector<HTMLElement>(".backdrop");
    const update = () => {
      const middle = window.innerHeight / 2;
      const scrolled = window.scrollY;
      for (const item of parallax) {
        const rect = item.el.getBoundingClientRect();
        const center = rect.top + rect.height / 2 - item.py; // where it would sit without parallax
        if (center < -window.innerHeight || center > window.innerHeight * 2) continue;
        const docCenter = center + scrolled;
        const pivot = docCenter < window.innerHeight ? 0 : docCenter - middle;
        const py = Math.round((scrolled - pivot) * item.speed * 10) / 10;
        if (py === item.py) continue;
        item.py = py;
        item.el.style.setProperty("--py", `${py}px`);
      }
      // The fixed backdrop shapes slide a little against the scroll, capped so they never leave.
      backdrop?.style.setProperty("--sy", `${Math.min(Math.round(scrolled), 2400)}`);
    };
    lenis.on("scroll", update);

    // Reveal: once, when a block is a little way into the viewport.
    const reveal = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-in");
          reveal.unobserve(entry.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 },
    );

    const tracked = new WeakSet<Element>();
    let started = performance.now();
    let rescan = 0;
    const scan = () => {
      rescan = 0;
      const force = performance.now() - started > GIVE_UP_MS;
      let waiting = false;
      parallax = parallax.filter((item) => item.el.isConnected);
      document.querySelectorAll<HTMLElement>("[data-parallax], .reveal").forEach((el) => {
        if (tracked.has(el)) return;
        if (!hydrated(el) && !force) {
          waiting = true;
          return;
        }
        tracked.add(el);
        if (el.dataset.parallax) parallax.push({ el, speed: Number(el.dataset.parallax) || 0, py: 0 });
        if (el.classList.contains("reveal")) reveal.observe(el);
      });
      update();
      if (waiting) rescan = window.setTimeout(scan, RESCAN_MS);
    };

    // New pages render on the client and stream in: scan again whenever the DOM changes.
    const mutations = new MutationObserver(() => {
      if (rescan) return;
      started = performance.now();
      rescan = window.setTimeout(scan, 0);
    });
    mutations.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("resize", update);
    scan();

    return () => {
      window.clearTimeout(rescan);
      mutations.disconnect();
      reveal.disconnect();
      window.removeEventListener("resize", update);
      lenis.destroy();
      root.classList.remove("motion");
    };
  }, []);

  return null;
}
