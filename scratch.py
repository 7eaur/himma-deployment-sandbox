import os, codecs

workspace = r'e:\مشروع منصه همه\Himma_Unified_Repository_v1.1_FINAL'

def write_file(rel_path, content):
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with codecs.open(full_path, 'w', 'utf-8') as f:
        f.write(content)

def append_file(rel_path, content):
    full_path = os.path.join(workspace, rel_path)
    with codecs.open(full_path, 'a', 'utf-8') as f:
        f.write(content)

append_file('apps/web/src/app/globals.css', '''
/* KEYFRAMES */
@keyframes fadeUp { from{opacity:0;transform:translateY(28px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-14px)} }
@keyframes floatAlt { 0%,100%{transform:translateY(0) rotate(-1deg)} 50%{transform:translateY(-10px) rotate(1deg)} }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(0.85)} }
@keyframes pulse-ring { 0%{transform:scale(0.85);opacity:0.5} 100%{transform:scale(1.6);opacity:0} }
@keyframes orbit-cw { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@keyframes orbit-ccw { from{transform:rotate(0deg)} to{transform:rotate(-360deg)} }
@keyframes shimmer-btn { 0%{background-position:200% center} 100%{background-position:-200% center} }
@keyframes slide-in-up { from{opacity:0;transform:translateY(40px)} to{opacity:1;transform:translateY(0)} }
@keyframes pop { 0%{transform:scale(0.7);opacity:0} 70%{transform:scale(1.08)} 100%{transform:scale(1);opacity:1} }
@keyframes bounce-gentle { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }

/* Root */
.welcome-root { min-height:100vh; overflow-x:hidden; position:relative; font-family:var(--font-student); background:var(--color-bg); }

/* Ambient bg shapes */
.amb-shape { position:fixed; border-radius:50%; pointer-events:none; z-index:0; }
.amb-1 { top:-15%; right:-8%; width:600px; height:600px; background:radial-gradient(circle,rgba(52,127,217,0.09),transparent 70%); filter:blur(60px); }
.amb-2 { bottom:5%; left:-10%; width:500px; height:500px; background:radial-gradient(circle,rgba(81,185,133,0.08),transparent 70%); filter:blur(50px); }
.amb-3 { top:40%; left:35%; width:350px; height:350px; background:radial-gradient(circle,rgba(255,200,87,0.06),transparent 70%); filter:blur(45px); }

/* Header */
.w-header { position:sticky; top:0; z-index:100; background:rgba(247,251,255,0.88); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); border-bottom:1px solid rgba(220,232,242,0.6); display:flex; align-items:center; justify-content:space-between; padding:0 48px; height:68px; }
.w-nav { display:flex; align-items:center; gap:8px; }
.w-nav-link { color:var(--color-navy); font-size:0.875rem; font-weight:500; text-decoration:none; padding:8px 12px; border-radius:var(--r-md); opacity:0.7; transition:opacity 0.2s,background 0.2s; }
.w-nav-link:hover { opacity:1; background:rgba(52,127,217,0.06); }
.w-nav-cta { background:var(--color-primary); color:white; font-size:0.875rem; font-weight:700; font-family:var(--font-student); padding:9px 22px; border-radius:var(--r-full); text-decoration:none; transition:transform 0.2s,box-shadow 0.2s; box-shadow:0 3px 12px rgba(52,127,217,0.3); display:inline-flex; align-items:center; gap:6px; }
.w-nav-cta:hover { transform:translateY(-1px); box-shadow:0 5px 20px rgba(52,127,217,0.4); }

/* Hero section */
.w-hero { display:grid; grid-template-columns:1fr 1fr; align-items:center; min-height:calc(100vh - 68px); padding:60px 80px; gap:40px; position:relative; z-index:1; }
.w-hero-copy { animation:fadeUp 0.7s ease 0.1s both; }
.w-eyebrow { display:inline-flex; align-items:center; gap:8px; background:rgba(52,127,217,0.08); color:var(--color-primary); border-radius:var(--r-full); padding:6px 16px; font-size:0.8rem; font-weight:600; margin-bottom:20px; border:1px solid rgba(52,127,217,0.15); }
.w-eyebrow-dot { width:7px; height:7px; background:var(--color-primary); border-radius:50%; animation:pulse-dot 2s ease-in-out infinite; }
.w-h1 { font-size:clamp(2.4rem,4.5vw,3.8rem); font-weight:800; line-height:1.12; color:var(--color-navy); margin:0 0 18px; }
.w-h1-accent { color:var(--color-primary); display:block; }
.w-lead { font-size:1.1rem; color:var(--color-muted); max-width:480px; line-height:1.75; margin-bottom:36px; }

/* CTA buttons */
.w-btn-primary { background:var(--color-primary); color:white; border-radius:var(--r-full); padding:16px 40px; font-size:1.05rem; font-weight:700; font-family:var(--font-student); display:inline-flex; align-items:center; gap:10px; text-decoration:none; box-shadow:0 4px 24px rgba(52,127,217,0.35); transition:transform 0.2s,box-shadow 0.2s; border:none; cursor:pointer; }
.w-btn-primary:hover { transform:translateY(-3px); box-shadow:0 8px 32px rgba(52,127,217,0.45); }
.w-btn-primary:active { transform:translateY(-1px); }
.w-btn-arrow { transform:scaleX(-1); display:inline-block; opacity:0.8; }
.w-btn-lg { padding:20px 52px; font-size:1.15rem; }

.w-actions { display:flex; flex-wrap:wrap; gap:14px; align-items:center; margin-bottom:40px; }

.w-trust { display:flex; flex-wrap:wrap; gap:20px; align-items:center; }
.w-trust-item { display:flex; align-items:center; gap:8px; font-size:0.85rem; color:var(--color-muted); font-weight:500; }
.w-trust-icon { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.w-trust-blue { background:var(--color-primary); }
.w-trust-green { background:var(--color-green); }
.w-trust-yellow { background:var(--color-yellow); }

/* Hero visual */
.w-hero-visual { position:relative; display:flex; align-items:flex-end; justify-content:center; min-height:500px; }
.w-orbit { position:absolute; border-radius:50%; border:1.5px dashed rgba(52,127,217,0.15); top:50%; left:50%; transform-origin:center; }
.w-orbit-1 { width:300px; height:300px; margin-top:-150px; margin-right:-150px; animation:orbit-cw 35s linear infinite; }
.w-orbit-2 { width:440px; height:440px; margin-top:-220px; margin-right:-220px; animation:orbit-ccw 55s linear infinite; }
.w-char { position:absolute; bottom:0; image-rendering:auto; }
.w-char-boy { right:8%; animation:float 4.5s ease-in-out infinite; z-index:2; }
.w-char-girl { left:8%; animation:float 4.5s ease-in-out infinite 2s; z-index:2; }
.w-floor { position:absolute; bottom:0; width:80%; height:3px; background:linear-gradient(to left,transparent,rgba(52,127,217,0.12),transparent); border-radius:var(--r-full); left:10%; }

/* Sections */
.w-section { padding:96px 0; position:relative; overflow:hidden; }
.w-section-alt { background:white; }
.w-section-inner { max-width:1100px; margin:0 auto; padding:0 48px; }
.w-section-badge { display:inline-flex; align-items:center; gap:8px; background:rgba(52,127,217,0.07); color:var(--color-primary); border-radius:var(--r-full); padding:5px 14px; font-size:0.78rem; font-weight:600; margin-bottom:10px; }
.w-h2 { font-size:clamp(1.9rem,3vw,2.6rem); font-weight:800; color:var(--color-navy); margin:0 0 14px; }
.w-section-lead { font-size:1.05rem; color:var(--color-muted); max-width:600px; line-height:1.75; margin-bottom:56px; }

/* About cards */
.w-cards-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; }
.w-about-card { background:white; border-radius:var(--r-lg); padding:36px 28px; box-shadow:var(--shadow-md); transition:transform 0.25s,box-shadow 0.25s; border-top:4px solid transparent; }
.w-about-card:hover { transform:translateY(-6px); box-shadow:var(--shadow-lg); }
.w-card-blue { border-top-color:var(--color-primary); }
.w-card-green { border-top-color:var(--color-green); }
.w-card-yellow { border-top-color:var(--color-yellow); }
.w-about-icon { margin-bottom:20px; }
.w-about-card h3 { font-size:1.1rem; font-weight:700; color:var(--color-navy); margin:0 0 10px; }
.w-about-card p { font-size:0.9rem; color:var(--color-muted); line-height:1.65; margin:0; }

/* Steps */
.w-steps { display:flex; flex-direction:column; }
.w-step { display:flex; align-items:flex-start; gap:20px; padding:24px 0; }
.w-step-line { width:2px; height:28px; background:rgba(52,127,217,0.2); margin-right:24px; /* RTL: align with circle center */ }
.w-step-num { width:48px; height:48px; background:var(--color-primary); color:white; border-radius:50%; font-size:1.2rem; font-weight:700; font-family:var(--font-student); display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 4px 12px rgba(52,127,217,0.3); }
.w-step-body h3 { font-size:1.05rem; font-weight:700; color:var(--color-navy); margin:0 0 6px; padding-top:10px; }
.w-step-body p { color:var(--color-muted); font-size:0.9rem; line-height:1.65; margin:0; }

/* Features */
.w-features { display:grid; grid-template-columns:repeat(2,1fr); gap:24px; }
.w-feature { padding:28px; border:1.5px solid var(--color-border); border-radius:var(--r-lg); background:white; transition:transform 0.2s,box-shadow 0.2s,border-color 0.2s; }
.w-feature:hover { transform:translateY(-4px); box-shadow:var(--shadow-md); border-color:rgba(52,127,217,0.3); }
.w-feature-icon { width:54px; height:54px; border-radius:var(--r-lg); display:flex; align-items:center; justify-content:center; margin-bottom:18px; }
.w-feature h3 { font-size:1rem; font-weight:700; color:var(--color-navy); margin:0 0 8px; }
.w-feature p { color:var(--color-muted); font-size:0.875rem; line-height:1.65; margin:0; }

/* CTA band */
.w-cta { background:linear-gradient(135deg,#20364D 0%,#1a4f8a 60%,#347FD9 100%); padding:0; margin:60px 48px; border-radius:var(--r-2xl); overflow:hidden; position:relative; }
.w-cta::before { content:''; position:absolute; top:-40%; right:-10%; width:400px; height:400px; background:radial-gradient(circle,rgba(255,255,255,0.05),transparent 70%); border-radius:50%; }
.w-cta-inner { max-width:900px; margin:0 auto; padding:64px 80px; display:flex; align-items:center; gap:60px; position:relative; }
.w-cta-char { flex-shrink:0; animation:float 3.5s ease-in-out infinite; filter:drop-shadow(0 12px 24px rgba(0,0,0,0.2)); }
.w-cta-h2 { font-size:clamp(1.6rem,2.5vw,2.2rem); font-weight:800; color:white; margin:0 0 10px; font-family:var(--font-student); }
.w-cta-p { color:rgba(255,255,255,0.78); font-size:1rem; line-height:1.6; margin:0 0 28px; }
.w-cta .w-btn-primary { background:white; color:var(--color-primary); box-shadow:0 4px 20px rgba(0,0,0,0.15); }
.w-cta .w-btn-primary:hover { background:rgba(255,255,255,0.95); }

/* Footer */
.w-footer { padding:40px 48px; border-top:1px solid var(--color-border); }
.w-footer-inner { max-width:700px; margin:0 auto; text-align:center; }
.w-footer-copy { color:var(--color-muted); font-size:0.85rem; margin:14px 0 4px; }
.w-footer-tagline { color:var(--color-primary); font-size:0.8rem; font-weight:600; margin:0; }

/* Scroll animations */
.animate-on-scroll { opacity:0; transform:translateY(24px); transition:opacity 0.6s ease,transform 0.6s ease; }
.animate-on-scroll.animated { opacity:1; transform:translateY(0); }
.animate-delay-1 { transition-delay:0.1s; }
.animate-delay-2 { transition-delay:0.2s; }
.animate-delay-3 { transition-delay:0.3s; }

/* Responsive welcome */
@media(max-width:900px) {
  .w-hero { grid-template-columns:1fr; padding:40px 24px; min-height:auto; }
  .w-hero-visual { min-height:300px; margin-top:24px; }
  .w-char-boy { width:160px; }
  .w-char-girl { width:145px; }
  .w-cards-grid { grid-template-columns:1fr; }
  .w-features { grid-template-columns:1fr; }
  .w-cta { margin:40px 16px; }
  .w-cta-inner { flex-direction:column; padding:48px 32px; gap:32px; }
  .w-cta-char { width:100px; }
  .w-header { padding:0 20px; }
  .w-section-inner { padding:0 24px; }
  .w-nav-link { display:none; }
}
@media(max-width:600px) {
  .w-hero { padding:32px 16px; }
  .w-hero-visual { display:none; }
  .w-section { padding:60px 0; }
}

/* Override sidebar styles */
.sidebar-layout { display:flex; min-height:100vh; }
.sidebar { width:260px; min-height:100vh; background:white; border-left:1px solid var(--color-border); display:flex; flex-direction:column; flex-shrink:0; box-shadow:2px 0 12px rgba(32,54,77,0.06); /* RTL: shadow goes right */  }
.sidebar-brand { height:76px; display:flex; align-items:center; justify-content:center; border-bottom:1px solid var(--color-border); padding:0 20px; background:linear-gradient(to bottom,white,var(--color-bg)); flex-shrink:0; }
.sidebar-nav { flex:1; padding:12px 10px; display:flex; flex-direction:column; gap:2px; overflow-y:auto; }
.sidebar-nav-item { display:flex; align-items:center; gap:12px; padding:12px 14px; border-radius:10px; text-decoration:none; font-size:0.875rem; font-weight:500; color:var(--color-muted); transition:all 0.18s; cursor:pointer; border:none; background:transparent; width:100%; text-align:right; }
.sidebar-nav-item:hover { background:var(--color-bg); color:var(--color-navy); }
.sidebar-nav-item.active { background:var(--color-primary); color:white; box-shadow:0 3px 10px rgba(52,127,217,0.3); }
.sidebar-nav-item.active svg { color:white; }
.sidebar-nav-icon { width:20px; height:20px; flex-shrink:0; }
.sidebar-footer { padding:12px 10px 20px; border-top:1px solid var(--color-border); }
.sidebar-user { display:flex; align-items:center; gap:10px; padding:10px 12px; margin-bottom:6px; border-radius:10px; background:var(--color-bg); }
.sidebar-avatar { width:36px; height:36px; background:var(--color-primary); color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.85rem; font-weight:700; flex-shrink:0; }
.sidebar-user-name { font-size:0.82rem; font-weight:600; color:var(--color-navy); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sidebar-logout { display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:10px; color:#DC2626; font-size:0.875rem; font-weight:500; background:transparent; border:none; cursor:pointer; width:100%; transition:background 0.18s,color 0.18s; text-align:right; }
.sidebar-logout:hover { background:#FEE2E2; }
.sidebar-content { flex:1; padding:32px; background:var(--color-bg); display:flex; flex-direction:column; min-width:0; overflow-x:hidden; }

/* Admin dashboard cards */
.stat-card { background:white; border-radius:var(--r-lg); padding:24px 28px; box-shadow:var(--shadow-sm); display:flex; align-items:center; gap:18px; border:1.5px solid var(--color-border); transition:transform 0.2s,box-shadow 0.2s; }
.stat-card:hover { transform:translateY(-3px); box-shadow:var(--shadow-md); }
.stat-icon { width:52px; height:52px; border-radius:var(--r-lg); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.stat-label { font-size:0.8rem; color:var(--color-muted); margin-bottom:4px; font-weight:500; }
.stat-value { font-size:2rem; font-weight:800; color:var(--color-navy); line-height:1; }

/* Admin login split layout */
.admin-login-root { display:flex; min-height:100vh; }
.admin-login-brand { width:420px; flex-shrink:0; background:linear-gradient(160deg,#20364D 0%,#1a4a80 50%,#347FD9 100%); display:flex; flex-direction:column; align-items:center; justify-content:center; padding:60px 48px; text-align:center; position:relative; overflow:hidden; }
.admin-login-brand::before { content:""; position:absolute; top:-20%; right:-20%; width:300px; height:300px; background:rgba(255,255,255,0.04); border-radius:50%; }
.admin-login-brand::after { content:""; position:absolute; bottom:-10%; left:-10%; width:250px; height:250px; background:rgba(255,255,255,0.03); border-radius:50%; }
.admin-brand-title { color:white; font-size:1.5rem; font-weight:800; margin:20px 0 8px; font-family:var(--font-researcher); }
.admin-brand-sub { color:rgba(255,255,255,0.7); font-size:0.9rem; line-height:1.6; margin:0; }
.admin-brand-char { margin-top:40px; animation:float 4s ease-in-out infinite; filter:drop-shadow(0 16px 32px rgba(0,0,0,0.25)); position:relative; z-index:1; }
.admin-brand-tagline { margin-top:20px; color:rgba(255,255,255,0.5); font-size:0.78rem; font-style:italic; }
.admin-login-form-wrap { flex:1; display:flex; align-items:center; justify-content:center; padding:40px; background:white; }
.admin-login-form-box { width:100%; max-width:420px; }
.admin-login-form-box h1 { font-size:1.6rem; font-weight:700; color:var(--color-navy); margin:0 0 8px; }
.admin-login-form-box p { color:var(--color-muted); font-size:0.9rem; margin:0 0 32px; }
.admin-login-hint { margin-top:24px; text-align:center; font-size:0.78rem; color:var(--color-muted); opacity:0.7; }

/* Student login split layout */
.student-login-root { min-height:100vh; display:flex; align-items:center; justify-content:center; background:var(--color-bg); padding:20px; position:relative; font-family:var(--font-student); overflow:hidden; }
.student-login-card { background:white; border-radius:var(--r-2xl); padding:52px 48px; width:100%; max-width:440px; box-shadow:var(--shadow-lg); animation:pop 0.5s ease both; text-align:center; position:relative; z-index:1; }
.student-login-logo { margin-bottom:20px; }
.student-login-title { font-size:1.8rem; font-weight:800; color:var(--color-navy); margin:0 0 8px; }
.student-login-sub { color:var(--color-muted); font-size:0.95rem; margin:0 0 32px; }
.student-login-code-input { width:100%; border:3px solid var(--color-border); border-radius:var(--r-xl); padding:18px 20px; font-size:2.2rem; font-family:"IBM Plex Mono","Courier New",monospace; font-weight:700; color:var(--color-primary); text-align:center; letter-spacing:0.15em; text-transform:uppercase; transition:border-color 0.2s,box-shadow 0.2s; background:var(--color-bg); }
.student-login-code-input:focus { outline:none; border-color:var(--color-primary); box-shadow:0 0 0 4px rgba(52,127,217,0.12); background:white; }
.student-login-btn { width:100%; margin-top:20px; padding:18px; font-size:1.15rem; font-weight:800; font-family:var(--font-student); background:var(--color-primary); color:white; border:none; border-radius:var(--r-xl); cursor:pointer; box-shadow:0 4px 20px rgba(52,127,217,0.35); transition:transform 0.2s,box-shadow 0.2s; }
.student-login-btn:hover:not(:disabled) { transform:translateY(-2px); box-shadow:0 8px 28px rgba(52,127,217,0.45); }
.student-login-btn:disabled { opacity:0.6; cursor:not-allowed; }
.student-login-amb-1 { position:fixed; top:-15%; left:-10%; width:450px; height:450px; background:radial-gradient(circle,rgba(52,127,217,0.07),transparent); border-radius:50%; pointer-events:none; filter:blur(50px); }
.student-login-amb-2 { position:fixed; bottom:-15%; right:-10%; width:400px; height:400px; background:radial-gradient(circle,rgba(81,185,133,0.07),transparent); border-radius:50%; pointer-events:none; filter:blur(45px); }

/* Student home page */
.student-home-root { min-height:100vh; background:var(--color-bg); display:flex; flex-direction:column; font-family:var(--font-student); position:relative; overflow:hidden; }
.student-home-header { display:flex; align-items:center; justify-content:space-between; padding:18px 28px; background:white; border-bottom:1px solid var(--color-border); box-shadow:var(--shadow-sm); position:relative; z-index:10; }
.student-logout-btn { display:flex; align-items:center; gap:6px; color:var(--color-muted); background:transparent; border:1.5px solid var(--color-border); border-radius:var(--r-full); padding:8px 16px; font-size:0.85rem; font-weight:600; font-family:var(--font-student); cursor:pointer; transition:all 0.2s; }
.student-logout-btn:hover { color:#DC2626; border-color:#DC2626; background:#FEF2F2; }
.student-home-main { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:40px 24px; text-align:center; position:relative; z-index:1; }
.student-home-char { animation:float 4s ease-in-out infinite; filter:drop-shadow(0 20px 40px rgba(52,127,217,0.15)); margin-bottom:24px; }
.student-greeting { font-size:clamp(1.8rem,4vw,2.6rem); font-weight:800; color:var(--color-navy); margin:0 0 8px; }
.student-subtitle { font-size:1rem; color:var(--color-muted); margin:0 0 40px; line-height:1.6; max-width:380px; }
.student-start-btn { font-size:1.3rem; font-weight:800; font-family:var(--font-student); background:var(--color-primary); color:white; border:none; border-radius:var(--r-full); padding:20px 56px; cursor:pointer; box-shadow:0 6px 28px rgba(52,127,217,0.4); transition:transform 0.2s,box-shadow 0.2s; position:relative; }
.student-start-btn:hover:not(:disabled) { transform:translateY(-3px); box-shadow:0 12px 40px rgba(52,127,217,0.5); }
.student-start-btn::after { content:""; position:absolute; inset:-4px; border-radius:var(--r-full); border:2px solid rgba(52,127,217,0.25); animation:pulse-ring 2.5s ease-out infinite; }
.student-grade-badge { display:inline-block; background:rgba(81,185,133,0.1); color:var(--color-green); border-radius:var(--r-full); padding:6px 16px; font-size:0.85rem; font-weight:700; margin-bottom:24px; border:1px solid rgba(81,185,133,0.2); }

@media(max-width:600px) {
  .admin-login-brand { display:none; }
  .admin-login-form-wrap { padding:24px; }
  .student-login-card { padding:36px 24px; }
  .student-login-code-input { font-size:1.6rem; }
  .sidebar-layout { flex-direction:column; }
  .sidebar { width:100%; min-height:auto; }
}
''')

