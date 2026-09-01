import AssessmentLetterStimulusPreviewFix from "@/components/AssessmentLetterStimulusPreviewFix";
import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";

export default function StudentAssessmentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <AssessmentLetterStimulusPreviewFix />
      <TemporaryAudioSkipControl mode="assessment" />
    </>
  );
}
