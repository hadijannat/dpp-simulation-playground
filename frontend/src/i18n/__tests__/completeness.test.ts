/* ------------------------------------------------------------------ */
/*  Import all locale JSON files using the same paths as i18n/index.ts */
/* ------------------------------------------------------------------ */

// English
import enCommon from "../locales/en/common.json";
import enSimulation from "../locales/en/simulation.json";
import enCompliance from "../locales/en/compliance.json";
import enEdc from "../locales/en/edc.json";
import enGamification from "../locales/en/gamification.json";
import enJourney from "../locales/en/journey.json";

// German
import deCommon from "../locales/de/common.json";
import deSimulation from "../locales/de/simulation.json";
import deCompliance from "../locales/de/compliance.json";
import deEdc from "../locales/de/edc.json";
import deGamification from "../locales/de/gamification.json";
import deJourney from "../locales/de/journey.json";

// French
import frCommon from "../locales/fr/common.json";
import frSimulation from "../locales/fr/simulation.json";
import frCompliance from "../locales/fr/compliance.json";
import frEdc from "../locales/fr/edc.json";
import frGamification from "../locales/fr/gamification.json";
import frJourney from "../locales/fr/journey.json";

/* ------------------------------------------------------------------ */
/*  Organize by language and namespace                                */
/* ------------------------------------------------------------------ */

const NAMESPACES = ["common", "simulation", "compliance", "edc", "gamification", "journey"] as const;

const en: Record<string, Record<string, string>> = {
  common: enCommon,
  simulation: enSimulation,
  compliance: enCompliance,
  edc: enEdc,
  gamification: enGamification,
  journey: enJourney,
};

const de: Record<string, Record<string, string>> = {
  common: deCommon,
  simulation: deSimulation,
  compliance: deCompliance,
  edc: deEdc,
  gamification: deGamification,
  journey: deJourney,
};

const fr: Record<string, Record<string, string>> = {
  common: frCommon,
  simulation: frSimulation,
  compliance: frCompliance,
  edc: frEdc,
  gamification: frGamification,
  journey: frJourney,
};

/* ------------------------------------------------------------------ */
/*  Helper                                                            */
/* ------------------------------------------------------------------ */

function getKeys(obj: Record<string, unknown>): string[] {
  return Object.keys(obj).sort();
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("i18n locale completeness", () => {
  describe("all namespaces exist in en, de, and fr", () => {
    for (const ns of NAMESPACES) {
      it(`namespace "${ns}" exists in English`, () => {
        expect(en[ns]).toBeDefined();
        expect(Object.keys(en[ns]).length).toBeGreaterThan(0);
      });

      it(`namespace "${ns}" exists in German`, () => {
        expect(de[ns]).toBeDefined();
        expect(Object.keys(de[ns]).length).toBeGreaterThan(0);
      });

      it(`namespace "${ns}" exists in French`, () => {
        expect(fr[ns]).toBeDefined();
        expect(Object.keys(fr[ns]).length).toBeGreaterThan(0);
      });
    }
  });

  describe("all English keys exist in German", () => {
    for (const ns of NAMESPACES) {
      it(`de/${ns} contains all keys from en/${ns}`, () => {
        const enKeys = getKeys(en[ns]);
        const deKeys = getKeys(de[ns]);
        const missingInDe = enKeys.filter((key) => !deKeys.includes(key));
        expect(missingInDe).toEqual([]);
      });
    }
  });

  describe("all English keys exist in French", () => {
    for (const ns of NAMESPACES) {
      it(`fr/${ns} contains all keys from en/${ns}`, () => {
        const enKeys = getKeys(en[ns]);
        const frKeys = getKeys(fr[ns]);
        const missingInFr = enKeys.filter((key) => !frKeys.includes(key));
        expect(missingInFr).toEqual([]);
      });
    }
  });

  describe("no extra keys in German that do not exist in English", () => {
    for (const ns of NAMESPACES) {
      it(`de/${ns} has no extra keys beyond en/${ns}`, () => {
        const enKeys = getKeys(en[ns]);
        const deKeys = getKeys(de[ns]);
        const extraInDe = deKeys.filter((key) => !enKeys.includes(key));
        expect(extraInDe).toEqual([]);
      });
    }
  });

  describe("no extra keys in French that do not exist in English", () => {
    for (const ns of NAMESPACES) {
      it(`fr/${ns} has no extra keys beyond en/${ns}`, () => {
        const enKeys = getKeys(en[ns]);
        const frKeys = getKeys(fr[ns]);
        const extraInFr = frKeys.filter((key) => !enKeys.includes(key));
        expect(extraInFr).toEqual([]);
      });
    }
  });

  describe("key counts match across all languages", () => {
    for (const ns of NAMESPACES) {
      it(`en/${ns}, de/${ns}, and fr/${ns} have the same number of keys`, () => {
        const enCount = Object.keys(en[ns]).length;
        const deCount = Object.keys(de[ns]).length;
        const frCount = Object.keys(fr[ns]).length;
        expect(deCount).toBe(enCount);
        expect(frCount).toBe(enCount);
      });
    }
  });
});