write_file('apps/web/src/app/admin/login/page.tsx', '''"use client";

import { useState } from "react";
import Image from "next/image";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        window.location.href = "/admin";
      } else {
        const data = await res.json();
        setError(data.detail || "Invalid credentials");
      }
    } catch (err) {
      setError("An error occurred during login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-login-root" dir="rtl">
      <div className="admin-login-brand">
        <Image src="/brand/logo-white.svg" alt="Himma Logo" width={140} height={48} />
        <h2 className="admin-brand-title">تسجيل دخول الباحثة</h2>
        <p className="admin-brand-sub">لوحة التحكم ومتابعة الطلاب</p>
        <Image src="/characters/girl/welcome.png" alt="Character" width={160} height={200} className="admin-brand-char" priority />
        <p className="admin-brand-tagline">أتعلم، أتطور، أصل إلى القمة</p>
      </div>

      <div className="admin-login-form-wrap">
        <div className="admin-login-form-box">
          <div className="md:hidden flex justify-center mb-8">
            <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={140} height={48} />
          </div>
          <h1>مرحباً بك مجدداً</h1>
          <p>أدخلي بياناتك للوصول إلى لوحة التحكم</p>

          {error && (
            <div data-testid="error-message" className="alert-error text-center mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-navy font-medium mb-2">اسم المستخدم</label>
              <input
                type="text"
                className="input-field"
                data-testid="input-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                dir="ltr"
              />
            </div>
            
            <div>
              <label className="block text-navy font-medium mb-2">كلمة المرور</label>
              <input
                type="password"
                className="input-field"
                data-testid="input-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                dir="ltr"
              />
            </div>
            
            <button
              type="submit"
              className="btn-primary w-full mt-6"
              data-testid="login-submit"
              disabled={isLoading}
            >
              {isLoading ? <span className="spinner"></span> : "دخول"}
            </button>
          </form>
          <p className="admin-login-hint">الوصول مصرح للباحثين والإداريين فقط</p>
        </div>
      </div>
    </div>
  );
}
''')

