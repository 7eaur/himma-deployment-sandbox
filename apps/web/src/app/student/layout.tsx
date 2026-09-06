import StudentAuthBoundary from "@/components/StudentAuthBoundary";
import StudentExperienceEffects from "@/components/StudentExperienceEffects";

// Student routes are protected before their content is rendered. The login page
// remains public, while protected routes are revalidated against /auth/me.
export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <StudentAuthBoundary>
      {children}
      <StudentExperienceEffects />
    </StudentAuthBoundary>
  );
}
