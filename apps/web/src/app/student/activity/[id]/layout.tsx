import StudentAdaptiveHoldOverlay from "@/components/StudentAdaptiveHoldOverlay";

export default function StudentActivityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <StudentAdaptiveHoldOverlay />
      {children}
    </>
  );
}
