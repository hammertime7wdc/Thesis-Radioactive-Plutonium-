# QualCheck — Flet Build Spec

Build a Python Flet app called **QualCheck**, a rubric-guided semantic evaluation system for academic responses (short answers, essays, code reports). This spec is implementation-ready: every value maps to a Python constant, every screen lists concrete components and states. Follow it exactly; where a decision was ambiguous in the original brief, the choice is stated and marked **(decision)**.

---

## 1. Design Tokens

Define these in `utils/utils.py` and import everywhere — never hardcode hex values in screen files.

### Colors

| Constant | Hex | Usage |
|---|---|---|
| `PRIMARY_BLUE` | `#2563EB` | buttons, active nav, accents |
| `PRIMARY_BLUE_DARK` | `#1D4ED8` | hover state |
| `PRIMARY_BLUE_LIGHT` | `#EFF6FF` | active toggle bg, info boxes |
| `BG_COLOR` | `#F3F4F6` | page background |
| `CARD_BG_COLOR` | `#FFFFFF` | cards, panels |
| `SECTION_BG_COLOR` | `#F9FAFB` | table header row, nested cards |
| `BORDER_COLOR` | `#E5E7EB` | hairline borders |
| `BORDER_COLOR_DARK` | `#D1D5DB` | emphasized borders |
| `TEXT_PRIMARY` | `#111827` | headings, primary text |
| `TEXT_SECONDARY` | `#6B7280` | body/secondary text |
| `TEXT_TERTIARY` | `#9CA3AF` | muted/disabled text, shadow tint |
| `TEXT_WHITE` | `#FFFFFF` | text on filled buttons/badges |
| `SUCCESS` | `#15803D` | text; bg `#DCFCE7` |
| `WARNING` | `#A16207` | text; bg `#FEF9C3` |
| `ERROR` | `#B91C1C` | text; bg `#FEE2E2` |
| `ADMIN_PURPLE` | `#7E22CE` | text; bg `#F3E8FF` — admin-role badge only |
| `BUTTON_PRIMARY_BG` / `BUTTON_PRIMARY_TEXT` | `PRIMARY_BLUE` / `TEXT_WHITE` | primary CTAs |
| `BUTTON_SECONDARY_BG` / `BUTTON_SECONDARY_TEXT` / `BUTTON_SECONDARY_BORDER` | `#FFFFFF` / `TEXT_PRIMARY` / `BORDER_COLOR` | secondary/filter buttons |
| `INPUT_BG` / `INPUT_BORDER` / `INPUT_TEXT` / `INPUT_HINT` | `#FFFFFF` / `BORDER_COLOR` / `TEXT_PRIMARY` / `TEXT_TERTIARY` | form fields |

**Login screen only** (dark theme, not tokenized into the light palette above):
`LOGIN_BG_GRADIENT = ["#0F172A", "#1E3A5F", "#0F172A"]`, glass card `rgba(255,255,255,0.05)` with `rgba(255,255,255,0.1)` border.

### Typography scale (decision — matches the already-built Admin Panel; do not use 24/14 from earlier drafts)

| Role | Size | Weight |
|---|---|---|
| Page title (e.g. "Admin Panel") | 22 | Bold |
| Section heading (e.g. "Users", "Scoring Thresholds") | 18 | Bold |
| Body text / table cells / buttons / badges | 13 | Regular / W_500–W_600 |
| Labels — table column headers, tags | 12 | Bold/Medium |
| Caption / tagline | 11 | Regular |

