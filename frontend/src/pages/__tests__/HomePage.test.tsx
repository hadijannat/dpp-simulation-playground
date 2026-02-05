import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HomePage from "../HomePage";

describe("HomePage", () => {
  it("renders the manufacturer journey call to action", () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "Start Manufacturer Journey" })).toBeInTheDocument();
  });
});
