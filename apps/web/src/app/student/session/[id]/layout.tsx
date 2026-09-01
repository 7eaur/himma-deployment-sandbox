import AssessmentLetterStimulusPreviewFix from "@/components/AssessmentLetterStimulusPreviewFix";
import AssessmentExperienceEnhancer from "@/components/AssessmentExperienceEnhancer";
import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";
import "./assessment-polish.css";

export default function StudentAssessmentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <AssessmentLetterStimulusPreviewFix />
      <AssessmentExperienceEnhancer />
      <TemporaryAudioSkipControl mode="assessment" />
    </>
  );
}