Font family: system default (Flet's default sans-serif — do not import a custom font unless requested).

### Shape & spacing

- Card border radius: `12px` · Button/input radius: `8px`
- Card padding: `24px` (matches built screens — not 32px)
- Gap between stacked sections: `20px`
- Card shadow: `blur_radius=8, spread_radius=0, color=TEXT_TERTIARY, offset=(0,2)`

---

## 2. Component Patterns (reuse across all screens)

- **Badge/pill**: `Container` with tinted bg, `padding.symmetric(horizontal=10, vertical=4)`, `border_radius=12`, text size 12, weight W_500, colored text matching the semantic color (SUCCESS/WARNING/ERROR/ADMIN_PURPLE).
- **Table**: `ft.DataTable`, `border=border.all(1, BORDER_COLOR)`, `border_radius=8`, `heading_row_color=SECTION_BG_COLOR`, header text size 12 bold TEXT_SECONDARY, body cells size 13.
- **Primary button**: `ElevatedButton`, `bgcolor=BUTTON_PRIMARY_BG`, `radius=8`, text size 13 W_600, icon 16–18px, `elevation=2`.
- **Filter/tab pill**: active = `PRIMARY_BLUE` bg + white text; inactive = `BUTTON_SECONDARY_BG` + `TEXT_SECONDARY`, text size 13.
- **Card container**: `bgcolor=CARD_BG_COLOR`, `border=border.all(1, BORDER_COLOR)`, `border_radius=12`, `padding=24`, standard shadow above.

---

## 3. Screens

### Screen 1 — Login
Full-screen dark navy gradient background, single centered glass card (max width 448, `border_radius=16`, `padding=32`).

- **Tabs**: "Sign In" / "Create Account", equal width; active = white text + 2px blue bottom border.
- **Logo row**: 36px blue rounded-square "Q" + "QualCheck" (16 bold white) / "Semantic Evaluation System" (11, muted blue).
- **Sign In fields, top → bottom**:
  1. "Continue with Google" — full width, white bg, Google logo, radius 10
  2. Divider: line — "or" — line
  3. Email label + dark input
  4. Password label + input (show/hide eye icon) + "Forgot password?" link, right-aligned on the label row
  5. "Sign in" — full width, blue, LogIn icon
- **Below card**: 3 stat chips — "BERT / Embeddings", "Cosine / Similarity", "Rubric / Guided".

**Forgot Password** (replaces form, tabs hidden): back link → circular blue-tinted mail icon (56px) → heading + subtitle → email input → "Send Reset Code". After send: green check circle → "Check your inbox" → email shown → "Enter reset code" → "Resend" link.

**Reset Password**: back link → key icon in blue circle → heading → 6-digit code input (centered, wide letter-spacing, large font) → new password + 4-segment strength bar (red/yellow/green, label Weak/Medium/Strong) → confirm password + red mismatch text → "Reset Password". Success: green check → "Password updated!" → auto-redirect to login.

### Screen 2 — Persistent Header
Height ~72px, white bg, bottom border.

- **Left**: 40px blue rounded-square "Q" logo, "QualCheck" (20 bold black), "Rubric-Guided Semantic Evaluation System" (12 gray) below.
- **Right, left → right**: (if admin) purple "Admin" pill w/ shield icon → "New Evaluation" → "Dashboard" (active = blue bg white text, inactive = light gray bg dark text) → divider → avatar (32px circle, initials) + name (14) / role (12 gray) → sign-out icon button.

### Screen 3 — New Evaluation (Input Form)
Card: max width 896, centered, `padding=32` (wider than standard — this is a focused single-task screen). Title "Evaluate Academic Response", 22 bold.

1. **Output Type** — 3 equal-width toggle buttons: Short Answer / Essay / Code Report. Active = 2px blue border + light blue bg + blue text.
2. **Academic Prompt** — label + 3-row textarea, blue focus ring.
3. **Rubric Descriptor** — label + helper text, then numbered criterion cards (`SECTION_BG_COLOR` bg, `border_radius=8`, `padding=16`, blue numbered circle 20px + bold criterion name + 2-row textarea):
   - Short Answer: Accuracy of Answer, Key Concept, Clarity
   - Essay: Content, Organization, Language
   - Code Report: Constraint Adherence, Technical Terminology, Algorithmic Logic, Clarity and Coherence
4. **Student Responses** — label w/ Users icon + "PDF per student" note, "Clear all" red link (shown only when files exist). Dashed drop zone (blue + light-blue on drag-over) with cloud icon + "Drag & drop PDFs, or browse". File list below: header row ("X students queued" / "Evaluating X of Y…" during processing), each row = file icon, filename (truncated), size, "#N" badge, remove (X). During evaluation: active row light-blue + spinner, completed rows light-green + checkmark.
5. **Submit** — full-width blue "Evaluate X Responses" + chevron; disabled = gray.
6. **Info box** below the card — light blue bg, blue border, "How it works" + 3 bullets.

### Screen 4 — Results
Two stacked cards **(decision: stacked, not two-column — keeps score legible on narrow viewports)**.

- **Score card**: large bold colored score ("73%"), circular/bar gauge, classification pill, timestamp (small gray).
- **Detail card**: prompt used, rubric criteria used, student filename, output-type badge.
- "New Evaluation" button, blue, bottom of screen.

### Screen 5 — Dashboard
- **Stat row** (3 cards): Total Evaluations (blue), Average Score (green), Last Evaluation (gray date).
- **Chart**: classification distribution (bar or pie, green/yellow/red slices/bars).
- **History table**: File, Score, Classification (pill), Type, Date — sortable columns.

### Screen 6 — Admin Panel *(already built — reference only)*
Header: purple shield square + "Admin Panel" (22 bold) + "Administrator" purple pill. Tab bar: Users | Analytics | Submissions | Settings & Audit (active = white bg + shadow, inactive = transparent gray text).

- **Users**: table (avatar+name, email, role pill, subject, evaluations count, joined, status toggle), "Add User" button top-right.
- **Analytics**: 3 stat cards (Total Evaluations blue, Avg Score green, Manual Overrides orange) → pie (classification) + radar (criterion averages) side by side → full-width bar chart (per-criterion averages, rounded-top blue bars).
- **Submissions**: filter pills (All/Fully/Partially/Irrelevant) + "Export CSV" green button top-right; table with Student File, Score, Classification (strikethrough original if overridden), Type, Evaluator, Date, Actions (inline override: dropdown + green check confirm + gray X cancel).
- **Settings & Audit**: Scoring Thresholds card (two sliders, "Fully Relevant ≥" default 75%, "Partially Relevant ≥" default 50%, value in bold colored text, "Save Thresholds" + "✓ Saved" fade) and Audit Log card (shield header, entries with clock icon, bold action, detail text, `actor · timestamp` line below).

### Screen 7 — Profile Settings
Two-column layout: left sidebar (208px) + right content.

- **Sidebar**: Profile / Security / Notifications nav buttons (icons: user/lock/bell; active = blue bg white text); below, small stat block (Evaluations count, Role, Member since).
- **Profile section**: card with 80px gradient avatar + camera-icon edit button (bottom-right corner), name/email/role pill beside avatar, 2-col grid (Full Name, Email [read-only], Department, Institution), full-width Bio textarea, Save button + "✓ Saved" confirmation (bottom row, save right / confirmation left). Second card: Recent Activity list (blue book icon, action, subject, right-aligned timestamp).
- **Security section**: Current Password (show/hide) → New Password + 4-segment strength bar → Confirm Password + red mismatch warning → "Update Password".
- **Notifications section**: 4 toggle rows (bold label + gray description left, pill toggle right, blue=on/gray=off) → "Save Preferences".

---

## 4. Navigation Architecture

Follow the pattern already used in `admin_navigation.py`: a per-area `Navigation` controller class holding `self.page`, `self.current_tab`, `self.main_content`, with `navigate_to_*` methods that either do first-time setup (`page.clean()`, set window size/theme, build app bar + secondary nav) or, on subsequent calls, swap only `main_content` and refresh the secondary nav's active-state styling. Each screen module exposes `main(page: ft.Page, nav=None)` and writes `nav.main_content = main_content` at the end so the controller can remove it on the next navigation call.

---

## 5. Open Decisions Made in This Spec

1. Typography set to **22/18/13/12/11** (not 24/18/14/12/11) to match the Admin Panel screens already implemented.
2. Card padding standardized to **24px** (not 32px), except the single-task Evaluation form (32px, intentionally more spacious).
3. Results screen uses **stacked** cards, not a two-column layout.
4. Added `ADMIN_PURPLE` / `ADMIN_PURPLE` background as new tokens — not previously defined in `utils/utils.py`.

If any of these should instead follow the original 24px/32px spec, flag it and I'll adjust before generating screens.
