import { render, screen } from "@testing-library/react";
import StudentPage from "./page";

const push = jest.fn();
const replace = jest.fn();
const refresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

function response(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Student page", () => {
  it("renders the student's first name and pretest before placement", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({
        id: 1,
        full_name: "طالب تجريبي",
        grade_level: 3,
        current_level: 1,
        posttest_enabled: false,
        next_action: "pretest",
        active_session: null,
      }))
      .mockResolvedValueOnce(response({
        pretest_completed: false,
        starting_level: null,
        current_level: 1,
        levels: [],
        learning_journey_completed: false,
        posttest_enabled: false,
        posttest_completed: false,
        posttest_ready: false,
      }))
      .mockResolvedValueOnce(response([]));

    render(<StudentPage />);
    expect(await screen.findByRole("heading", { name: "مرحبًا يا طالب" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ابدأ الاختبار" })).toBeEnabled();
    expect(screen.getByRole("heading", { name: "الاختبار القبلي" })).toBeInTheDocument();
    expect(screen.queryByTestId("level-journey")).not.toBeInTheDocument();
  });

  it("shows skipped, completed and active levels without claiming skipped work was completed", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({
        id: 1,
        full_name: "طالب تجريبي",
        grade_level: 3,
        current_level: 3,
        posttest_enabled: false,
        next_action: "learning",
        active_session: { id: 33, session_type: "core" },
      }))
      .mockResolvedValueOnce(response({
        available: true,
        level_id: 3,
        completed_items: 4,
        total_items: 10,
        completed: false,
        session_id: 33,
      }))
      .mockResolvedValueOnce(response({
        pretest_completed: true,
        starting_level: 2,
        current_level: 3,
        levels: [
          { level_id: 1, name: "الاستعداد للقراءة", state: "skipped", completed_items: 0, total_items: 10, session_id: null },
          { level_id: 2, name: "بناء الكلمة", state: "completed", completed_items: 10, total_items: 10, session_id: 22 },
          { level_id: 3, name: "الطلاقة والفهم", state: "active", completed_items: 4, total_items: 10, session_id: 33 },
        ],
        learning_journey_completed: false,
        posttest_enabled: false,
        posttest_completed: false,
        posttest_ready: false,
      }))
      .mockResolvedValueOnce(response([]));

    render(<StudentPage />);
    expect(await screen.findByTestId("level-journey")).toBeInTheDocument();
    expect(screen.getByText("بدأت من المستوى 2")).toBeInTheDocument();
    expect(screen.getByText("تجاوزته في الاختبار القبلي")).toBeInTheDocument();
    expect(screen.getByText("أنت هنا")).toBeInTheDocument();
    expect(screen.getByText("10 من 10 أنشطة أساسية")).toBeInTheDocument();
    expect(screen.getByText("4 من 10 أنشطة أساسية")).toBeInTheDocument();
  });
});
