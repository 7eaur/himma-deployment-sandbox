import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <style>{`
        [data-testid="activity-session"] [data-testid="student-audio-review-hold"] {
          display: none !important;
        }
        [data-testid="activity-session"] audio[controls] + div + p {
          display: none !important;
        }
      `}</style>
      <StudentAdaptiveHoldOverlay />
      {children}
    </>
  );
}
