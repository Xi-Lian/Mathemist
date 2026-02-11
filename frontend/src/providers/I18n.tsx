"use client";

import React from "react";
import { useQueryState, parseAsString } from "nuqs";

export type Language = "zh-CN" | "en-US";

const translations = {
  "zh-CN": {
    openGitHubRepo: "打开 GitHub 仓库",
    newThread: "新对话线程",
    switchToPaper: "切换到纸张主题",
    switchToBasalt: "切换到深色主题",
    typeYourMessage: "输入你的消息...",
    uploadPdfOrImage: "上传 PDF 或图片",
    hideToolCalls: "隐藏工具调用",
    cancel: "取消",
    send: "发送",
    scrollToBottom: "滚动到底部",
    loading: "加载中...",
  },
  "en-US": {
    openGitHubRepo: "Open GitHub repo",
    newThread: "New thread",
    switchToPaper: "Switch to paper",
    switchToBasalt: "Switch to basalt",
    typeYourMessage: "Type your message...",
    uploadPdfOrImage: "Upload PDF or Image",
    hideToolCalls: "Hide Tool Calls",
    cancel: "Cancel",
    send: "Send",
    scrollToBottom: "Scroll to bottom",
    loading: "Loading...",
  },
} as const;

export type Translations = typeof translations[keyof typeof translations];

const I18nContext = React.createContext<{
  language: Language;
  setLanguage: (lang: Language) => void;
}>({
  language: "zh-CN",
  setLanguage: () => {},
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [urlLanguage, setUrlLanguage] = useQueryState(
    "lang",
    parseAsString.withDefault("")
  );

  const language: Language = (urlLanguage === "en-US" ? "en-US" : "zh-CN") as Language;

  const setLanguage = (lang: Language) => {
    setUrlLanguage(lang === "zh-CN" ? "" : lang);
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const { language, setLanguage } = React.useContext(I18nContext);
  return {
    t: translations[language],
    language,
    setLanguage,
  };
}
