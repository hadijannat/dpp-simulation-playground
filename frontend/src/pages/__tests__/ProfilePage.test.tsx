import { render, screen, fireEvent } from "@testing-library/react";
import ProfilePage from "../ProfilePage";

/* ------------------------------------------------------------------ */
/*  Mocks                                                             */
/* ------------------------------------------------------------------ */

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("../../hooks/useAuth", () => ({
  useAuth: () => ({
    user: { preferred_username: "testuser" },
  }),
}));

vi.mock("../../stores/roleStore", () => ({
  useRoleStore: () => ({ role: "manufacturer" }),
}));

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

const STORAGE_KEY = "dpp-profile-preferences";

function renderPage() {
  return render(<ProfilePage />);
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders the profile heading", () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("profile");
  });

  it("displays user identity from useAuth", () => {
    renderPage();
    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("displays the active role", () => {
    renderPage();
    expect(screen.getByText("manufacturer")).toBeInTheDocument();
  });

  it("saves preferences to localStorage on button click", () => {
    renderPage();

    // Type into the organization field
    const orgInput = screen.getByRole("textbox", { name: "organization" });
    fireEvent.change(orgInput, { target: { value: "Acme Corp" } });

    // Click save
    fireEvent.click(screen.getByRole("button", { name: "savePreferences" }));

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.organization).toBe("Acme Corp");
  });

  it('shows "Saved at" pill after save', () => {
    renderPage();
    // Initially no pill
    expect(screen.queryByText(/savedAt/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "savePreferences" }));

    // After saving the pill should appear with the savedAt key
    expect(screen.getByText(/savedAt/)).toBeInTheDocument();
  });

  it("checkbox toggles onboardingCompleted", () => {
    renderPage();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    // Save and verify localStorage
    fireEvent.click(screen.getByRole("button", { name: "savePreferences" }));
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.onboardingCompleted).toBe(true);
  });

  it("loads existing preferences from localStorage", () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ organization: "PreLoaded Org", title: "Engineer", onboardingCompleted: true }),
    );
    renderPage();

    const orgInput = screen.getByRole("textbox", { name: "organization" }) as HTMLInputElement;
    expect(orgInput.value).toBe("PreLoaded Org");

    const titleInput = screen.getByRole("textbox", { name: "title" }) as HTMLInputElement;
    expect(titleInput.value).toBe("Engineer");

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });
});
