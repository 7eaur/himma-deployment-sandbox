"use client";

import Image from "next/image";
import Link from "next/link";
import { BookOpenCheck, Headphones, Mic2, Route, ShieldCheck, Sparkles } from "lucide-react";
import styles from "./landing.module.css";

export default function WelcomePage() {
  return (
    <div className={styles.page} dir="rtl">
      <header className={styles.header}>
        <Image src="/brand/logo-gradient.svg" alt="منصة هِمّة" width={132} height={44} priority />
        <nav className={styles.nav} aria-label="التنقل في الصفحة الرئيسية">
          <a href="#benefits">ما الذي ستتعلمه؟</a>
          <a href="#journey">رحلتك</a>
          <a href="#practice">كيف نتدرّب؟</a>
          <Link href="/student/login" className={styles.studentLink}>دخول الطالب</Link>
        </nav>
      </header>

      <main>
        <section className={styles.hero}>
          <div className={styles.copy}>
            <span className={styles.eyebrow}><span className={styles.eyebrowDot} /> رحلة قراءة تناسب مستواك خطوة بخطوة</span>
            <h1>اقرأ بثقة،<br /><span className={styles.accent}>وتقدّم مع هِمّة.</span></h1>
            <p className={styles.lead}>
              أنشطة قصيرة بالصوت والصورة والقراءة تساعدك على تمييز الحروف والكلمات،
              تدريب النطق والقراءة الجهرية، وفهم النصوص بطريقة واضحة وممتعة تناسب تقدمك.
            </p>
            <div className={styles.actions}>
              <Link href="/student/login" className={styles.primary}>
                <BookOpenCheck size={20} /> ابدأ رحلتي
              </Link>
              <a href="#journey" className={styles.quietLink}>كيف تعمل هِمّة؟</a>
            </div>
            <div className={styles.trust}>
              <span><i className={styles.dotBlue} /> مهمة واحدة في كل شاشة</span>
              <span><i className={styles.dotGreen} /> يتدرج المسار مع مستواك</span>
              <span><i className={styles.dotYellow} /> تشجيع بعد الإنجاز</span>
            </div>
          </div>

          <div className={styles.visual} aria-label="شخصية هِمّة التعليمية">
            <div className={`${styles.floatingCard} ${styles.cardTop}`}><strong>استمع ثم جرّب</strong><span>صوت وصورة وتعليمات بسيطة</span></div>
            <div className={`${styles.floatingCard} ${styles.cardBottom}`}><strong>تقدمك محفوظ</strong><span>نكمل دائمًا من آخر خطوة</span></div>
            <Image className={styles.character} src="/characters/girl/welcome.png" alt="شخصية هِمّة ترحب بالطالب" width={410} height={500} priority />
          </div>
        </section>

        <section id="benefits" className={styles.section}>
          <div className={styles.sectionInner}>
            <div className={styles.center}>
              <span className={styles.sectionBadge}>نتعلم بأكثر من طريقة</span>
              <h2>مهارات قراءة نبنيها معًا</h2>
              <p className={styles.sectionIntro}>لا نعتمد على شكل واحد من الأسئلة؛ كل مهارة تحصل على نشاط يناسبها بالصوت أو الصورة أو القراءة.</p>
            </div>
            <div className={styles.benefits}>
              <article className={styles.benefit}>
                <div className={`${styles.icon} ${styles.blue}`}><Headphones size={25} /></div>
                <h3>الاستماع والتمييز</h3>
                <p>استمع إلى حرف أو مقطع أو كلمة، ثم اختر الحرف أو الصورة الصحيحة من خيارات واضحة وكبيرة.</p>
              </article>
              <article className={styles.benefit}>
                <div className={`${styles.icon} ${styles.green}`}><Mic2 size={25} /></div>
                <h3>القراءة بصوت واضح</h3>
                <p>اقرأ الحروف والكلمات والجمل بصوت طبيعي، وسجّل قراءتك من داخل النشاط عندما تطلب منك هِمّة ذلك.</p>
              </article>
              <article className={styles.benefit}>
                <div className={`${styles.icon} ${styles.yellow}`}><Sparkles size={25} /></div>
                <h3>الفهم والتدرّج</h3>
                <p>رتّب الصور، ابنِ الكلمات، وافهم القصص القصيرة، ثم انتقل إلى ما يناسب تقدمك الحقيقي.</p>
              </article>
            </div>
          </div>
        </section>

        <section id="journey" className={`${styles.section} ${styles.alt}`}>
          <div className={styles.sectionInner}>
            <div className={styles.center}>
              <span className={styles.sectionBadge}>ثلاث خطوات واضحة</span>
              <h2>رحلتك في هِمّة</h2>
              <p className={styles.sectionIntro}>نبدأ بمعرفة مستواك، نتدرب على المهارات المناسبة، ثم نقيس التقدم في النهاية.</p>
            </div>
            <div className={styles.journey}>
              <article className={styles.journeyStep}><div className={styles.stepNumber}>١</div><h3>نعرف نقطة البداية</h3><p>اختبار قبلي متنوع يجمع بين الاختيار والصوت والصورة والقراءة.</p></article>
              <article className={styles.journeyStep}><div className={styles.stepNumber}>٢</div><h3>نتعلم ونتدرّب</h3><p>أنشطة قصيرة في مستويات القراءة، مع تقوية موجهة عندما تحتاج إليها.</p></article>
              <article className={styles.journeyStep}><div className={styles.stepNumber}>٣</div><h3>نقيس ما تحقق</h3><p>اختبار بعدي يقيس التقدم بعد إكمال المسار التعليمي.</p></article>
            </div>
          </div>
        </section>

        <section id="practice" className={styles.section}>
          <div className={styles.sectionInner}>
            <div className={styles.practice}>
              <div className={styles.practiceText}>
                <span className={styles.sectionBadge}>تجربة مصممة للطفل</span>
                <h2>تعليمات قليلة، تركيز أكبر</h2>
                <p>تظهر لك مهمة واحدة في كل مرة، مع أزرار كبيرة وصور واضحة وصوت يمكن إعادته. وعند القراءة الجهرية، يكون زر التسجيل كبيرًا وواضحًا لتعرف متى تبدأ ومتى تنتهي.</p>
                <div className={styles.skills}><span>الحروف</span><span>المقاطع</span><span>الكلمات</span><span>الجمل</span><span>الطلاقة</span><span>الفهم</span></div>
              </div>
              <div className={styles.practiceVisual}>
                <div className={styles.miniCard}><Headphones size={34} color="#347FD9" /><strong>استمع</strong><span>ثم اختر ما سمعت</span></div>
                <div className={styles.miniCard}><Mic2 size={34} color="#51B985" /><strong>اقرأ</strong><span>وسجّل قراءتك</span></div>
                <div className={styles.miniCard}><Route size={34} color="#D89E23" /><strong>رتّب</strong><span>الصور أو الكلمات</span></div>
                <div className={styles.miniCard}><ShieldCheck size={34} color="#347FD9" /><strong>تقدّم بأمان</strong><span>المحتوى محفوظ ومعتمد</span></div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.cta}>
          <div className={styles.ctaBox}>
            <div><h2>جاهز لبدء أول خطوة؟</h2><p>استخدم رمز الدخول الذي أعطاك إياه المشرف، وسنأخذك مباشرة إلى مسارك.</p></div>
            <Link href="/student/login" className={styles.primary}>دخول الطالب</Link>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={34} />
          <span>أتعلم، أتطور، أصل إلى القمة</span>
          <div className={styles.footerLinks}><Link href="/student/login">دخول الطالب</Link><Link href="/admin/login">دخول المشرف</Link></div>
        </div>
      </footer>
    </div>
  );
}
