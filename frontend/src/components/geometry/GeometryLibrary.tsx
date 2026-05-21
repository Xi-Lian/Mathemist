"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { PRESETS_2D, PRESETS_3D, type GeometryMode } from "./geometry-presets";

interface GeoGebraApi {
  evalCommand: (command: string) => void;
  getAllObjectNames: () => string[];
  deleteObject: (name: string) => void;
}

interface GeoGebraAppletInstance {
  inject: (containerId: string) => void;
  getAppletObject: () => GeoGebraApi;
}

interface GeoGebraAppletConstructor {
  new (params: Record<string, unknown>, noPreview: boolean): GeoGebraAppletInstance;
}

declare global {
  interface Window {
    GGBApplet?: GeoGebraAppletConstructor;
  }
}

interface GeometryLibraryProps {
  initialMode?: GeometryMode;
  title?: string;
}

function withNoTrailingSlash(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export function GeometryLibrary({
  initialMode = "2d",
  title = "高中数学图形库",
}: GeometryLibraryProps) {
  const [mode, setMode] = useState<GeometryMode>(initialMode);
  const [scriptReady, setScriptReady] = useState(false);
  const [scriptError, setScriptError] = useState<string | null>(null);
  const [api, setApi] = useState<GeoGebraApi | null>(null);
  const uniqueId = useId();
  const containerId = `ggb-container-${uniqueId}`;
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (window.GGBApplet) {
      setScriptReady(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://www.geogebra.org/apps/deployggb.js";
    script.async = true;
    script.onload = () => {
      if (!mountedRef.current) return;
      setScriptReady(true);
      setScriptError(null);
    };
    script.onerror = () => {
      if (!mountedRef.current) return;
      setScriptError("GeoGebra 脚本加载失败，请检查网络后重试。");
    };

    document.head.appendChild(script);
    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  useEffect(() => {
    if (!scriptReady || !window.GGBApplet) return;

    const AppletCtor = window.GGBApplet;
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = "";
    setApi(null);

    const applet = new AppletCtor(
      {
        appName: mode === "2d" ? "classic" : "3d",
        width: Math.max(container.clientWidth, 900),
        height: 760,
        showToolBar: true,
        showAlgebraInput: true,
        showMenuBar: true,
        language: "zh-CN",
      },
      true,
    );

    applet.inject(containerId);

    const timer = window.setTimeout(() => {
      try {
        const appletApi = applet.getAppletObject();
        if (appletApi) setApi(appletApi);
      } catch {
        setScriptError("GeoGebra 初始化失败，请刷新页面重试。");
      }
    }, 1200);

    return () => {
      window.clearTimeout(timer);
    };
  }, [containerId, mode, scriptReady]);

  const clearAll = () => {
    if (!api) return;
    const objectNames = api.getAllObjectNames?.() ?? [];
    for (const objectName of objectNames) {
      api.deleteObject(objectName);
    }
  };

  const applyPreset = (commands: string[]) => {
    if (!api) return;
    clearAll();
    window.setTimeout(() => {
      for (const command of commands) {
        api.evalCommand(command);
      }
    }, 250);
  };

  const sections = mode === "2d" ? PRESETS_2D : PRESETS_3D;

  return (
    <div className="w-full rounded-xl border bg-background p-4">
      <h1 className="text-center text-2xl font-semibold">{title}</h1>

      <div className="mt-4 flex justify-center gap-2">
        <Button
          type="button"
          variant={mode === "2d" ? "default" : "outline"}
          onClick={() => setMode("2d")}
        >
          2D 模式
        </Button>
        <Button
          type="button"
          variant={mode === "3d" ? "default" : "outline"}
          onClick={() => setMode("3d")}
        >
          3D 模式
        </Button>
      </div>

      <div className="mt-4 space-y-4">
        {sections.map((section) => (
          <section
            key={section.title}
            className="rounded-lg border bg-muted/30 p-3"
          >
            <h2 className="mb-3 text-base font-medium">{section.title}</h2>
            <div className="flex flex-wrap gap-2">
              {section.presets.map((preset) => (
                <Button
                  key={preset.label}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset(preset.commands)}
                  disabled={!api}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="mt-4 flex justify-center">
        <Button
          type="button"
          variant="destructive"
          onClick={clearAll}
          disabled={!api}
        >
          清空画布
        </Button>
      </div>

      {scriptError && (
        <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {scriptError}
        </div>
      )}

      <div
        id={containerId}
        className="mt-4 h-[760px] w-full overflow-hidden rounded-md border bg-white"
      />

      {/* V48.7修复：使用静态文本避免 Hydration 不匹配 */}
      <p className="mt-2 text-center text-xs text-muted-foreground">
        依赖 GeoGebra 在线脚本：https://www.geogebra.org
      </p>
    </div>
  );
}
