# DRMD (Digital Reference Material Document)

This repository provides the DRMD XML schema (v0.2.0), example XML files, an XSLT for HTML rendering, a Streamlit app to author and validate DRMD documents, and utilities/tests to keep everything consistent.

Current version: v0.2.0

## Repository Structure

```
v0.2.0/
  xsd/            # Canonical schema (drmd.xsd)
  xsl/            # Stylesheets (drmd.xsl)
  xml/            # Example XML documents
  html/           # Generated example HTML
imports/          # Local copies of external dependencies
  dcc.xsd
  SI_Format.xsd
  xmldsig-core-schema.xsd
  qudt.ttl
webapp/           # Streamlit app
  app.py          # Launcher (sets absolute resource paths)
  app_impl.py     # App implementation
scripts/          # Utilities
  validate_v0_2.py
  xml2html.py
  convert_v0_1_to_v0_2.py
  normalize_v0_2_examples.py
tests/            # Unit tests
  test_v0_2_0.py
docs/
  help.md         # App help loaded inside Streamlit
Makefile          # Common dev tasks
Dockerfile        # Container image for the app
```

## DRMD Schema (v0.2.0)

The canonical schema lives at `v0.2.0/xsd/drmd.xsd` and imports external dependencies from `../../imports/`:
- DCC: `imports/dcc.xsd`
- D‑SI: `imports/SI_Format.xsd`
- XMLDSIG: `imports/xmldsig-core-schema.xsd`

Top-level elements of a DRMD document:
- `administrativeData` (coreData, producer, respPersons)
- `materials` (one or more materials)
- `materialPropertiesList` (results and quantities)
- `statements` (official/custom statements)
- optional `comment`, `document`, and 0..n `ds:Signature`

See `docs/help.md` for the end-user mapping and guidance.

## Setup

Prerequisite: Python 3.12+

Install and validate:
```
make install     # create venv + install deps
make check       # normalize + validate + html + tests
```

Run the app:
```
make app         # http://localhost:8501
```

The app includes Diagnostics (compile XSD/XSL, validate examples) and a Help tab that loads `docs/help.md`.

## Utilities

- `scripts/validate_v0_2.py`: validate XML against `v0.2.0/xsd/drmd.xsd`
- `scripts/xml2html.py`: transform XML → HTML via `v0.2.0/xsl/drmd.xsl`
- `scripts/normalize_v0_2_examples.py`: normalize example XMLs to current structure

Examples:
```
python scripts/validate_v0_2.py v0.2.0/xml/BAM-F017.xml v0.2.0/xsd/drmd.xsd
python scripts/xml2html.py v0.2.0/xml/BAM-F017.xml v0.2.0/xsl/drmd.xsl v0.2.0/html/BAM-F017.html
```

## Tests
```
python -m unittest tests/test_v0_2_0.py -v
```

## Containerization

Build and run the Streamlit app in Docker:
```
make docker-build
make docker-run    # http://localhost:8501
```

The container sets `DRMD_XSD_PATH`, `DRMD_XSL_PATH`, and `QUDT_TTL_PATH` to repository locations.

## Notes

- Root-level duplicates (`xsd/`, `xsl/`, `xml/`, `html/`) are removed. Use the versioned folder `v0.2.0/` as the source of truth.
- `imports/` holds offline copies of external schemas and QUDT data used by the app.

## License
LGPL-3.0 (schema). See headers in source files where applicable.

