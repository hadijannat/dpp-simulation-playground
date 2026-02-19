import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import JourneyPage from "../JourneyPage";

/* ------------------------------------------------------------------ */
/*  Mocks                                                             */
/* ------------------------------------------------------------------ */

// react-i18next: simple passthrough t(key) => key
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

// roleStore
const mockRole = "manufacturer";
vi.mock("../../stores/roleStore", () => ({
  useRoleStore: () => ({ role: mockRole }),
}));

// sessionStore
const mockSetCurrentJourneyRunId = vi.fn();
let mockCurrentJourneyRunId: string | undefined = undefined;

vi.mock("../../stores/sessionStore", () => ({
  useSessionStore: (selector?: (state: Record<string, unknown>) => unknown) => {
    const state = {
      currentJourneyRunId: mockCurrentJourneyRunId,
      setCurrentJourneyRunId: mockSetCurrentJourneyRunId,
    };
    return selector ? selector(state) : state;
  },
}));

// Journey hooks
const mockCreateRunMutateAsync = vi.fn().mockResolvedValue({ id: "run-123" });
const mockExecuteStepMutateAsync = vi.fn().mockResolvedValue({});
const mockRunCheckMutateAsync = vi.fn().mockResolvedValue({ id: "comp-1" });
const mockApplyFixMutateAsync = vi.fn().mockResolvedValue({});
const mockCsatMutateAsync = vi.fn().mockResolvedValue({ created_at: "2025-01-01" });

vi.mock("../../hooks/useJourney", () => ({
  useJourneyRun: () => ({
    run: { data: null, refetch: vi.fn() },
    createRun: { mutateAsync: mockCreateRunMutateAsync },
    executeStep: { mutateAsync: mockExecuteStepMutateAsync },
  }),
  useJourneyCompliance: () => ({
    complianceRun: { data: null, refetch: vi.fn() },
    runCheck: { mutateAsync: mockRunCheckMutateAsync },
    applyFix: { mutateAsync: mockApplyFixMutateAsync },
  }),
  useDigitalTwin: () => ({ data: null }),
  useDigitalTwinHistory: () => ({ data: null, isLoading: false }),
  useDigitalTwinDiff: () => ({ data: null, isLoading: false }),
  useCsatFeedback: () => ({ mutateAsync: mockCsatMutateAsync, data: null }),
}));

// Template hook
let mockTemplateData: Record<string, unknown> | undefined = undefined;

vi.mock("../../hooks/useJourneyTemplate", () => ({
  useJourneyTemplate: () => ({
    data: mockTemplateData,
  }),
}));

// Platform V2 service (used by useMutation directly in the page)
vi.mock("../../services/platformV2Service", () => ({
  createNegotiation: vi.fn().mockResolvedValue({ id: "neg-1" }),
  createTransfer: vi.fn().mockResolvedValue({ id: "tx-1" }),
  runNegotiationAction: vi.fn().mockResolvedValue({}),
  runTransferAction: vi.fn().mockResolvedValue({}),
}));

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderPage() {
  const qc = createQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <JourneyPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("JourneyPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCurrentJourneyRunId = undefined;
    mockTemplateData = undefined;
  });

  it("renders fallback title from t() when no template is loaded", () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("title");
  });

  it("renders the template name when template data is available", () => {
    mockTemplateData = {
      name: "Manufacturer Core E2E",
      description: "Full journey",
      steps: [],
    };
    renderPage();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Manufacturer Core E2E");
  });

  it("shows Start Journey button that calls createRun", async () => {
    renderPage();
    const startBtn = screen.getByRole("button", { name: "startJourney" });
    expect(startBtn).toBeInTheDocument();
    fireEvent.click(startBtn);
    // createRun.mutateAsync is called inside startRun()
    await vi.waitFor(() => {
      expect(mockCreateRunMutateAsync).toHaveBeenCalledTimes(1);
    });
  });

  it("shows Continue Journey button when currentJourneyRunId exists", () => {
    mockCurrentJourneyRunId = "existing-run-999";
    renderPage();
    expect(screen.getByRole("button", { name: "continueJourney" })).toBeInTheDocument();
  });

  it("does not show Continue Journey button when currentJourneyRunId is undefined", () => {
    mockCurrentJourneyRunId = undefined;
    renderPage();
    expect(screen.queryByRole("button", { name: "continueJourney" })).not.toBeInTheDocument();
  });

  it("renders Open Payload Editor button", () => {
    renderPage();
    const editorBtn = screen.getByRole("button", { name: "openPayloadEditor" });
    expect(editorBtn).toBeInTheDocument();
  });

  it("toggles editor visibility when Open Payload Editor is clicked", () => {
    renderPage();
    // The bottom-sheet editor overlay should not be present initially
    expect(screen.queryByRole("presentation")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "openPayloadEditor" }));

    // After clicking, the overlay should appear
    expect(screen.getByRole("presentation")).toBeInTheDocument();
  });

  it("renders step buttons from template steps", () => {
    mockTemplateData = {
      name: "Template",
      description: "desc",
      steps: [
        { step_key: "create-dpp", title: "Create DPP Shell", action: "aas.create", order_index: 0, help_text: "", default_payload: {} },
        { step_key: "check-compliance", title: "Run Compliance", action: "compliance.check", order_index: 1, help_text: "", default_payload: {} },
      ],
    };
    renderPage();
    expect(screen.getByRole("button", { name: "1. Create DPP Shell" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2. Run Compliance" })).toBeInTheDocument();
  });

  it("renders fallback step buttons when template has no steps", () => {
    mockTemplateData = undefined;
    renderPage();
    // Fallback buttons use translated keys
    expect(screen.getByRole("button", { name: /createDpp/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /runCompliance/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /runNegotiation/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /runTransfer/ })).toBeInTheDocument();
  });
});
