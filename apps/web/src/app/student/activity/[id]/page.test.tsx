import { render, screen } from "@testing-library/react";
import StudentActivityPage from "./page";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "42" }),
  useRouter: () => ({ push }),
}));

function response(body: unknown) {
  return { ok: true, json: async () => body };
}

beforeEach(() => {
  jest.clearAllMocks();
  window.sessionStorage.clear();
});

describe("Student activity page", () => {
  it("renders only the structured learning projection and never leaks legacy prompt options", async () => {
    global.fetch = jest
      .fn()
      // Execution endpoint: presentation data here is deliberately legacy/noisy and must be ignored.
      .mockResolvedValueOnce(response({
        session_id: 42,
        item: { id: 99, interaction_type: "listen_choose_one" },
        step: { id: 7, prompt_text: "سُ؛ سَ/سِ/سُ" },
      }))
      // Authoritative student-facing payload.
      .mockResolvedValueOnce(response({
        version: "HIMMA-LEARNING-2026-09-01-R2",
        session_id: 42,
        level_id: 2,
        item_id: 99,
        stable_key: "L2-CORE-01",
        kind: "core_activity",
        interaction_type: "listen_choose_one",
        round: {
          round_number: 3,
          round_total: 5,
          skill: "تمييز الحركات القصيرة",
          encouragement: "أحسنت، أنت تتقدم بشكل جميل!",
          hint: "ركّز على الحركة المسموعة في المقطع.",
          question_text: "استمع إلى المقطع، ثم اختر المقطع الذي سمعته.",
          instruction_text: "اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.",
          stimulus_text: "",
        },
        retry: false,
        attempts_used: 0,
        max_attempts: 2,
        step: {
          id: 7,
          order_index: 3,
          expected_reading_text: null,
          options: [
            { id: 1, text: "سَ", order_index: 1 },
            { id: 2, text: "سِ", order_index: 2 },
            { id: 3, text: "سُ", order_index: 3 },
          ],
          assets: [{ asset_id: "audio-s", asset_type: "audio", url: "/api/media/audio-s" }],
          media_gaps: [],
        },
        assets: [],
      }))
      .mockResolvedValueOnce(response({
        session_id: 42,
        status: "in_progress",
        level_id: 2,
        completed_items: 2,
        total_items: 10,
        elapsed_seconds: 30,
      }));

    render(<StudentActivityPage />);

    expect(await screen.findByRole("heading", { name: "استمع إلى المقطع، ثم اختر المقطع الذي سمعته." })).toBeInTheDocument();
    expect(screen.getByText("اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.")).toBeInTheDocument();
    expect(screen.getByText("أحسنت، أنت تتقدم بشكل جميل!")).toBeInTheDocument();
    expect(screen.queryByText("سُ؛ سَ/سِ/سُ")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "سَ" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "سِ" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "سُ" })).toBeInTheDocument();
    expect(screen.getByText("الجولة 3 من 5")).toBeInTheDocument();
  });

  it("shows the hint instead of encouragement when the current round is a retry", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(response({ session_id: 42, item: { id: 99 }, step: { id: 7 } }))
      .mockResolvedValueOnce(response({
        version: "HIMMA-LEARNING-2026-09-01-R2",
        session_id: 42,
        level_id: 1,
        item_id: 99,
        stable_key: "L1-CORE-01",
        kind: "core_activity",
        interaction_type: "choose_one",
        round: {
          round_number: 1,
          round_total: 5,
          skill: "الانتباه والتمييز البصري",
          encouragement: "ممتاز، أنت قادر عليها!",
          hint: "ركّز على شكل الحرف وعدد النقاط ومكانها.",
          question_text: "ابحث عن الحرف المطلوب، ثم اضغط عليه.",
          instruction_text: "انظر إلى الحرف المطلوب، ثم اختره من الحروف المعروضة.",
          stimulus_text: "ب",
        },
        retry: true,
        attempts_used: 1,
        max_attempts: 2,
        step: {
          id: 7,
          order_index: 1,
          expected_reading_text: null,
          options: [
            { id: 1, text: "ت", order_index: 1 },
            { id: 2, text: "ب", order_index: 2 },
          ],
          assets: [],
          media_gaps: [],
        },
        assets: [],
      }))
      .mockResolvedValueOnce(response({ session_id: 42, status: "in_progress", level_id: 1, completed_items: 0, total_items: 10, elapsed_seconds: 4 }));

    render(<StudentActivityPage />);

    expect(await screen.findByText("ركّز على شكل الحرف وعدد النقاط ومكانها.")).toBeInTheDocument();
    expect(screen.queryByText("ممتاز، أنت قادر عليها!")).not.toBeInTheDocument();
    expect(screen.getByText("ب", { selector: "div" })).toBeInTheDocument();
  });

  it("renders a completed learning session without requesting a presentation payload", async () => {
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

    expect(await screen.findByRole("heading", { name: "أحسنت، أكملت أنشطة المستوى!" })).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});
