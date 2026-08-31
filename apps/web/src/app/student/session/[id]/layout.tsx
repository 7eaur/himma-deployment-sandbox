import TemporaryAudioSkipControl from "@/components/TemporaryAudioSkipControl";

export default function StudentAssessmentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <TemporaryAudioSkipControl mode="assessment" />
    </>
  );
}
