import { render, screen } from "@testing-library/react";
import StudentActivityPage from "./page";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "42" }),
  useRouter: () => ({ push, replace: jest.fn() }),
}));

function response(body: unknown) {
  return { ok: true, json: async () => body };
}

beforeEach(() => {
  jest.clearAllMocks();
  window.sessionStorage.clear();
});

describe("Student activity page", () => {
  it("keeps reinforcement context without exposing internal task-design labels", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({ id: 99, stable_key: "reinforcement-test" }))
      .mockResolvedValueOnce(response({
        version: "HIMMA-STUDENT-EXPERIENCE-2.0",
        session_id: 42,
        level_id: 2,
        item_id: 99,
        stable_key: "reinforcement-test",
        kind: "reinforcement_activity",
        interaction_type: "choose_one",
        round: {
          round_number: 1,
          round_total: 5,
          skill: "الشدة",
          encouragement: "أنت تتقدم بشكل رائع.",
          hint: "ركّز على الحرف المشدد.",
          question_text: "أي كلمة تحتوي على شدة؟",
          instruction_text: "اختر الكلمة التي تحتوي على شدة",
          stimulus_text: "",
        },
        retry: false,
        attempts_used: 0,
        max_attempts: 2,
        step: {
          id: 7,
          order_index: 1,
          expected_reading_text: null,
          required_selection_count: 1,
          options: [
            { id: 1, text: "مُعَلِّم", order_index: 1 },
            { id: 2, text: "كتاب", order_index: 2 },
          ],
          assets: [],
          media_gaps: [],
        },
        assets: [],
      }))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "in_progress",
        level_id: 2,
        completed_items: 5,
        total_items: 10,
        elapsed_seconds: 30,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByTestId("student-task-instruction")).toHaveTextContent("اختر الكلمة التي تحتوي على شدة");
    expect(screen.getByTestId("reinforcement-intro")).toHaveTextContent("بعد إتقانها تعود إلى نشاطك الأساسي");
    expect(screen.queryByText("مهمة واحدة في كل مرة", { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByTestId("reinforcement-badge")).not.toBeInTheDocument();
    expect(screen.getByTestId("activity-session")).toHaveAttribute("data-activity-kind", "reinforcement");
  });

  it("returns an L2 completion to the authoritative student journey instead of hardcoding the next route", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(null))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "completed",
        level_id: 2,
        completed_items: 10,
        total_items: 10,
        elapsed_seconds: 180,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByRole("heading", { name: "أحسنت، أكملت بناء الكلمة" })).toBeInTheDocument();
    expect(screen.getByText(/ارجع إلى مسارك لتظهر لك الخطوة التالية المناسبة/)).toBeInTheDocument();
    expect(screen.queryByText((content, element) => element?.tagName === "P" && content.includes("البعدي"))).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "العودة إلى مساري" })).toBeEnabled();
  });

  it("mentions the posttest only after completing L3", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response(null))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "completed",
        level_id: 3,
        completed_items: 10,
        total_items: 10,
        elapsed_seconds: 220,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByRole("heading", { name: "أحسنت، أكملت المستوى الثالث" })).toBeInTheDocument();
    expect(screen.getByText((content, element) => element?.tagName === "P" && content.includes("البعدي"))).toBeInTheDocument();
  });
});
