import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enCommon from "./locales/en/common.json";
import enSimulation from "./locales/en/simulation.json";
import enCompliance from "./locales/en/compliance.json";
import enEdc from "./locales/en/edc.json";
import enGamification from "./locales/en/gamification.json";

import deCommon from "./locales/de/common.json";
import deSimulation from "./locales/de/simulation.json";
import deCompliance from "./locales/de/compliance.json";
import deEdc from "./locales/de/edc.json";
import deGamification from "./locales/de/gamification.json";

import frCommon from "./locales/fr/common.json";
import frSimulation from "./locales/fr/simulation.json";
import frCompliance from "./locales/fr/compliance.json";
import frEdc from "./locales/fr/edc.json";
import frGamification from "./locales/fr/gamification.json";

const STORAGE_KEY = "dpp-locale";

const defaultLanguage =
  localStorage.getItem(STORAGE_KEY) ||
  (navigator.language || "en").split("-")[0] ||
  "en";

i18n.use(initReactI18next).init({
  lng: ["en", "de", "fr"].includes(defaultLanguage) ? defaultLanguage : "en",
  fallbackLng: "en",
  defaultNS: "common",
  ns: ["common", "simulation", "compliance", "edc", "gamification"],
  interpolation: {
    escapeValue: false,
  },
  resources: {
    en: {
      common: enCommon,
      simulation: enSimulation,
      compliance: enCompliance,
      edc: enEdc,
      gamification: enGamification,
    },
    de: {
      common: deCommon,
      simulation: deSimulation,
      compliance: deCompliance,
      edc: deEdc,
      gamification: deGamification,
    },
    fr: {
      common: frCommon,
      simulation: frSimulation,
      compliance: frCompliance,
      edc: frEdc,
      gamification: frGamification,
    },
  },
});

i18n.on("languageChanged", (language) => {
  localStorage.setItem(STORAGE_KEY, language);
});

export default i18n;
