import type { Metadata } from "next";
import { Archivo, Red_Hat_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";

const archivo = Archivo({ subsets: ["latin"], axes: ["wdth"], variable: "--font-archivo" });
const redHatMono = Red_Hat_Mono({ subsets: ["latin"], variable: "--font-red-hat-mono" });

export const metadata: Metadata = {
  title: "ProofSkill",
  description: "Verifiable training credentials: issue, share, and verify, with a labeled skill-fit recommendation.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${archivo.variable} ${redHatMono.variable}`}>
      <body>
        {/* Every portal page reads the URL and the per-tab session on the client, so it streams in. */}
        <Suspense fallback={null}>{children}</Suspense>
      </body>
    </html>
  );
}