write_file('apps/web/src/app/student/login/page.tsx', '''"use client";

import { useState } from "react";
import Image from "next/image";

export default function StudentLogin() {
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/student-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_code: accessCode }),
      });

      if (res.ok) {
        window.location.href = "/student";
      } else {
        const data = await res.json();
        setError(data.detail || "رمز الدخول غير صحيح");
      }
    } catch (err) {
      setError("حدث خطأ أثناء تسجيل الدخول");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccessCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (val.length > 3) {
      val = val.slice(0, 3) + "-" + val.slice(3, 7);
    }
    setAccessCode(val);
  };

  return (
    <div className="student-login-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <div className="student-login-card">
        <div className="flex justify-center student-login-logo">
          <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={180} height={60} />
        </div>
        
        <div className="flex justify-center mb-6">
          <Image 
            src="/characters/boy/welcome.png" 
            alt="Welcome" 
            width={140} 
            height={180}
            className="drop-shadow-md hover:scale-105 transition-transform duration-300" 
          />
        </div>
        
        <h1 className="student-login-title">أهلاً بك يا بطل!</h1>
        <p className="student-login-sub">أدخل رمز الدخول السري لنبدأ التعلم معاً</p>
        
        {error && (
          <div data-testid="error-message" className="alert-error text-center mb-6 font-bold">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="student-login-code-input mb-4"
            data-testid="input-access-code"
            value={accessCode}
            onChange={handleAccessCodeChange}
            placeholder="ABC-1234"
            maxLength={8}
            required
            dir="ltr"
          />
          
          <button
            type="submit"
            className="student-login-btn"
            data-testid="student-login-submit"
            disabled={isLoading || accessCode.length < 8}
          >
            {isLoading ? <span className="spinner mx-auto border-4"></span> : "يلا نبدأ!"}
          </button>
        </form>
      </div>
    </div>
  );
}
''')

