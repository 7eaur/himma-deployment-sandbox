import { render, screen } from "@testing-library/react";
import Home from "./page";

describe("Home page", () => {
  it("renders the child-focused welcome heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /اقرأ بثقة/ })).toBeInTheDocument();
    expect(screen.getByText(/أنشطة قصيرة بالصوت والصورة والقراءة/)).toBeInTheDocument();
  });

  it("offers student login", () => {
    render(<Home />);
    const links = screen.getAllByRole("link", { name: /دخول الطالب/ });
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => link.getAttribute("href") === "/student/login")).toBe(true);
  });
});
