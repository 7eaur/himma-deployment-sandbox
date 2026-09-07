import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: [
      "src/app/student/session/**/page.tsx",
      "src/app/student/activity/**/page.tsx",
    ],
    rules: {
      // These two student runtimes intentionally keep one short-lived Audio
      // element per prompt and chain multi-asset prompts through onended.
      // Navigation, submit, payload change and unmount all clear that handler
      // before the callback can survive into another question/activity.
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
