import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";
import StudentAudioReviewOverlay from "@/components/StudentAudioReviewOverlay";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAudioReviewOverlay />
      <StudentAdaptiveHoldOverlay />
      {children}
    </>
  );
}
