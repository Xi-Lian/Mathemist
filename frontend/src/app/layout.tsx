import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import React from "react";
import { ThemeProvider } from "@/providers/Theme";
import { I18nProvider } from "@/providers/I18n";
import { NuqsAdapter } from "nuqs/adapters/next/app";

const inter = Inter({
  subsets: ["latin"],
  preload: true,
  display: "swap",
});

export const metadata: Metadata = {
  title: "Mathemist",
  description: "Mathemist - AI Agent Platform",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning data-theme="paper">
      <body className={inter.className}>
        <ThemeProvider>
          <NuqsAdapter>
            <React.Suspense>
              <I18nProvider>{children}</I18nProvider>
            </React.Suspense>
          </NuqsAdapter>
        </ThemeProvider>
      </body>
    </html>
  );
}
