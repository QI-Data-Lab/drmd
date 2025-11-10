# app.py
# -----------------------------------------------------------------------------
# Imports (include every lib used elsewhere so later tabs keep working)
import re, math, uuid, base64, functools, traceback, io
from datetime import date
from xml.dom import minidom
import xml.etree.ElementTree as ET
import random
import re

import pandas as pd
import streamlit as st
# Optional dependency: xmlschema (used for deep validation & diagnostics). Gracefully degrade if absent.
try:
    import xmlschema  # type: ignore
except ImportError:  # pragma: no cover - allows lightweight tests without xmlschema installed
    xmlschema = None  # sentinel
from rdflib import Graph, Namespace
from pathlib import Path as _Path
import os as _os

# pretty‑print / XSLT (used in Export tab later)
try:
    from lxml import etree
except ImportError:
    st.error("lxml is required. Please install it via pip install lxml.")

# Local module imports
from utils import (
    SESSION_DEFAULTS,
    get_default_ui_settings,
    render_ui_settings_panel,
    load_xml_into_state,
    DEFAULT_XSD_PATH
)
from tabs.administrative_data import render_administrative_data
from tabs.materials import render_materials
from tabs.properties import render_properties
from tabs.statements import render_statements
from tabs.comments_documents import render_comments_documents
from tabs.digital_signature import render_digital_signature
from tabs.validate_export import render_validate_export
from tabs.help import render_help
from tabs.settings import render_settings

# -----------------------------------------------------------------------------
# Page config & global CSS tweaks (consistent typography)
st.set_page_config(layout="wide")

# -----------------------------------------------------------------------------
# Apply UI Settings & Custom CSS (from utils)

if "ui_font_scale" not in st.session_state:
    st.session_state.ui_font_scale = get_default_ui_settings()["font_scale"]

fs = st.session_state["ui_font_scale"]
pad = round(fs * 0.6, 2)

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{
        font-size: {fs}rem !important;
        line-height: {fs * 1.4:.2f}rem !important;
    }}
    /* ... all other CSS rules from the original file ... */
    .sticky-right {{
        position: sticky;
        top: 3.5rem; /* adjust if you have headers above */
        background: white;
        z-index: 999;
        padding-bottom: 1rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Robust session‑state initialisation (covers all tabs)
for k, v in SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------------------------------------------------------
# Sidebar utilities (minimal – with schema validation feedback)
xml_template = st.sidebar.file_uploader("Load XML file", type=["xml"])
if xml_template:
    xml_bytes = xml_template.getvalue()
    if not st.session_state.template_loaded:
        load_xml_into_state(xml_bytes)
    # Schema validation feedback (debounced by content hash)
    try:
        import hashlib, lxml.etree as _etree
        cur_hash = hashlib.md5(xml_bytes).hexdigest()
        if cur_hash != st.session_state.get('_last_validated_xml_hash'):
            schema_doc = _etree.parse(DEFAULT_XSD_PATH)
            _etree.XMLSchema(schema_doc).assertValid(_etree.parse(io.BytesIO(xml_bytes)))
            st.sidebar.success('XML schema validation: OK')
            st.session_state._last_validated_xml_hash = cur_hash
        else:
            st.sidebar.info('XML already validated.')
    except Exception as _e:
        first_line = str(_e).splitlines()[0]
        st.sidebar.error(f'Schema validation failed: {first_line}')

if st.sidebar.button("Reset All"):
    st.session_state.clear(); st.rerun()

# Render the UI settings panel in the sidebar
render_ui_settings_panel()

# -----------------------------------------------------------------------------
# Main Tabs list
tabs = st.tabs([
    "Administrative Data", "Materials", "Properties", "Statements",
    "Comments & Documents", "Digital Signature", "Validate & Export", "Help", "Settings"
])

# -----------------------------------------------------------------------------
# Render each tab by calling its respective function
# -----------------------------------------------------------------------------
with tabs[0]:
    render_administrative_data()

with tabs[1]:
    render_materials()

with tabs[2]:
    render_properties()

with tabs[3]:
    render_statements()

with tabs[4]:
    render_comments_documents()

with tabs[5]:
    render_digital_signature()

with tabs[6]:
    render_validate_export()

with tabs[7]:
    render_help()

with tabs[8]:
    render_settings()