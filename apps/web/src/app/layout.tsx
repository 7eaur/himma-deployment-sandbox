import type { Metadata } from "next";
import "./tailwind.css";
import "./globals.css";
import "./accessibility.css";
import "./student-image-options.css";
import { ScrollAnimator } from "@/components/ScrollAnimator";

export const metadata: Metadata = {
  title: "منصة همة التعليمية",
  description: "أتعلم، أتطور، أصل إلى القمة",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <ScrollAnimator />
        {children}
      </body>
    </html>
  );
}