write_file('apps/web/src/app/student/page.tsx', '''"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

interface StudentMe {
  id: string;
  full_name: string;
  grade_level: number;
}

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingSession, setStartingSession] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const meRes = await fetch("/api/me");
        if (meRes.ok) {
          setStudent(await meRes.json());
        }
      } catch (err) {
        console.error("Error fetching student info", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleStartAssessment = async () => {
    setStartingSession(true);
    try {
      const res = await fetch("/api/assessment/start", {
        method: "POST"
      });
      if (res.ok) {
        const session = await res.json();
        router.push(`/student/session/${session.id}`);
      }
    } catch (err) {
      console.error("Error starting assessment", err);
      setStartingSession(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  if (loading) {
    return (
      <div className="student-home-root">
        <div className="flex-1 flex items-center justify-center">
          <div className="spinner w-12 h-12 border-4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="student-home-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <header className="student-home-header">
        <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={140} height={45} />
        <button onClick={handleLogout} className="student-logout-btn">
          <LogOut size={16} />
          <span>خروج</span>
        </button>
      </header>

      <main className="student-home-main">
        <Image 
          src="/characters/boy/welcome.png" 
          alt="Welcome" 
          width={220} 
          height={280}
          className="student-home-char" 
          priority
        />
        
        <h1 className="student-greeting">
          أهلاً بك يا بطل، {student?.full_name?.split(' ')[0] || "طالب"}!
        </h1>
        {student?.grade_level && (
          <div className="student-grade-badge">الصف {student.grade_level}</div>
        )}
        <p className="student-subtitle">
          هل أنت مستعد لنبدأ رحلة التعلم والتطور معاً؟
        </p>
        
        <button
          onClick={handleStartAssessment}
          disabled={startingSession}
          className="student-start-btn"
        >
          {startingSession ? (
            <span className="flex items-center justify-center gap-3">
              <span className="spinner border-4 w-6 h-6"></span>
              <span>جاري التجهيز...</span>
            </span>
          ) : (
            "ابدأ الاختبار"
          )}
        </button>
      </main>
    </div>
  );
}
''')

