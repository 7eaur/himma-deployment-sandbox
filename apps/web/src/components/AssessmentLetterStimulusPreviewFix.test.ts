import { extractAssessmentLetterStimulus } from "./AssessmentLetterStimulusPreviewFix";

describe("extractAssessmentLetterStimulus", () => {
  it("extracts only the displayed pretest letter from the legacy prose prompt", () => {
    expect(
      extractAssessmentLetterStimulus(
        "يظهر الحرف «م». اختر الشكل الآخر للحرف نفسه: مـ، سـ، لـ، بـ.",
      ),
    ).toBe("م");
  });

  it("keeps the equivalent posttest letter-form task symmetric", () => {
    expect(
      extractAssessmentLetterStimulus(
        "يظهر الحرف «س». اختر الشكل الآخر للحرف نفسه: سـ، شـ، صـ، نـ.",
      ),
    ).toBe("س");
  });

  it("does not rewrite unrelated assessment prompts", () => {
    expect(extractAssessmentLetterStimulus("اضغط على الحرف «ب»." )).toBeNull();
  });
});
