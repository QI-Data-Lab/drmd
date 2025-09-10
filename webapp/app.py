import os, sys
from pathlib import Path

# Reuse the original webapp code but adapt schema/XSL paths to the unified repo layout.

BASE_DIR = Path(__file__).resolve().parent.parent
XSD_PATH = BASE_DIR / "v0.2.0" / "xsd" / "drmd.xsd"
XSL_PATH = BASE_DIR / "v0.2.0" / "xsl" / "drmd.xsl"
QUDT_PATH = BASE_DIR / "webapp_src" / "qudt.ttl"

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

_SRC_FILE = BASE_DIR / "webapp_src" / "app.py"
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

# Streamlit expects top-level code; re-export run context.
for name in dir(webapp_impl):
    if name.startswith('_'): continue
    globals()[name] = getattr(webapp_impl, name)
