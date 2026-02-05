import { render, screen } from "@testing-library/react";
import ValidationFeedback from "../ValidationFeedback";

describe("ValidationFeedback", () => {
  it("renders compliant status", () => {
    render(<ValidationFeedback result={{ status: "compliant" }} />);
    expect(screen.getByText("compliant")).toBeInTheDocument();
  });

  it("returns null for empty result", () => {
    const { container } = render(<ValidationFeedback result={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
