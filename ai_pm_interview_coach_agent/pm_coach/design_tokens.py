"""
The design system: every color/font constant (read directly off the reference app's own
compiled CSS - shadcn/Tailwind :root theme block + Google Fonts @import - not eyeballed from
screenshots), plus _inject_design_system(), which injects them as global CSS overrides
(fonts, card/input borders, primary-button color) on top of .streamlit/config.toml's native
theme. Other modules import the color/font constants directly; only the entry point calls
_inject_design_system() itself.
"""
import streamlit as st


# --- Dashboard rendering ------------------------------------------------------------------
# The model leads its response with a small fenced JSON block (see SYSTEM_PROMPT ->
# OUTPUT FORMATTING); this drives a scannable numbers-and-bars summary instead of dumping the
# whole markdown report as one flat page. If the JSON is missing or malformed, everything below
# degrades gracefully to the plain markdown - the report is never held hostage by the summary.

STATUS_COLORS = {
    "good": "#009966",
    "warning": "#973c00",
    "critical": "#e7000b",
    "info": "#1c66b5",
    "muted": "#687487",
}
# Subtle chip tokens: light steps of the same Tailwind emerald/amber/red/secondary-blue scales
# the reference app's own compiled CSS actually uses, paired with a darker step of the same
# family for text (readable on white, never color-alone).
CHIP_BG = {"good": "#ecfdf5", "warning": "#fffbeb", "critical": "#fef2f2", "info": "#e3eaf2", "muted": "#eceff4"}
CHIP_FG = {"good": "#007a55", "warning": "#973c00", "critical": "#e7000b", "info": "#29496b", "muted": "#687487"}

# Explicit light theme for the report card itself, independent of Streamlit's own theme setting -
# this is meant to read like a printed debrief, not adapt to whatever chrome it's embedded in.
CARD_BG = "#ffffff"
CARD_BORDER = "1px solid #d7dce5"
TEXT_PRIMARY = "#22293a"
TEXT_SECONDARY = "#687487"
TEXT_MUTED = "rgba(34,41,58,0.44)"

# Editorial-debrief design system - tokens read directly off the reference app's own compiled
# CSS (its shadcn/Tailwind :root theme block and Google Fonts @import), not eyeballed from
# screenshots: cool-gray page, Fraunces serif display headlines over DM Sans body, a single
# steel-blue accent for eyebrows/links/primary actions, and status chips built from Tailwind's
# own emerald/amber/red/secondary-blue scales at the same shades the reference actually uses.
PAGE_BG = "#eff1f5"
SURFACE_MUTED = "#eceff4"
ACCENT_BLUE = "#1c66b5"
ACCENT_BLUE_BG = "#e3eaf2"
GRAY_PILL_BG = "#eceff4"
GRAY_PILL_FG = "#687487"
FONT_SERIF = "'Fraunces', Georgia, 'Times New Roman', serif"
FONT_SANS = "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
RATING_ACCENT = {"good": "#007a55", "warning": "#973c00", "critical": "#e7000b", "muted": "#687487"}
def _inject_design_system() -> None:
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap" rel="stylesheet">
        <style>
        .stApp {{ background: {PAGE_BG}; }}
        [data-testid="stAppViewContainer"] {{ background: {PAGE_BG}; }}
        /* The sidebar (Settings) and the main panel were the same near-identical gray with no
           boundary between them - give the sidebar a clearly distinct white surface and a
           hairline divider so the two panels read as separate regions. */
        [data-testid="stSidebar"] {{
            background: {CARD_BG} !important;
            border-right: 1px solid #d7dce5;
        }}
        .pmic-eyebrow {{
            font-family: {FONT_SANS}; font-size: 12px; font-weight: 700;
            letter-spacing: 0.09em; text-transform: uppercase; color: {ACCENT_BLUE};
            margin: 0 0 6px;
        }}
        .pmic-h1 {{
            font-family: {FONT_SERIF}; font-weight: 600; font-size: 32px;
            line-height: 1.18; color: {TEXT_PRIMARY}; margin: 0 0 8px;
        }}
        .pmic-h2 {{
            font-family: {FONT_SERIF}; font-weight: 600; font-size: 21px;
            line-height: 1.28; color: {TEXT_PRIMARY}; margin: 0 0 4px;
        }}
        .pmic-subtitle {{
            font-family: {FONT_SANS}; font-size: 14.5px; color: {TEXT_SECONDARY};
            line-height: 1.55; margin: 0 0 4px;
        }}
        /* Force a plain, obviously-editable border on text fields - Streamlit's own default
           can render a red/invalid-looking border on an empty required-ish field, which reads
           as broken rather than "click here to type". Broad selectors (not just the specific
           data-testid) plus an explicit white fill, since this has resurfaced once already. */
        div[data-baseweb] textarea, div[data-baseweb] input,
        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
        .stTextArea textarea, .stTextInput input, textarea, input[type="text"], input[type="password"] {{
            border-color: #d7dce5 !important;
            background-color: #ffffff !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        div[data-baseweb] textarea:focus, div[data-baseweb] input:focus,
        [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus,
        .stTextArea textarea:focus, .stTextInput input:focus, textarea:focus, input[type="text"]:focus {{
            border-color: {ACCENT_BLUE} !important;
            box-shadow: 0 0 0 1px {ACCENT_BLUE} !important;
        }}
        /* Belt-and-suspenders on top of config.toml's primaryColor: a browser tab open across
           a server restart can keep showing Streamlit's default red for primary buttons until
           a full page reload, not just a rerun. Target every selector Streamlit has used for
           primary buttons across versions so this never depends on cache timing. */
        .stButton button[kind="primary"], .stButton button[kind="primaryFormSubmit"],
        [data-testid="stBaseButton-primary"], [data-testid="baseButton-primary"] {{
            background-color: {ACCENT_BLUE} !important;
            border-color: {ACCENT_BLUE} !important;
            color: #ffffff !important;
        }}
        .stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover, [data-testid="baseButton-primary"]:hover {{
            background-color: {TEXT_PRIMARY} !important;
            border-color: {TEXT_PRIMARY} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
