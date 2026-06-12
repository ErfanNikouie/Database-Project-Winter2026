
from __future__ import annotations

import streamlit as st

from styles import theme


def inject_css() -> None:
    st.markdown(
        f"""
<style>
:root {{
  --primary: {theme.PRIMARY};
  --primary-hover: {theme.PRIMARY_HOVER};
  --bg: {theme.BG};
  --card: {theme.CARD};
  --text: {theme.TEXT};
  --muted: {theme.MUTED};
}}

.stApp {{
  background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
  color: var(--text);
}}

html, body, [class*="css"], .stApp, .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {{
  color: var(--text);
}}

/* Hide default Streamlit chrome/menu for cleaner app shell */
#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{
  background: transparent;
}}
footer {{ visibility: hidden; }}

/* Hide Streamlit multipage nav (app/dynamic_page/login/profile). */
[data-testid="stSidebarNav"] {{
  display: none;
}}

.block-container {{
  padding-top: 1.2rem;
  padding-bottom: 1.2rem;
  max-width: 1280px;
}}

div[data-testid="stSidebar"] {{
  background: rgba(17, 24, 39, 0.95);
  border-right: 1px solid rgba(148, 163, 184, 0.18);
}}

section[data-testid="stSidebar"] {{
  background: rgba(17, 24, 39, 0.95);
  border-right: 1px solid rgba(148, 163, 184, 0.18);
}}

section[data-testid="stSidebar"] * {{
  color: var(--text) !important;
}}

/* Active menu button style in sidebar */
section[data-testid="stSidebar"] button[kind="primary"],
div[data-testid="stSidebar"] button[kind="primary"] {{
  background: rgba(16, 185, 129, 0.22) !important;
  border: 1px solid rgba(16, 185, 129, 0.65) !important;
  color: #e5e7eb !important;
}}

section[data-testid="stSidebar"] button[kind="primary"]:hover,
div[data-testid="stSidebar"] button[kind="primary"]:hover {{
  background: rgba(16, 185, 129, 0.34) !important;
}}

div[data-testid="stSidebar"] .stButton > button {{
  background: rgba(79, 70, 229, 0.16);
  border: 1px solid rgba(79, 70, 229, 0.45);
}}

div[data-testid="stSidebar"] .stButton > button:hover {{
  background: rgba(79, 70, 229, 0.25);
}}

.card {{
  background: rgba(17, 24, 39, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 12px;
  padding: 14px;
}}

.hrms-muted {{
  color: var(--muted);
  font-size: 0.9rem;
}}

.stButton > button {{
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: var(--primary);
  color: white;
  transition: all 0.15s ease;
}}

/* Catch Streamlit base buttons that bypass .stButton wrappers */
button[kind="secondary"],
button[kind="primary"],
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-header"] {{
  background: rgba(79, 70, 229, 0.18) !important;
  color: #e5e7eb !important;
  border: 1px solid rgba(99, 102, 241, 0.45) !important;
  border-radius: 10px !important;
}}

.stButton > button:hover {{
  background: var(--primary-hover);
  border-color: transparent;
}}

button[kind="secondary"]:hover,
button[kind="primary"]:hover,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="baseButton-header"]:hover {{
  background: rgba(67, 56, 202, 0.55) !important;
  border-color: rgba(99, 102, 241, 0.75) !important;
}}

/* Inputs and pickers: force dark controls with readable text */
/* Global hard reset for Streamlit/BaseWeb input wrappers to kill white outlines */
.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="base-input"],
.stApp div[data-baseweb="textarea"],
.stApp div[data-baseweb="select"],
.stApp div[data-baseweb="input"] > div,
.stApp div[data-baseweb="base-input"] > div,
.stApp div[data-baseweb="textarea"] > div,
.stApp div[data-baseweb="select"] > div {{
  background: rgba(15, 23, 42, 0.88) !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  box-shadow: none !important;
  outline: none !important;
  border-image: none !important;
}}

.stApp div[data-baseweb="input"]:focus-within,
.stApp div[data-baseweb="base-input"]:focus-within,
.stApp div[data-baseweb="textarea"]:focus-within,
.stApp div[data-baseweb="select"]:focus-within,
.stApp div[data-baseweb="input"] > div:focus-within,
.stApp div[data-baseweb="base-input"] > div:focus-within,
.stApp div[data-baseweb="textarea"] > div:focus-within,
.stApp div[data-baseweb="select"] > div:focus-within {{
  border: 1px solid rgba(99, 102, 241, 0.85) !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.5) !important;
  outline: none !important;
}}

.stApp input,
.stApp textarea,
.stApp select {{
  outline: none !important;
  box-shadow: none !important;
}}

.stApp input:focus,
.stApp textarea:focus,
.stApp select:focus,
.stApp input:focus-visible,
.stApp textarea:focus-visible,
.stApp select:focus-visible {{
  outline: none !important;
  box-shadow: none !important;
}}

div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="popover"] div,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] div[role="combobox"] {{
  background: rgba(15, 23, 42, 0.88) !important;
  color: #e5e7eb !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  outline: none !important;
  box-shadow: none !important;
  border-image: none !important;
  background-clip: padding-box !important;
}}

div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {{
  box-shadow: none !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  outline: none !important;
  border-image: none !important;
}}

div[data-testid="stTextInput"] [data-baseweb="base-input"],
div[data-testid="stTextArea"] [data-baseweb="textarea"],
div[data-testid="stNumberInput"] [data-baseweb="base-input"],
div[data-testid="stDateInput"] [data-baseweb="input"] {{
  box-shadow: none !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
  outline: none !important;
}}

div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stNumberInput"] input::placeholder {{
  color: #94a3b8 !important;
}}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stDateInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stSelectbox"] div[role="combobox"]:focus {{
  border: 1px solid rgba(99, 102, 241, 0.85) !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.5) !important;
  outline: none !important;
}}

div[data-testid="stTextInput"] input:focus-visible,
div[data-testid="stTextArea"] textarea:focus-visible,
div[data-testid="stNumberInput"] input:focus-visible,
div[data-testid="stDateInput"] input:focus-visible,
div[data-testid="stSelectbox"] div[role="combobox"]:focus-visible {{
  outline: none !important;
}}

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
textarea:-webkit-autofill,
select:-webkit-autofill {{
  -webkit-text-fill-color: #e5e7eb !important;
  -webkit-box-shadow: 0 0 0px 1000px rgba(15, 23, 42, 0.92) inset !important;
  box-shadow: 0 0 0px 1000px rgba(15, 23, 42, 0.92) inset !important;
}}

/* Password reveal icon */
div[data-testid="stTextInput"] button {{
  background: transparent !important;
  border: none !important;
}}

div[data-testid="stTextInput"] button svg,
div[data-testid="stTextInput"] button path {{
  fill: #cbd5e1 !important;
  color: #cbd5e1 !important;
}}

/* Number input +/- stepper buttons */
div[data-testid="stNumberInput"] button {{
  background: rgba(30, 41, 59, 0.92) !important;
  color: #e5e7eb !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
}}

div[data-testid="stNumberInput"] button:hover {{
  background: rgba(51, 65, 85, 0.95) !important;
}}

div[data-testid="stNumberInput"] button svg,
div[data-testid="stNumberInput"] button path {{
  fill: #e5e7eb !important;
  color: #e5e7eb !important;
}}

/* Dropdown menus */
ul[role="listbox"],
div[role="listbox"] {{
  background: rgba(15, 23, 42, 0.98) !important;
  color: #e5e7eb !important;
  border: 1px solid rgba(148, 163, 184, 0.35) !important;
}}

li[role="option"] {{
  color: #e5e7eb !important;
}}

li[role="option"][aria-selected="true"],
li[role="option"]:hover {{
  background: rgba(79, 70, 229, 0.25) !important;
}}

/* Dataframe/table wrappers */
div[data-testid="stDataFrame"] {{
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 10px;
}}

/* Expander/folder boxes (e.g., sidebar System menu) */
div[data-testid="stExpander"] {{
  border: 1px solid rgba(148, 163, 184, 0.24) !important;
  border-radius: 10px !important;
  background: rgba(15, 23, 42, 0.7) !important;
  overflow: hidden;
}}

div[data-testid="stExpander"] details,
div[data-testid="stExpander"] summary {{
  background: rgba(15, 23, 42, 0.78) !important;
  color: #e5e7eb !important;
}}

div[data-testid="stSidebar"] div[data-testid="stExpander"] {{
  background: rgba(30, 41, 59, 0.78) !important;
  border-color: rgba(99, 102, 241, 0.35) !important;
}}

div[data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover {{
  background: rgba(51, 65, 85, 0.82) !important;
}}

.home-hero {{
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.24), rgba(15, 23, 42, 0.65));
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 16px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
}}

.home-hero h1 {{
  margin: 0;
  font-size: 1.8rem;
}}

.home-hero p {{
  margin: 0.5rem 0 0;
  color: #cbd5e1;
}}

.home-card {{
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 12px;
  padding: 1rem;
  min-height: 126px;
}}

.home-card h3 {{
  margin: 0 0 0.45rem 0;
}}

.home-card p {{
  margin: 0;
  color: #cbd5e1;
}}
</style>
""",
        unsafe_allow_html=True,
    )

