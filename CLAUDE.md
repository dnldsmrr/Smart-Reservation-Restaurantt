# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SARA — Smart AI Reservation Assistant for **Mandala Rasa** restaurant. Capstone project (CAMP Batch 4, Kelompok 3). Built with Streamlit + Google Gemini 2.5 Flash Lite, backed by a Railway MySQL database with a local JSON fallback.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app (always from project root)
streamlit run Beranda.py

# Activate venv (Windows)
venv\Scripts\activate
```

Required `.env` at project root:
```
GOOGLE_API_KEY="your_gemini_key"
```
MySQL credentials are optional — defaults in `utils.py` point to the Railway instance. Override with: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_TABLE`.

## Architecture

### Entry Point & Page Routing

`Beranda.py` is the Streamlit entry point — the public-facing SARA chatbot page. Streamlit's automatic sidebar navigation is **globally disabled** in `.streamlit/config.toml` (`showSidebarNavigation = false`). Admin pages build their own sidebar nav manually with `st.page_link()`.

The two admin-only pages live in `pages/` and follow Streamlit's numeric prefix routing convention:
- `pages/1_Dashboard_Analytics.py` — KPI cards + Plotly analytics charts (reservation trends, revenue, customer breakdown)
- `pages/2_Reservation_Management.py` — filterable reservation table with pagination and detail panel, CSV export

### Authentication

Admin auth is a single session state flag: `st.session_state.admin_logged_in`. Password is hardcoded as `"admin123"` in both `Beranda.py` (inline popover) and `utils.check_admin_login()` (full-page login guard used by admin pages). `check_admin_login()` calls `st.switch_page("Beranda.py")` then `st.stop()` when unauthenticated — place it early in each admin page, after `set_page_config` and CSS injection but before any data loading or rendering.

Admin pages also track `st.session_state.admin_sidebar_open` (bool) to toggle the sidebar and render a floating FAB hamburger button when collapsed (the `#sara-show-menu-marker` CSS selector hack in both admin pages and in `COMMON_CSS`).

### Data Flow (`utils.py`)

`load_data()` is the main entry point — it tries Railway MySQL first, falls back to `data.json`. If MySQL is empty it auto-migrates all local records. Two cached helpers underpin it: `load_mysql_data()` and `load_local_data()` (both use `@st.cache_data`).

`_normalize_reservation_df()` is called by both cached loaders to standardize column names and dtypes (`Tanggal Reservasi` as datetime, `Bulan`, `Nama Bulan`, `Rating` and `Total Estimasi (IDR)` as numeric). Pass DataFrames through this whenever loading from a new source.

New reservations (from SARA) are written via `append_reservation(record)`: this writes to `data.json` first, then syncs to MySQL. If MySQL sync fails it returns a `warning` key — success is still `True`. After writing, caches are cleared manually.

`data.json` holds 500 synthetic reservations and is the local source of truth.

### AI Pipeline (`Beranda.py`)

Message processing uses a **heuristic-first, Gemini-fallback** pattern:

1. `detect_intent(msg)` — keyword matching returns one of: `buat_reservasi`, `cek_reservasi`, `info_restoran`, `greeting`, `general`
2. `extract_params(msg)` — regex extracts name, party size, date (`DD/MM` → `YYYY-MM-DD`), time, area, and occasion
3. If intent is recognised, `heuristic_response()` handles it locally (calling `cek_reservasi_tool` or `buat_reservasi_tool` as needed)
4. Only when `heuristic_response()` returns the "tidak memahami" fallback string does `call_gemini()` fire — it uses raw `urllib.request`, not the Gemini SDK, hitting `gemini-2.5-flash-lite`

### Styling System

CSS is split across three layers that each serve different surfaces:

| Layer | Location | Used by |
|---|---|---|
| Chat page CSS | `styles/main.css` | `Beranda.py` via `load_css("main.css")` |
| Admin shared CSS | `COMMON_CSS` string in `utils.py` | Both admin pages via `st.markdown(COMMON_CSS, ...)` |
| Page-specific overrides | Inline `st.markdown("""<style>...""")` | Per-page fine-tuning |

`styles/admin.css` exists but is **not currently loaded** by any page — it contains status badge classes for a future table layout feature.

Color tokens and other constants exported from `utils.py` — always use these, never raw hex:
- `GOLD = "#FF6B35"` — terracotta, primary accent
- `DARK = "#2D2522"` — charcoal, headings and text
- `CREAM = "#FFFBF8"` — warm off-white, page backgrounds
- `STATUS_COLORS` — dict mapping status strings (both title-case and lowercase variants) to hex colors
- `MONTH_MAP` — dict mapping month integers 1–12 to Indonesian abbreviated month names

Fonts loaded from Google Fonts: **Inter** (body/labels) and **Outfit** (headings/KPI values).

### Key CSS Classes (reusable across admin pages)

Defined in `COMMON_CSS` (utils.py):
- `.kpi-card` — white card with colored left border (set `--accent` CSS var per card)
- `.section-title` — heading with a gold gradient underline rule
- `.badge` — pill-shaped inline label
- `.back-button` / `.back-button-wrapper` — gradient terracotta CTA button

Defined in `styles/admin.css` (for future use):
- `.status-confirmed/pending/cancelled/completed/no_show` — colored text
- `.table-card-indoor/outdoor/vip` — area-specific table layout cards
