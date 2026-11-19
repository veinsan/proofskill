"use client";

import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { DownloadIcon } from "./icons";

const OPTIONS = { type: "svg" as const, margin: 1, errorCorrectionLevel: "M" as const, color: { dark: "#0f1b3dff", light: "#ffffffff" } };

/** Renders the share URL as a QR code in the browser; the token never leaves this page for a QR service. */
export function ShareQr({ url, linkId }: { url: string; linkId: string }) {
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    QRCode.toString(url, OPTIONS).then((markup) => {
      if (live) setSvg(markup);
    });
    return () => {
      live = false;
    };
  }, [url]);

  function download() {
    if (!svg) return;
    const href = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `proofskill-${linkId}.svg`;
    anchor.click();
    URL.revokeObjectURL(href);
  }

  return (
    <div className="stack" style={{ gap: "var(--s-sm)" }}>
      {/* Markup produced locally by the qrcode library from our own URL. */}
      <div className="qr" role="img" aria-label={`QR code for ${url}`} dangerouslySetInnerHTML={svg ? { __html: svg } : undefined} />
      <button className="btn btn--quiet" type="button" onClick={download} disabled={!svg}>
        <DownloadIcon />
        Download QR
      </button>
    </div>
  );
}
