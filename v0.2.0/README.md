# Digital Reference Material Document (DRMD) - Version 0.2.0

This folder contains the **current stable release** of the DRMD schema.

## Overview

This version (`v0.2.0`) introduces a **refactored and modular structure**, improving clarity, scalability, and alignment with best practices for machine-readable certificates.

The schema is developed by **Bundesanstalt für Materialforschung und -prüfung (BAM)** and aligns with the QI-Digital initiative.

---

## What's New in Version 0.2.0

This version introduces **breaking changes** compared to `v0.1.0`:

 - **Separation of core document elements for clarity and reuse:**
  - `materials` is now a standalone root element.
  - `materialPropertiesList` is now a standalone root element.
  - `statements` are now separated from `administrativeData` and placed at root level.
 - Clean modularization enables clearer referencing between materials, properties
 - The changes enhance:
  - **Reusability of classes and properties**
  - **Clean separation of certificate-wide statements**
  - **Simplified integration in digital infrastructures, data spaces, and linked data scenarios**

---

## Schema structure

````
digitalReferenceMaterialDocument
├── administrativeData
│   ├── coreData
│   ├── referenceMaterialProducer
│   └── respPersons
├── statements
├── materials
│   └── material
│       ├── name
│       ├── description
│       ├── materialClass
├── materialPropertiesList
│   └── materialProperties
├── comment (optional)
├── document (optional)
└── Signature (0..n)
````


## Folder Structure

````

v0.2.0/
├── xsd/            # DRMD XML Schema Definition (XSD)
│   └── drmd.xsd    # Imports ../../imports/{dcc.xsd, SI_Format.xsd, xmldsig-core-schema.xsd}
├── xsl/            # XSLT stylesheets for transforming DRMD XML to HTML
│   └── drmd.xsl
├── xml/            # Example DRMD XML files
│   ├── BAM-F017.xml
│   └── BAM-M375a.xml
├── html/           # Example human-readable HTML (generated from XML + XSL)
│   ├── BAM-F017.html
│   └── BAM-M375a.html
└── README.md       # Documentation for this version

````

---

## Usage

### 1. Validate your DRMD documents
Use the versioned schema for v0.2.0:

```bash
python scripts/validate_v0_2.py v0.2.0/xml/BAM-F017.xml v0.2.0/xsd/drmd.xsd
```

For offline tooling, an alias with local imports is also available at `xsd/drmd.xsd`.

### 2. Transform to human-readable HTML

```bash
Apply the stylesheet in xsl/drmd.xsl to your XML file.
```

### 3. Examples

* See `xml/BAM-F017.xml` for a valid document following the new structure.
* Check `html/BAM-F017.html` for the rendered certificate.

---

## Compatibility

| Field                    | Value |
| ------------------------ | ------------------------------------------- |
| Namespace                | [https://example.org/drmd](https://example.org/drmd) |
| Schema Version Attribute | schemaVersion="0.2.0" |
| Backward Compatibility   | No (breaking changes) |

---

## Changelog

### v0.2.0 - May 2025

* Refactored schema structure.
* Introduced `materialClassList`, `materialPropertiesList`, and `statements` at root level.
* Modular and normalized schema layout.
* Updated supporting files and samples.

---

## License

This schema is published under the **GNU Lesser General Public License (LGPL) v3.0**.

---

## References

* [QI-Digital Project](https://www.bam.de/qi-digital)
* [ISO 17034:2016](https://www.iso.org/standard/29357.html)
* [ISO Guide 31:2015](https://www.iso.org/standard/59573.html)
