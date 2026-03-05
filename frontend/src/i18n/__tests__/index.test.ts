import i18n, {
  STORAGE_KEY,
  normalizeLanguage,
  resolveDefaultLanguage,
} from "../index";

describe("i18n bootstrap language resolution", () => {
  it("prefers a supported stored language", () => {
    expect(resolveDefaultLanguage("fr", "de-DE")).toBe("fr");
  });

  it("normalizes underscore and regional browser locales", () => {
    expect(resolveDefaultLanguage(null, "de_DE")).toBe("de");
    expect(resolveDefaultLanguage(null, "fr-CA")).toBe("fr");
  });

  it("falls back to english for unsupported languages", () => {
    expect(resolveDefaultLanguage(null, "es-ES")).toBe("en");
    expect(resolveDefaultLanguage("it", "de-DE")).toBe("en");
  });

  it("normalizes locale tokens consistently", () => {
    expect(normalizeLanguage("DE_de")).toBe("de");
    expect(normalizeLanguage(" fr-FR ")).toBe("fr");
    expect(normalizeLanguage(undefined)).toBe("");
  });
});

describe("i18n runtime behavior", () => {
  it("interpolates gamification toasts with punctuation and braces in name", async () => {
    await i18n.changeLanguage("en");
    const name = 'Alice, "A{B}" & Co.';
    const message = i18n.t("newAchievementToast", { ns: "gamification", name });
    expect(message).toBe(`New achievement unlocked: ${name}`);
  });

  it("persists selected language on language change", async () => {
    localStorage.removeItem(STORAGE_KEY);
    await i18n.changeLanguage("de");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("de");
  });
});