write_file('apps/web/src/app/admin/(dashboard)/layout.tsx', '''"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { LayoutDashboard, Users, UserPlus, Mic, BarChart2, Settings, LogOut, Menu, X } from "lucide-react";

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { href: "/admin", label: "لوحة القيادة", icon: LayoutDashboard },
    { href: "/admin/students", label: "الطلاب", icon: Users },
    { href: "/admin/students/new", label: "إضافة طالب", icon: UserPlus },
    { href: "/admin/audio-review", label: "مراجعة التسجيلات", icon: Mic },
    { href: "/admin/reports", label: "التقارير", icon: BarChart2 },
    { href: "/admin/settings", label: "الإعدادات", icon: Settings },
  ];

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const SidebarContent = () => (
    <>
      <div className="sidebar-brand">
        <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={120} height={40} />
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={20} className="sidebar-nav-icon" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">ب</div>
          <div className="sidebar-user-name">الباحثة</div>
        </div>
        <button onClick={handleLogout} className="sidebar-logout">
          <LogOut size={18} />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="sidebar-layout" dir="rtl">
      <aside className="sidebar hidden md:flex">
        <SidebarContent />
      </aside>

      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 max-w-sm flex-1 bg-white flex flex-col z-50 h-full">
            <button 
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 left-4 p-2 text-muted hover:bg-bg rounded-md"
            >
              <X size={24} />
            </button>
            <SidebarContent />
          </div>
        </div>
      )}

      <main className="sidebar-content">
        <div className="md:hidden flex items-center justify-between bg-white p-4 border-b border-border mb-4 rounded-md shadow-sm">
          <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={100} height={32} />
          <button 
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 text-navy hover:bg-bg rounded-md"
          >
            <Menu size={24} />
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
''')

