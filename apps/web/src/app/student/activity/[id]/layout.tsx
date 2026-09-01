import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";
import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";
import LearningExperienceEnhancer from "@/components/LearningExperienceEnhancer";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAdaptiveHoldOverlay />
      {children}
      <LearningExperienceEnhancer />
      <TemporaryAudioSkipControl mode="activity" />
    </>
  );
}
