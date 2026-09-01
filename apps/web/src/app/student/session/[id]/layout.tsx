import AssessmentLetterStimulusPreviewFix from "@/components/AssessmentLetterStimulusPreviewFix";
import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";
import "./assessment-polish.css";

export default function StudentAssessmentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <AssessmentLetterStimulusPreviewFix />
      <TemporaryAudioSkipControl mode="assessment" />
    </>
  );
}
