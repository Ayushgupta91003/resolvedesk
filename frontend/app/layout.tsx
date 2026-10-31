import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "ResolveDesk — support, with a little superpower", description: "A full-stack AI support workspace with evidence-backed investigations and human-approved actions." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
