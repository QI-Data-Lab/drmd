# tabs/help.py
import streamlit as st
from pathlib import Path as _Path

def render_help():
    # Load help content from docs/help.md instead of hardcoding
    _help_md_path = _Path(__file__).resolve().parents[1] / 'docs' / 'help.md'
    try:
        with open(_help_md_path, 'r', encoding='utf-8') as _hf:
            st.markdown(_hf.read())
            st.markdown('---')
    except Exception as _e:
        st.warning(f"Could not load help markdown from `{_help_md_path}`. Showing built-in help.\n{_e}")

    st.markdown("#### Application Overview  \n"
                "The DRMD Generator is a Streamlit-based tool for creating **Digital Reference Material Documents** "
                "that conform to the DRMD XML schema. It walks you through each section of a Reference Material "
                "Certificate—metadata, materials, measurement properties, statements, signatures, and export.")

    st.markdown("#### Main Sections  \n"
                "- **Administrative Data**: Document title, persistent identifier, document identifiers, validity, "
                "producer and responsible-person details.  \n"
                "- **Materials** (formerly “Items”): Define one or more materials, their class, sample size, quantities "
                "and material identifiers.  \n"
                "- **Properties**: Specify measurement-property sets, certified values, uncertainties, and units.  \n"
                "- **Statements**: Capture official statements (intended use, traceability, safety, etc.) and add any custom notes.  \n"
                "- **Comments & Documents**: Attach external files or free-form remarks.  \n"
                "- **Digital Signature**: Apply XML Signature, e-seal, and timestamp options.  \n"
                "- **Validate & Export**: Run schema validation (drmd.xsd) and download your finished XML.  \n"
                "- **Help**: You’re here — background, schema mapping, dependencies, and version notes.")

    st.markdown("#### Schema Mapping  \n"
                "All fields map 1:1 to elements in **drmd.xsd** (version in `/drmd.xsd`). "
                "Key top-level XML elements are:  \n"
                "- `<digitalReferenceMaterialDocument>` (root)  \n"
                "- `<administrativeData>`: contains `<titleOfTheDocument>`, `<persistentIdentifier>`, `<documentIdentifiers>`, `<validity>`, `<referenceMaterialProducer>`, `<respPersons>`  \n"
                "- `<materials>` _(the former `<items>` element)_ with child `<material>` entries: `<name>`, `<description>`, `<materialClass>`, `<minimumSampleSize>`, `<itemQuantities>`, `<materialIdentifiers>`, `<isCertified>`  \n"
                "- `<measurementResults>`: holds `<materialProperty>` sets, `<result>` elements, and `<quantities>` tables.  \n"
                "- `<statements>`: wraps official and custom statements.  \n"
                "- `<ds:Signature>`: optional XML Digital Signature nodes.")

    st.markdown("#### How to Use  \n"
                "1. **Load** an existing DRMD XML (optional) — fields populate automatically.  \n"
                "2. Work through each tab, filling in all required fields. Hover over ⓘ icons for inline help.  \n"
                "3. **Generate** the Persistent Identifier (UUID) or supply your own.  \n"
                "4. In **Validate & Export**, click “Validate” to catch schema errors, then “Download” to save your XML.")

    st.markdown("#### Dependencies  \n"
                "- Python 3.8+  \n"
                "- `streamlit`  \n"
                "- `pandas`  \n"
                "- `rdflib`  \n"
                "- `xmlschema`  \n"
                "- `lxml`")

    st.markdown("#### External Standards  \n"
                "- Based on the Digital Calibration Certificate (DCC) schema.  \n"
                "- Conforms to **ISO 33401** for reference material certificates.")


    st.markdown("#### Further Documentation  \n"
                "- Full DRMD schema and docs: [link-to-drmd-documentation]  \n"
                "- Original DCC schema: [link-to-dcc-schema]")