import os, sys
from pathlib import Path

# Reuse the original webapp code but adapt schema/XSL paths to the unified repo layout.

BASE_DIR = Path(__file__).resolve().parent.parent
XSD_PATH = BASE_DIR / "v0.2.0" / "xsd" / "drmd.xsd"
XSL_PATH = BASE_DIR / "v0.2.0" / "xsl" / "drmd.xsl"
QUDT_PATH = BASE_DIR / "imports" / "qudt.ttl"

if not XSD_PATH.exists():
    raise FileNotFoundError(f"DRMD schema not found at {XSD_PATH}")
if not XSL_PATH.exists():
    raise FileNotFoundError(f"DRMD XSL not found at {XSL_PATH}")

# Inject variables expected by the legacy app implementation.
DEFAULT_XSD_PATH = str(XSD_PATH)
DEFAULT_XSL_PATH = str(XSL_PATH)

# Import the original application source (vendored) or inline minimal launcher.
# To keep history clear we vendor the previous single-file app as module webapp_impl.

from importlib import util

_SRC_FILE = BASE_DIR / "webapp" / "app_impl.py"
# Ensure impl can locate resources via environment variables before module import
os.environ.setdefault("QUDT_TTL_PATH", str(QUDT_PATH))
os.environ.setdefault("DRMD_XSD_PATH", DEFAULT_XSD_PATH)
os.environ.setdefault("DRMD_XSL_PATH", DEFAULT_XSL_PATH)
spec = util.spec_from_file_location("webapp_impl", _SRC_FILE)
webapp_impl = util.module_from_spec(spec)
sys.modules[spec.name] = webapp_impl
spec.loader.exec_module(webapp_impl)  # type: ignore

# Patch the constants inside the loaded module.
setattr(webapp_impl, 'DEFAULT_XSD_PATH', DEFAULT_XSD_PATH)
setattr(webapp_impl, 'DEFAULT_XSL_PATH', DEFAULT_XSL_PATH)
if QUDT_PATH.exists():
    setattr(webapp_impl, 'QUDT_TTL_PATH', str(QUDT_PATH))

# Update namespace constant to the current canonical namespace if it changed.
CANON_NS = "https://example.org/drmd"  # adjust if schema targetNamespace changed

if hasattr(webapp_impl, 'ALLOWED_TITLES'):
    pass  # leave as-is

# Patch load_qudt to use repository path for qudt.ttl
try:
    import streamlit as st  # ensure available for cache decorator
    from rdflib import Graph, Namespace

    @st.cache_data
    def _patched_load_qudt():
        ttl_path = getattr(webapp_impl, 'QUDT_TTL_PATH', str(QUDT_PATH))
        g = Graph(); g.parse(ttl_path, format='turtle')
        Q = Namespace('http://qudt.org/schema/qudt/')
        res = {}
        for s in g.subjects(None, Q.QuantityKind):
            qn = s.split('/')[-1]
            res[qn] = [u.split('/')[-1] for u in g.objects(s, Q.applicableUnit)] or ['Custom']
        return res

    # Replace function and prime the cache
    setattr(webapp_impl, 'load_qudt', _patched_load_qudt)
    setattr(webapp_impl, 'qudt_quantities', _patched_load_qudt())
except Exception:
    # If patching fails we leave the original function; app may handle errors.
    pass

# Streamlit expects top-level code; re-export run context.
for name in dir(webapp_impl):
    if name.startswith('_'): continue
    globals()[name] = getattr(webapp_impl, name)

# Sidebar status block: show resolved paths and availability
try:
    import streamlit as st
    from pathlib import Path as _Path
    st.sidebar.markdown("---")
    st.sidebar.markdown("### DRMD App Status")

    def _status(label: str, ok: bool, path: str = None):
        icon = "✅" if ok else "❌"
        if path is not None:
            st.sidebar.write(f"{icon} {label}: `{path}`")
        else:
            st.sidebar.write(f"{icon} {label}")

    _status("Schema (XSD)", _Path(DEFAULT_XSD_PATH).exists(), DEFAULT_XSD_PATH)
    _status("Stylesheet (XSL)", _Path(DEFAULT_XSL_PATH).exists(), DEFAULT_XSL_PATH)
    _qudt = getattr(webapp_impl, 'QUDT_TTL_PATH', str(QUDT_PATH))
    _status("QUDT (TTL)", _Path(_qudt).exists(), _qudt)
except Exception:
    pass

# Diagnostics expander: compile XSD/XSL and validate examples
try:
    import streamlit as st
    from lxml import etree as _etree
    import xmlschema as _xmlschema
    import glob as _glob
    from pathlib import Path as _P

    with st.expander("Diagnostics", expanded=False):
        root = _P(__file__).resolve().parent.parent
        imports_dir = root / 'imports'
        st.write(f"Imports folder: {'✅' if imports_dir.is_dir() else '❌'} `{imports_dir}`")
        for fname in ['dcc.xsd', 'SI_Format.xsd', 'xmldsig-core-schema.xsd']:
            p = imports_dir / fname
            st.write(f"- {'✅' if p.exists() else '❌'} {fname}: `{p}`")

        # Compile schema
        xsd_ok = False
        xsd_err = None
        try:
            _schema_doc = _etree.parse(DEFAULT_XSD_PATH)
            _schema = _etree.XMLSchema(_schema_doc)
            xsd_ok = True
        except Exception as e:
            xsd_err = str(e)
        st.write(f"XSD compile: {'✅' if xsd_ok else '❌'} `{DEFAULT_XSD_PATH}`")
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
        st.write(f"XSLT compile: {'✅' if xsl_ok else '❌'} `{DEFAULT_XSL_PATH}`")
        if xsl_err:
            st.code(xsl_err)

        # Validate example XMLs
        examples = sorted(_glob.glob(str(root / 'v0.2.0' / 'xml' / '*.xml')))
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
except Exception:
    pass
