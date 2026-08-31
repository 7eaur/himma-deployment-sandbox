# P03 Design System Blueprint

## Route Map

| Route | Type | Description |
|-------|------|-------------|
| `/` | Public | Welcome page, entry point for both student and researcher |
| `/admin/login` | Researcher | Login with username/password |
| `/admin` | Researcher | Dashboard with stats and recent students |
| `/admin/students` | Researcher | Students list table |
| `/admin/students/new` | Researcher | Add new student form |
| `/admin/students/[id]` | Researcher | Student detail profile |
| `/admin/audio-review` | Researcher | Review student audio recordings |
| `/admin/reports` | Researcher | Reports and statistics (coming soon) |
| `/admin/settings` | Researcher | User and system settings |
| `/student/login` | Student | Login with access code |
| `/student` | Student | Student home page |
| `/student/session/[id]` | Student | Assessment session runner |

## Color Tokens

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `--color-primary` | `#347FD9` | Primary actions, branding |
| `--color-green` | `#51B985` | Success, progress |
| `--color-yellow` | `#FFC857` | Warnings, accents |
| `--color-navy` | `#20364D` | Typography (main text) |
| `--color-bg` | `#F7FBFF` | Main background color |
| `--color-border` | `#DCE8F2` | Borders and dividers |
| `--color-white` | `#FFFFFF` | Card backgrounds |
| `--color-muted` | `#64788B` | Secondary text, placeholders |

## Typography

| Font Family | Usage | Fallback |
|-------------|-------|----------|
| `Tajawal` | Student UI, joyful | `sans-serif` |
| `IBM Plex Sans Arabic` | Researcher UI, professional | `sans-serif` |

## Component Inventory

### Utility Classes (globals.css)
- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`
- `.card`
- `.badge`
- `.input-field`
- `.spinner`
- `.alert`, `.alert-error`, `.alert-success`
- `.progress-bar`, `.progress-bar-fill`
- `.sidebar-layout`, `.sidebar`, `.sidebar-content`

### Shared Components
- `AssessmentRunner`: Handles student test execution, progress, MCQ and Read Aloud interactions. Uses Lucide icons (`Mic`, `MicOff`).
