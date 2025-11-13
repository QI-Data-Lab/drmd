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
st.set_page_config(
    page_title="Digital Reference Material Generator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Apply UI Settings & Custom CSS (from utils)

if "ui_font_scale" not in st.session_state:
    st.session_state.ui_font_scale = get_default_ui_settings()["font_scale"]

fs = st.session_state["ui_font_scale"]
pad = round(fs * 0.6, 2)

st.markdown(
    f"""
    <style>
    /* Import Google Fonts for professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global typography */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: {fs}rem !important;
        line-height: {fs * 1.6:.2f}rem !important;
        color: #1a1a1a;
    }}
    
    /* Main container with subtle gradient background */
    .main {{
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
    }}
    
    /* Sidebar styling - VERY LIGHT VIOLET/PURPLE TRANSPARENT BACKGROUND */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-right: 1px solid rgba(102, 126, 234, 0.15);
    }}
    
    /* All text in sidebar should be BLACK */
    [data-testid="stSidebar"] * {{
        color: #1a1a1a !important;
    }}
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {{
        color: #1a1a1a !important;
    }}
    
    /* Sidebar labels */
    [data-testid="stSidebar"] label {{
        color: #1a1a1a !important;
    }}
    
    /* Sidebar button styling */
    [data-testid="stSidebar"] .stButton button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }}
    
    [data-testid="stSidebar"] .stButton button:hover {{
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }}
    
    /* Tab container styling with icons */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: white;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #6c757d;
        font-weight: 500;
        padding: 0 1.5rem;
        transition: all 0.3s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #f8f9fa;
        color: #495057;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transform: translateY(-2px);
    }}
    
    /* Headers with gradient */
    h1 {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }}
    
    h2 {{
        color: #2c3e50;
        font-weight: 600;
        font-size: 1.8rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        padding-left: 1rem;
    }}
    
    h3 {{
        color: #34495e;
        font-weight: 600;
        font-size: 1.4rem;
        margin-top: 1rem;
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        background: white;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        font-weight: 600;
        color: #2c3e50;
        padding: 1rem;
        transition: all 0.3s ease;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: #f8f9fa;
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
    }}
    
    .streamlit-expanderContent {{
        background: white;
        border: 1px solid #e9ecef;
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1.5rem;
    }}
    
    /* Input fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {{
        border: 2px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        background: white !important;
    }}
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus, .stNumberInput input:focus {{
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }}
    
    /* Buttons */
    .stButton button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }}
    
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }}
    
    /* Success/Error/Warning/Info messages */
    .stSuccess {{
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 4px solid #dc3545;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
        border-left: 4px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 4px solid #17a2b8;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    /* Data editor/table styling */
    [data-testid="stDataFrame"] {{
        border: 2px solid #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        background: white;
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: #764ba2;
        background: #f8f9fa;
    }}
    
    /* Checkbox styling */
    .stCheckbox {{
        padding: 0.5rem 0;
    }}
    
    /* Code blocks */
    code {{
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        background: #f8f9fa;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: #e83e8c;
        font-size: 0.9em;
    }}
    
    pre {{
        background: #2c3e50;
        color: #ecf0f1;
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
    }}
    
    /* Dividers */
    hr {{
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }}
    
    /* Sticky elements */
    .sticky-right {{
        position: sticky;
        top: 3.5rem;
        background: white;
        z-index: 999;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }}
    
    /* Remove default Streamlit branding adjustments */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Scroll bar styling */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #f1f1f1;
        border-radius: 10px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Header with icon
st.markdown(
    """
    <div style='text-align: center; padding: 1rem 0 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
            🔬 Digital Reference Material Generator
        </h1>
        <p style='color: #6c757d; font-size: 1.1rem; font-weight: 400;'>
            Create, validate, and export digital reference material certificates
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# Robust session‑state initialisation (covers all tabs)
for k, v in SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------------------------------------------------------
# Sidebar utilities with enhanced styling
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='font-size: 1.5rem; margin: 0;'>⚙️ Controls</h2>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

xml_template = st.sidebar.file_uploader("📁 Load XML file", type=["xml"])
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
            st.sidebar.success('✅ XML schema validation: OK')
            st.session_state._last_validated_xml_hash = cur_hash
        else:
            st.sidebar.info('ℹ️ XML already validated.')
    except Exception as _e:
        first_line = str(_e).splitlines()[0]
        st.sidebar.error(f'❌ Schema validation failed: {first_line}')

if st.sidebar.button("🔄 Reset All"):
    st.session_state.clear(); st.rerun()

# Removed duplicate separator line here
# Render the UI settings panel in the sidebar
render_ui_settings_panel()

# -----------------------------------------------------------------------------
# Main Tabs list with icons
tabs = st.tabs([
    "📋 Administrative Data",
    "🧪 Materials",
    "📊 Properties",
    "📝 Statements",
    "💬 Comments & Documents",
    "✍️ Digital Signature",
    "✅ Validate & Export",
    "❓ Help",
    "⚙️ Settings"
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