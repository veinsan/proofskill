import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Red_Hat_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta" });
const redHatMono = Red_Hat_Mono({ subsets: ["latin"], variable: "--font-red-hat-mono" });

export const metadata: Metadata = {
  title: "ProofSkill",
  description: "Verifiable training credentials: issue, share, and verify, with a labeled skill-fit recommendation.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${jakarta.variable} ${redHatMono.variable}`}>
      <body>
        <div className="backdrop" aria-hidden="true">
          <img className="backdrop__a" src="/art/shapes.webp" alt="" width={460} height={449} />
          <img className="backdrop__b" src="/art/arch.webp" alt="" width={400} height={266} />
          <img className="backdrop__c" src="/art/tiles.webp" alt="" width={240} height={209} />
        </div>
        {/* Every portal page reads the URL and the per-tab session on the client, so it streams in. */}
        <Suspense fallback={null}>{children}</Suspense>
      </body>
    </html>
  );
}
