# tabs/settings.py
import streamlit as st
import os as _os
from pathlib import Path as _P

try:
    from lxml import etree as _etree
except ImportError:
    _etree = None

try:
    import xmlschema as _xmlschema
except ImportError:
    _xmlschema = None

from utils import DEFAULT_XSD_PATH, DEFAULT_XSL_PATH, load_qudt

def render_settings():
    st.markdown("### Settings")
    # Initialize settings values
    if 'settings_xsd_path' not in st.session_state:
        st.session_state.settings_xsd_path = DEFAULT_XSD_PATH
    if 'settings_xsl_path' not in st.session_state:
        st.session_state.settings_xsl_path = DEFAULT_XSL_PATH
    if 'settings_qudt_path' not in st.session_state:
        st.session_state.settings_qudt_path = _os.environ.get('QUDT_TTL_PATH', '')

    colA, _ = st.columns([2, 1])
    with colA:
        xsd_in = st.text_input('XSD Path', st.session_state.settings_xsd_path)
        xsl_in = st.text_input('XSL Path', st.session_state.settings_xsl_path)
        qudt_in = st.text_input('QUDT TTL Path', st.session_state.settings_qudt_path)
        if st.button('Apply Paths', key='apply_paths_btn'):
            # Update environment and module defaults
            _os.environ['DRMD_XSD_PATH'] = xsd_in
            _os.environ['DRMD_XSL_PATH'] = xsl_in
            if qudt_in:
                _os.environ['QUDT_TTL_PATH'] = qudt_in
            
            # This is tricky, but we respect the original code's intention
            # to modify the global state of the *running module*.
            # In a multi-file app, this is better handled by session_state
            # or a dedicated config object, but for minimal changes:
            globals()['DEFAULT_XSD_PATH'] = xsd_in
            globals()['DEFAULT_XSL_PATH'] = xsl_in
            
            # Refresh QUDT cache
            try:
                load_qudt.clear()
                # Re-run the load_qudt from utils
                # This global modification is also from the original code.
                from .. import utils
                utils.qudt_quantities = load_qudt()
            except Exception:
                pass
            st.success('Paths updated')

    # Diagnostics (on-demand)
    st.markdown('---')
    st.markdown('### Diagnostics')
    if st.button('Run Diagnostics', key='run_diagnostics'):
        if _etree is None:
            st.error("lxml is not installed. Cannot run diagnostics.")
            return
        if _xmlschema is None:
            st.error("xmlschema is not installed. Cannot run diagnostics.")
            return
            
        from lxml import etree as _etree
        import xmlschema as _xmlschema
        
        st.write(f"XSD: `{DEFAULT_XSD_PATH}`")
        st.write(f"XSL: `{DEFAULT_XSL_PATH}`")
        st.write(f"QUDT TTL: `{_os.environ.get('QUDT_TTL_PATH','')}`")

        # Compile schema
        xsd_ok = False
        xsd_err = None
        try:
            _schema_doc = _etree.parse(DEFAULT_XSD_PATH)
            _schema = _etree.XMLSchema(_schema_doc)
            xsd_ok = True
        except Exception as e:
            xsd_err = str(e)
        st.write(f"XSD compile: {'✅' if xsd_ok else '❌'}")
        if xsd_err:
            st.code(xsd_err)

        # Compile XSL
        xsl_ok = False
        xsl_err = None
        try:
            _xslt = _etree.XSLT(_etree.parse(DEFAULT_XSL_PATH))
            xsl_ok = True
        except Exception as e:
            xsl_err = str(e)
        st.write(f"XSLT compile: {'✅' if xsl_ok else '❌'}")
        if xsl_err:
            st.code(xsl_err)

        # Validate examples from the detected version folder
        try:
            xsd_dir = _P(DEFAULT_XSD_PATH).resolve().parent
            version_dir = xsd_dir.parent
            xml_dir = version_dir / 'xml'
            examples = sorted([str(p) for p in xml_dir.glob('*.xml')])
        except Exception:
            examples = []
        if examples:
            st.write("Example XML validation:")
        if xsd_ok:
            try:
                _xs = _xmlschema.XMLSchema(DEFAULT_XSD_PATH)
            except Exception:
                _xs = None
            for ex in examples:
                try:
                    _schema.assertValid(_etree.parse(ex))
                    st.write(f"- ✅ Valid: `{ex}`")
                except Exception as ve:
                    st.write(f"- ❌ Invalid: `{ex}`")
                    st.code(str(ve))
                    if _xs is not None:
                        for err in _xs.iter_errors(ex):
                            st.code(str(err))
        else:
            for ex in examples:
                st.write(f"- ⚠️ Skipped (schema failed): `{ex}`")
    else:
        st.info("Click 'Run Diagnostics' to compile schema/XSL and validate bundled example XML files.")