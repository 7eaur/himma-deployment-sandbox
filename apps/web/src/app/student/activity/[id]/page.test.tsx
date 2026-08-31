import { render, screen } from "@testing-library/react";
import StudentActivityPage from "./page";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "42" }),
  useRouter: () => ({ push }),
}));

function response(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  window.sessionStorage.clear();
});

describe("Student activity page", () => {
  it("keeps reinforcement context without exposing internal task-design labels", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({
        session_id: 42,
        item: {
          id: 99,
          stable_key: "reinforcement-test",
          canonical_id: "L2-REIN-09",
          title: "تقوية: كلمات الشدة",
          level_id: 2,
          order_index: 9,
          interaction_type: "choose_one",
          kind: "reinforcement_activity",
          assets: [],
        },
        step: {
          id: 7,
          order_index: 1,
          prompt_text: "اختر الكلمة الصحيحة",
          instruction_text: "اختر الكلمة التي تحتوي على شدة",
          expected_reading_text: null,
          options: [
            { id: 1, text: "مُعَلِّم", order_index: 1 },
            { id: 2, text: "كتاب", order_index: 2 },
          ],
          assets: [],
          media_gaps: [],
        },
        attempts_used: 0,
        max_attempts: 2,
        retry: false,
        hint_available: false,
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

  it("points an L2 completion to L3 instead of advertising the posttest too early", async () => {
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
    expect(screen.getByText(/خطوتك التالية هي الطلاقة والفهم/)).toBeInTheDocument();
    expect(screen.queryByText(/الاختبار البعدي عندما يفتحه المشرف/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "الانتقال إلى خطوتي التالية" })).toBeEnabled();
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
    expect(screen.getByText(/الاختبار البعدي عندما يفتحه المشرف/)).toBeInTheDocument();
  });
});
