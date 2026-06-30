---
title: "feat: Mobile-responsive layout for Stock Explorer"
date: 2026-06-30
type: feat
depth: Standard
---

# feat: Mobile-responsive layout for Stock Explorer

## Summary

Make the Stock Explorer Streamlit app usable on phones. The primary pain points are multi-stock KPI columns overflowing on narrow screens, oversized headings, and cramped tab controls. All fixes are CSS-only (media queries injected via `st.markdown`) because Streamlit has no server-side screen-width detection.

---

## Problem Frame

Users opening `https://imb-stock-explorer.streamlit.app/` on a 375–430 px screen (iPhone SE → iPhone 15 Pro Max) see:

- `st.columns(len(valid))` metric cards horizontally overflowing — 5 cards at ~75 px each, labels clipped, numbers truncated
- Win/loss streak cards: same column issue
- Heading sizes designed for 1440 px desktop feel oversized on mobile
- Tab pills may need horizontal scrolling on small screens
- The 🔄 "next fact" button is a 31 px tap target — below Apple/Google's 44 px minimum

---

## Requirements

- R1: KPI metric cards and streak cards must be readable without horizontal scroll on screens ≥ 360 px wide
- R2: Heading text must not overflow on small screens
- R3: Tab row must scroll horizontally rather than wrap or clip labels
- R4: The 🔄 fact button must meet 44 × 44 px minimum tap target
- R5: No changes to desktop layout (breakpoint ≤ 768 px only)

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CSS vs Python layout | CSS media queries | Streamlit has no runtime screen-width in Python; injecting CSS via `st.markdown` is the only option |
| Column wrapping strategy | `flex-wrap + min-width` | Cards naturally reflow to 2-per-row on narrow screens without changing Python `st.columns()` calls |
| Breakpoint | 768 px | Standard tablet/phone threshold; Streamlit's own sidebar breakpoint is ~768 px |
| Chart height on mobile | CSS override | Plotly's `height` param is Python-only and would change desktop too; CSS targeting `.stPlotlyChart` lets us reduce height only on mobile |

---

## Implementation Units

### U1. Mobile CSS layer

**Goal:** Inject a `@media (max-width: 768px)` block that fixes layout, typography, and tap targets on mobile.

**Requirements:** R1, R2, R3, R4, R5

**Dependencies:** none

**Files:** `app.py`

**Approach:**
Extend the existing `st.markdown("""<style>…</style>""")` block already in `app.py`. Add a media query section after the existing desktop styles. Key selectors:

- `[data-testid="stHorizontalBlock"]` — Streamlit's flex row; add `flex-wrap: wrap`
- `[data-testid="column"]` — each column child; set `min-width: 130px; flex: 1 1 130px`
- `h1` / `h2` / `h3` — reduce font sizes (`1.4rem` / `1.15rem` / `1rem`)
- `[data-testid="stMetricValue"]` — reduce from desktop size to `1.3rem`
- `[data-testid="stTabs"] > div:first-child` — `overflow-x: auto; -webkit-overflow-scrolling: touch`
- `[data-testid="stButton"] button` — `min-height: 44px; min-width: 44px`
- `.main .block-container` — reduce lateral padding to `1rem`
- `[data-testid="stAlert"]` — tighter padding and slightly smaller font for the "Did you know?" banner

**Patterns to follow:** Existing `st.markdown(…, unsafe_allow_html=True)` CSS injection at the top of `app.py`.

**Test scenarios:**
- At 375 px viewport, 5 stocks selected: metric cards must show 2–3 per row, no horizontal overflow
- At 375 px viewport, 3 stocks selected: cards wrap to 2 rows cleanly
- At 1440 px desktop: no visible change to layout (breakpoint guard)
- Tab row with 3 tabs at 375 px: all tabs visible or scrollable without clipping
- 🔄 button: tappable area ≥ 44 × 44 px on mobile (visually verify via Playwright)

**Verification:** Take a Playwright screenshot at 390 × 844 px (iPhone 14 viewport) and confirm no horizontal overflow.

---

## Scope Boundaries

### In scope
- CSS media query additions to `app.py`'s existing style block

### Deferred to Follow-Up Work
- Dedicated mobile sidebar toggle UX (Streamlit handles sidebar collapse natively)
- Chart height reduction (Plotly iframes don't expose a clean CSS height override; low priority since charts pan/zoom on touch)
- Python-level `st.columns` refactor (not needed if CSS wrapping works)

### Outside scope
- Native mobile app
- Server-side device detection
- Changes to the assignment's graded features

---

## Sources & Research

- Streamlit DOM selectors verified against Streamlit 1.x component hierarchy (`data-testid` attributes)
- Apple HIG: minimum tap target 44 × 44 pt
- Material Design: minimum touch target 48 × 48 dp
