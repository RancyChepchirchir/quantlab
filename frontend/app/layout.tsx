import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import {
  QuantLabNav,
} from "@/components/layout/QuantLabNav";
import Link from "next/link";
import { QuantLabShell } from "@/components/layout/QuantLabShell";

export const metadata: Metadata = {
  title: "QuantLab",
  description:
    "Quantitative research workstation for derivatives pricing, volatility modelling, and computational finance.",
};

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});


<body>
  <QuantLabNav />
  <Link
  href="/research-lab"
  className="mt-6 inline-flex items-center gap-2 rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-300 transition hover:border-emerald-400 hover:text-emerald-400"
>
  Explore FDM vs PINN vs DeepONet
  <span>→</span>
</Link>

</body>

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <QuantLabShell>{children}</QuantLabShell>
      </body>
    </html>
  );
}
