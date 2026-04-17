import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "StructureIQ — AEC Compliance Intelligence",
  description:
    "Grounded compliance analysis for construction documents against ADA, OSHA, IBC, and ASHRAE standards.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans bg-white text-ink antialiased`}>
        {children}
      </body>
    </html>
  );
}
