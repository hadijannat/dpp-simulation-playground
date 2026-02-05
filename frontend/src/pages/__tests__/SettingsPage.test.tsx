import { render, screen, fireEvent, act } from "@testing-library/react";
import SettingsPage from "../SettingsPage";

/* ------------------------------------------------------------------ */
/*  Mocks                                                             */
/* ------------------------------------------------------------------ */

const mockChangeLanguage = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: mockChangeLanguage },
  }),
}));

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

const STORAGE_KEY = "dpp-ui-settings";

function renderPage() {
  return render(<SettingsPage />);
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the settings heading", () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("settings");
  });

  it("renders the settings description", () => {
    renderPage();
    expect(screen.getByText("settingsDescription")).toBeInTheDocument();
  });

  it("language select shows the current language", () => {
    renderPage();
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("en");
  });

  it("language change calls i18n.changeLanguage", () => {
    renderPage();
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "de" } });
    expect(mockChangeLanguage).toHaveBeenCalledWith("de");
  });

  it("reduce motion checkbox toggles the setting", () => {
    renderPage();
    const checkboxes = screen.getAllByRole("checkbox");
    // First checkbox is reduceMotion, second is compactDensity
    const reduceMotion = checkboxes[0];
    expect(reduceMotion).not.toBeChecked();

    fireEvent.click(reduceMotion);
    expect(reduceMotion).toBeChecked();
  });

  it("save button persists settings to localStorage", () => {
    renderPage();

    // Toggle reduce motion on
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    // Click save
    fireEvent.click(screen.getByRole("button", { name: "saveSettings" }));

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.reduceMotion).toBe(true);
    expect(stored.compactDensity).toBe(false);
  });

  it('"Settings saved" pill appears after save and disappears', () => {
    renderPage();

    // Initially no pill
    expect(screen.queryByText("settingsSaved")).not.toBeInTheDocument();

    // Click save
    fireEvent.click(screen.getByRole("button", { name: "saveSettings" }));

    // Pill should appear
    expect(screen.getByText("settingsSaved")).toBeInTheDocument();

    // Advance timers past the 1800ms timeout
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    // Pill should disappear
    expect(screen.queryByText("settingsSaved")).not.toBeInTheDocument();
  });

  it("loads existing settings from localStorage", () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ reduceMotion: true, compactDensity: true }),
    );
    renderPage();

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes[0]).toBeChecked(); // reduceMotion
    expect(checkboxes[1]).toBeChecked(); // compactDensity
  });
});
