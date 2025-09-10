## DRMD App Help

This application creates and validates Digital Reference Material Documents (DRMD) as XML, and renders HTML using XSLT.

### Repository Layout (relevant to the app)

- `v0.2.0/xsd/drmd.xsd`: Canonical DRMD schema (imports DCC, SI, and XMLDSIG via `../../imports/...`).
- `v0.2.0/xsl/drmd.xsl`: Stylesheet for HTML rendering.
- `v0.2.0/xml/`: Example DRMD XML documents.
- `imports/`: Local copies of external schemas and QUDT data: `dcc.xsd`, `SI_Format.xsd`, `xmldsig-core-schema.xsd`, `qudt.ttl`.
- `webapp/`: Streamlit application (`app.py` launcher, `app_impl.py` implementation).

### DRMD Structure (v0.2.0)

Root: `drmd:digitalReferenceMaterialDocument` with attributes:

- `administrativeData`
  - `coreData`: `titleOfTheDocument`, `uniqueIdentifier`, `documentIdentifiers`, `validity`
  - `referenceMaterialProducer`: `name`, `contact`, `organizationIdentifiers`
  - `respPersons`
- `materials`: list of `material` (name, description, minimumSampleSize, materialIdentifiers)
- `materialPropertiesList`: list of `materialProperties` (name, results [result → data → list/quantity])
- `statements`: official and custom statements
- `comment` (optional), `document` (optional), `ds:Signature` (0..n)

### Typical Workflow

1. Fill Administrative Data
2. Add Materials and sample sizes
3. Define Material Properties and Results (values, units, uncertainties)
4. Add Statements and optional comment/document
5. Validate & Export → Download XML and HTML

### Validation & Rendering

- Schema is compiled from `v0.2.0/xsd/drmd.xsd` (local imports under `imports/`).
- HTML is generated via `v0.2.0/xsl/drmd.xsl`.
- Diagnostics (in the app) compile XSD/XSL and validate example XMLs.

### Troubleshooting

- If “XSL Transformation Error” appears, ensure the stylesheet exists and the app points to `v0.2.0/xsl/drmd.xsl` (the launcher sets this automatically).
- If schema validation fails, expand Diagnostics to see the exact error.

