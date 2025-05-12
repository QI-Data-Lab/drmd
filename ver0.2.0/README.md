
# Digital Reference Material Document (DRMD) - Version 0.2.0

## Overview

The **Digital Reference Material Document (DRMD)** is a standardized XML schema for the digital representation of reference material certificates.  
This version (`v0.2.0`) introduces a **refactored and modular structure**, improving clarity, scalability, and alignment with best practices for machine-readable certificates.

The schema is developed by **Bundesanstalt für Materialforschung und -prüfung (BAM)** and aligns with the QI-Digital initiative.

---

## What's New in Version 0.2.0

This version introduces **breaking changes** compared to `v0.1.0`:

- 📦 **Separation of core document elements for clarity and reuse:**
  - `materialClassList` is now a standalone root element.
  - `materialPropertiesList` is now a standalone root element.
  - `statements` are now separated from `administrativeData` and placed at root level.
- ❌ Removed the nested `materialPropertiesList` inside `materialClass`.
- 🛠 Clean modularization enables clearer referencing between materials, properties, and classes.
- ✅ The changes enhance:
  - **Reusability of classes and properties**
  - **Clean separation of certificate-wide statements**
  - **Simplified integration in digital infrastructures, data spaces, and linked data scenarios**

---

## Schema structure

````

digitalReferenceMaterialDocument
├── administrativeData
│   ├── coreData
│   ├── materials
│   ├── referenceMaterialProducer
│   └── respPersons
├── materialClassList
│   └── materialClass
│       ├── reference
│       ├── classID
│       └── link (optional)
├── materialPropertiesList
│   └── materialProperties
│       ├── name
│       ├── description
│       ├── procedures
│       ├── results
│       └── measurementMetaData
├── statements
│   ├── intendedUse
│   ├── storageInformation
│   └── other statements...
├── comment (optional)
├── document (optional)
└── Signature (0..n)
````


## Folder Structure

````

v0.2.0/
├── xsd/            # DRMD XML Schema Definition (XSD)
│   └── drmd.xsd
├── xsl/            # XSLT stylesheets for transforming DRMD XML to HTML
│   └── drmd\_visualization.xslt
├── xml/            # Example DRMD XML files (converted from PDF)
│   └── drmd-sample-v0.2.0.xml
├── html/           # Example human-readable HTML (generated from XML + XSL)
│   └── drmd-sample-v0.2.0.html
└── README.md       # Documentation for this version

````

---

## Usage

### 1. Validate your DRMD documents
```bash
Use xsd/drmd.xsd to validate your DRMD XML documents.
````

### 2. Transform to human-readable HTML

```bash
Apply the stylesheet in xsl/drmd_visualization.xslt to your XML file.
```

### 3. Examples

* See `xml/drmd-sample-v0.2.0.xml` as a valid document following the new structure.
* Check `html/drmd-sample-v0.2.0.html` for the rendered certificate.

---

## Compatibility

| Field                    | Value                                                |
| ------------------------ | ---------------------------------------------------- |
| Namespace                | [https://example.org/drmd](https://example.org/drmd) |
| Schema Version Attribute | schemaVersion="0.2.0"                                |
| Backward Compatibility   | ❌ No (breaking changes)                              |

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
