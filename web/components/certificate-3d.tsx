"use client";

import { useEffect, useRef, useState } from "react";

/** The certificate art as a live 3D object that floats up and down (three.js, loaded only here).
 * The static image shows until the first 3D frame is drawn, and stays if WebGL is unavailable. */
export function Certificate3D({ className, width, height }: { className: string; width: number; height: number }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [live, setLive] = useState(false);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let cleanup: (() => void) | undefined;
    let cancelled = false;
    import("./certificate-scene")
      .then(({ mountCertificate }) => {
        if (cancelled) return;
        try {
          cleanup = mountCertificate(host, () => setLive(true));
        } catch {
          // No WebGL: keep the image.
        }
      })
      .catch(() => {
        // The 3D chunk failed to load: keep the image.
      });
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, []);

  return (
    <div ref={hostRef} className={`${className} cert3d${live ? " cert3d--live" : ""}`} style={{ aspectRatio: `${width} / ${height}` }} aria-hidden="true">
      <img className="cert3d__image" src="/art/certificate.webp" alt="" width={width} height={height} />
    </div>
  );
}
