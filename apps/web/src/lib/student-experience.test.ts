import { classifyStudentRecovery, shuffleForPresentation } from "./student-experience";

describe("student experience helpers", () => {
  test("routes authentication failures back through login", () => {
    expect(classifyStudentRecovery(401, "غير مصرح")).toBe("login");
  });

  test("routes dead or expired student resources back to the dashboard", () => {
    expect(classifyStudentRecovery(404, "الجلسة غير موجودة")).toBe("dashboard");
    expect(classifyStudentRecovery(410, "انتهت الجلسة")).toBe("dashboard");
    expect(classifyStudentRecovery(409, "الجلسة انتهت")).toBe("dashboard");
    expect(classifyStudentRecovery(403, "غير متاح لهذا الطالب")).toBe("dashboard");
  });

  test("keeps transient failures retryable", () => {
    expect(classifyStudentRecovery(500, "تعذر الاتصال بالخدمة")).toBe("retry");
    expect(classifyStudentRecovery(409, "حاول مرة أخرى")).toBe("retry");
  });

  test("shuffles a presentation without mutating or losing choices", () => {
    const source = [1, 2, 3, 4, 5];
    const result = shuffleForPresentation(source);
    expect(result).not.toBe(source);
    expect(source).toEqual([1, 2, 3, 4, 5]);
    expect([...result].sort((a, b) => a - b)).toEqual(source);
  });
});
