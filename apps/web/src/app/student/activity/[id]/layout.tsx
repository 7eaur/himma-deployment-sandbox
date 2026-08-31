import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";
import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAdaptiveHoldOverlay />
      {children}
      <TemporaryAudioSkipControl mode="activity" />
    </>
  );
}
