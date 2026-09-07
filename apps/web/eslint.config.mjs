import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: [
      "src/app/student/session/[id]/page.tsx",
      "src/app/student/activity/[id]/page.tsx",
    ],
    rules: {
      // These two pages intentionally keep one short-lived Audio element per
      // prompt and chain multi-asset prompts through onended. Every navigation,
      // submit and unmount path clears that handler before the payload changes,
      // so the self-recursive callback cannot survive into a later render.
      "react-hooks/immutability": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
