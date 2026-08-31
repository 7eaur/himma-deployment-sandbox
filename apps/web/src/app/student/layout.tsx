import StudentExperienceEffects from "@/components/StudentExperienceEffects";
import "./student-experience.css";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <StudentExperienceEffects />
    </>
  );
}
