import { useRoleStore, getSelectedRole } from "../roleStore";

/* ------------------------------------------------------------------ */
/*  Tests                                                             */
/* ------------------------------------------------------------------ */

describe("roleStore", () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset the store to the default by setting role back to what localStorage provides
    // (which after clear is nothing, so the default "manufacturer" applies)
    useRoleStore.setState({ role: localStorage.getItem("dpp-role") || "manufacturer" });
  });

  it('initial role is "manufacturer" when localStorage is empty', () => {
    const { role } = useRoleStore.getState();
    expect(role).toBe("manufacturer");
  });

  it("setRole changes the role in the store", () => {
    useRoleStore.getState().setRole("recycler");
    expect(useRoleStore.getState().role).toBe("recycler");
  });

  it("setRole persists the role to localStorage", () => {
    useRoleStore.getState().setRole("auditor");
    expect(localStorage.getItem("dpp-role")).toBe("auditor");
  });

  it("getSelectedRole returns the current role", () => {
    useRoleStore.getState().setRole("supplier");
    expect(getSelectedRole()).toBe("supplier");
  });

  it("role reads from localStorage when store is initialized", () => {
    localStorage.setItem("dpp-role", "consumer");
    // Re-initialize by setting state as if the store constructor ran
    useRoleStore.setState({ role: localStorage.getItem("dpp-role") || "manufacturer" });
    expect(useRoleStore.getState().role).toBe("consumer");
  });

  it("setRole updates the role multiple times", () => {
    useRoleStore.getState().setRole("manufacturer");
    expect(useRoleStore.getState().role).toBe("manufacturer");

    useRoleStore.getState().setRole("recycler");
    expect(useRoleStore.getState().role).toBe("recycler");

    useRoleStore.getState().setRole("auditor");
    expect(useRoleStore.getState().role).toBe("auditor");
    expect(localStorage.getItem("dpp-role")).toBe("auditor");
  });
});