write_file('apps/web/src/app/admin/(dashboard)/page.tsx', '''"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Users, Activity, Plus } from "lucide-react";

interface Researcher {
  id: string;
  username: string;
  role: string;
}

interface Student {
  id: string;
  full_name: string;
  grade_level: number;
  access_code: string;
}

export default function AdminDashboard() {
  const [researcher, setResearcher] = useState<Researcher | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [meRes, studentsRes] = await Promise.all([
          fetch("/api/me"),
          fetch("/api/researcher/students")
        ]);
        
        if (meRes.ok) setResearcher(await meRes.json());
        if (studentsRes.ok) setStudents(await studentsRes.json());
      } catch (err) {
        console.error("Error fetching dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="spinner w-8 h-8 border-4"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-navy mb-1">
            مرحباً، {researcher?.username || "الباحثة"}
          </h1>
          <p className="text-muted text-sm">نظرة عامة على أداء الطلاب ونشاطاتهم اليوم.</p>
        </div>
        <Link href="/admin/students/new" className="btn-primary w-fit">
          <Plus size={20} />
          إضافة طالب
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="stat-card">
          <div className="stat-icon bg-primary/10 text-primary">
            <Users size={24} />
          </div>
          <div>
            <p className="stat-label">إجمالي الطلاب</p>
            <p className="stat-value">{students.length}</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-green/10 text-green">
            <Activity size={24} />
          </div>
          <div>
            <p className="stat-label">الطلاب النشطين</p>
            <p className="stat-value">{students.length}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold text-navy">الطلاب المضافين حديثاً</h2>
          <Link href="/admin/students" className="text-primary hover:underline text-sm font-medium">
            عرض الكل
          </Link>
        </div>
        
        {students.length === 0 ? (
          <div className="empty-state">
            <Image src="/characters/girl/welcome.png" alt="No students" width={100} height={140} className="mb-6 opacity-80" />
            <h3 className="text-lg font-bold text-navy mb-2">لا يوجد طلاب حتى الآن</h3>
            <p className="text-muted mb-6">أضف أول طالب للبدء في تتبع تقدمهم</p>
            <Link href="/admin/students/new" className="btn-primary">
              <Plus size={20} />
              إضافة طالب جديد
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>الصف</th>
                  <th>رمز الدخول</th>
                </tr>
              </thead>
              <tbody>
                {students.slice(0, 5).map(student => (
                  <tr key={student.id}>
                    <td className="font-medium text-navy">{student.full_name}</td>
                    <td>{student.grade_level}</td>
                    <td>
                      <span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono text-sm" dir="ltr">
                        {student.access_code}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
''')

