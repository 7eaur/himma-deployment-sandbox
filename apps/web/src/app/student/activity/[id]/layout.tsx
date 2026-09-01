import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";
import LearningExperienceEnhancer from "@/components/LearningExperienceEnhancer";
import "./learning-experience-polish.css";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAdaptiveHoldOverlay />
      {children}
      <LearningExperienceEnhancer />
    </>
  );
}
