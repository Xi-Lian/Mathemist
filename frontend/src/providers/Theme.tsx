"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ReactNode } from "react";

const themes = ["paper", "basalt"] as const;

export type ThemeName = (typeof themes)[number];

export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="data-theme"
      defaultTheme="paper"
      disableTransitionOnChange
      enableSystem={false}
      themes={[...themes]}
    >
      {children}
    </NextThemesProvider>
  );
}