write_file('apps/web/src/app/page.tsx', '''"use client";

import Image from "next/image";
import Link from "next/link";

export default function WelcomePage() {
  return (
    <div className="welcome-root" dir="rtl">

      <div className="amb-shape amb-1" />
      <div className="amb-shape amb-2" />
      <div className="amb-shape amb-3" />

      <header className="w-header">
        <div className="w-logo-wrap">
          <Image src="/brand/logo-navy.svg" alt="منصة هِمّة" width={130} height={44} priority />
        </div>
        <nav className="w-nav">
          <a href="#about" className="w-nav-link">عن المنصة</a>
          <a href="#how" className="w-nav-link">كيف تعمل</a>
          <a href="#features" className="w-nav-link">المزايا</a>
          <Link href="/student/login" className="w-nav-cta">ابدأ الآن</Link>
        </nav>
      </header>

      <section className="w-hero">
        <div className="w-hero-copy">
          <span className="w-eyebrow">
            <span className="w-eyebrow-dot" />
            منصة بحثية لتعليم القراءة — سلطنة عُمان
          </span>
          <h1 className="w-h1">
            نتعلّم بهدوء،
            <br />
            <span className="w-h1-accent">ونتقدّم بثقة.</span>
          </h1>
          <p className="w-lead">
            هِمّة منصة تعليمية تكيّفية مصممة لمساعدة طلاب الصف الثالث على تطوير مهارات القراءة
            خطوةً خطوة، من خلال أنشطة ممتعة وتقييم دقيق.
          </p>
          <div className="w-actions">
            <Link href="/student/login" className="w-btn-primary">
              <Image src="/brand/logo-white.svg" alt="" width={22} height={22} />
              دخول الطالب
              <span className="w-btn-arrow">←</span>
            </Link>
          </div>
          <div className="w-trust">
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-blue" />
              واضحة وسهلة
            </div>
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-green" />
              تتدرّج مع الطالب
            </div>
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-yellow" />
              تشجيع في كل خطوة
            </div>
          </div>
        </div>

        <div className="w-hero-visual">
          <div className="w-orbit w-orbit-1" />
          <div className="w-orbit w-orbit-2" />
          <Image
            src="/characters/boy/welcome.png"
            alt="شخصية الطالب"
            width={220} height={300}
            className="w-char w-char-boy"
            priority
          />
          <Image
            src="/characters/girl/welcome.png"
            alt="شخصية الطالبة"
            width={200} height={280}
            className="w-char w-char-girl"
            priority
          />
          <div className="w-floor" />
        </div>
      </section>

      <section id="about" className="w-section">
        <div className="w-section-inner">
          <div className="w-section-badge">من نحن</div>
          <h2 className="w-h2">منصة هِمّة التعليمية</h2>
          <p className="w-section-lead">
            هِمّة مشروع بحثي تعليمي يهدف إلى دعم طلاب الصف الثالث الذين يواجهون صعوبات في القراءة.
            تعتمد المنصة على نهج تكيّفي يُعدّل مسار التعلّم بناءً على أداء كل طالب،
            لضمان تقدّم حقيقي وقابل للقياس.
          </p>

          <div className="w-cards-grid">
            <div className="w-about-card w-card-blue animate-on-scroll animate-delay-1">
              <div className="w-about-icon">
                <Image src="/characters/boy/explain.png" alt="" width={80} height={100} />
              </div>
              <h3>للطالب</h3>
              <p>أنشطة قصيرة وممتعة تناسب مستواه، مع تشجيع مستمر وشخصيات محببة ترافقه في رحلته.</p>
            </div>
            <div className="w-about-card w-card-green animate-on-scroll animate-delay-2">
              <div className="w-about-icon">
                <Image src="/characters/girl/explain.png" alt="" width={80} height={100} />
              </div>
              <h3>للباحثة</h3>
              <p>لوحة بيانات احترافية لمتابعة تقدّم الطلاب، مراجعة التسجيلات الصوتية، وإصدار التقارير.</p>
            </div>
            <div className="w-about-card w-card-yellow animate-on-scroll animate-delay-3">
              <div className="w-about-icon" style={{ fontSize: "2.5rem", lineHeight: 1 }}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#20364D" strokeWidth="1.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <h3>نظام تكيّفي</h3>
              <p>تُحدّد هِمّة مستوى الطالب تلقائياً وتختار له المحتوى المناسب، فلا إفراط ولا تفريط.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="w-section w-section-alt">
        <div className="w-section-inner">
          <div className="w-section-badge">كيف تعمل</div>
          <h2 className="w-h2">رحلة الطالب في هِمّة</h2>

          <div className="w-steps">
            <div className="w-step animate-on-scroll animate-delay-1">
              <div className="w-step-num">١</div>
              <div className="w-step-body">
                <h3>الاختبار القبلي</h3>
                <p>يبدأ الطالب باختبار يُحدّد مستواه الحالي في القراءة — 30 سؤالاً متدرجاً.</p>
              </div>
            </div>
            <div className="w-step-line" />
            <div className="w-step animate-on-scroll animate-delay-2">
              <div className="w-step-num">٢</div>
              <div className="w-step-body">
                <h3>الأنشطة التكيّفية</h3>
                <p>تختار هِمّة الأنشطة التي تناسب مستوى الطالب وتُعدّلها تلقائياً مع تقدّمه.</p>
              </div>
            </div>
            <div className="w-step-line" />
            <div className="w-step animate-on-scroll animate-delay-3">
              <div className="w-step-num">٣</div>
              <div className="w-step-body">
                <h3>الاختبار البعدي</h3>
                <p>بعد إتمام المسار التعليمي، يُجري الطالب اختباراً نهائياً لقياس التحسّن الفعلي.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="w-section">
        <div className="w-section-inner">
          <div className="w-section-badge">المزايا</div>
          <h2 className="w-h2">ما يجعل هِمّة مختلفة</h2>

          <div className="w-features">
            <div className="w-feature animate-on-scroll animate-delay-1">
              <div className="w-feature-icon" style={{ background: "#EBF5FF" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#347FD9" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
                </svg>
              </div>
              <h3>تعلّم في أي وقت</h3>
              <p>المنصة متاحة على الهاتف والكمبيوتر واللوحة، وتحفظ تقدّم الطالب تلقائياً.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-2">
              <div className="w-feature-icon" style={{ background: "#D1FAE5" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#51B985" strokeWidth="2">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <h3>تقييم حقيقي</h3>
              <p>يُسجّل الطالب قراءته ويستقبل تقييماً دقيقاً، بعيداً عن الحفظ والتخمين.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-1">
              <div className="w-feature-icon" style={{ background: "#FEF9C3" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2">
                  <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                </svg>
              </div>
              <h3>تشجيع مستمر</h3>
              <p>شخصيات هِمّة ترافق الطالب في كل خطوة، تُشجّعه عند النجاح وتُحفّزه عند التعثّر.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-2">
              <div className="w-feature-icon" style={{ background: "#F3E8FF" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" strokeWidth="2">
                  <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              <h3>تقارير للباحثة</h3>
              <p>بيانات تفصيلية عن أداء كل طالب، مع إمكانية تصدير التقارير لدعم البحث العلمي.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="w-cta">
        <div className="w-cta-inner">
          <Image
            src="/characters/boy/encourage.png"
            alt=""
            width={120} height={160}
            className="w-cta-char"
          />
          <div>
            <h2 className="w-cta-h2">هل أنت مستعد لبدء رحلتك؟</h2>
            <p className="w-cta-p">أدخل رمز الدخول الخاص بك وابدأ التعلّم الآن.</p>
            <Link href="/student/login" className="w-btn-primary w-btn-lg">
              ابدأ الآن
              <span className="w-btn-arrow">←</span>
            </Link>
          </div>
        </div>
      </section>

      <footer className="w-footer">
        <div className="w-footer-inner">
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={34} />
          <p className="w-footer-copy">
            منصة هِمّة التعليمية — مشروع بحثي لدعم تعليم القراءة في سلطنة عُمان
          </p>
          <p className="w-footer-tagline">أتعلم، أتطور، أصل إلى القمة</p>
        </div>
      </footer>
    </div>
  );
}
''')

write_file('apps/web/src/components/ScrollAnimator.tsx', '''"use client";
import { useEffect } from "react";

export function ScrollAnimator() {
  useEffect(() => {
    const els = document.querySelectorAll(".animate-on-scroll");
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add("animated");
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
  return null;
}
''')

write_file('apps/web/src/app/layout.tsx', '''import type { Metadata } from "next";
import "./globals.css";
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
''')
