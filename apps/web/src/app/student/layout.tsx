import StudentExperienceEffects from "@/components/StudentExperienceEffects";

// Student routes render explicit state; this layout adds effects only and never patches task DOM.
export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <StudentExperienceEffects />
    </>
  );
}
