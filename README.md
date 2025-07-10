# Digital Reference Material Document (DRMD) Project

The Digital Reference Material Document (DRMD) project aims to create a standardized digital format for reference material certificates. This project is developed by the Bundesanstalt für Materialforschung und -prüfung (BAM) and is partially funded by the QI-Digital project from BMWK. The DRMD schema is based on the existing Digital Calibration Certificate (DCC) schema and complies with the requirements of the ISO 33401 standard for reference material certificates


## Schema Information

The DRMD schema is designed to encapsulate all necessary data for reference material certificates, ensuring consistency and adherence to international standards.

### Key Features:

- **Administrative Data**: Core information about the document, items, producer information, responsible persons, and relevant statements.
- **Measurement Results**: Structured representation of measurement data, including certified values and uncertainties.

### Documentation:

The development of the DRMD is partially funded and supported by the QI-Digital project from BMWK. Further documentation and project details can be found [here](https://www.bam.de/Content/EN/Projects/QI-Digital/qi-digital.html).

## Dependencies

The DRMD schema builds upon the existing DCC schema. You can find the DCC schema [here](https://ptb.de/dcc/v3.2.1/DCC.xsd). 

### External Standards:

- **ISO 33401**: The DRMD schema is designed to meet the requirements of the ISO 33401 standard for reference material certificates.

## Usage

### XML Schema Definition (XSD)

The `drmd.xsd` file defines the structure of the DRMD. This file is essential for creating and validating XML documents that conform to the DRMD specifications.

### Sample XML Document

The `dcrm-0001.xml` file is a sample XML document that adheres to the `drmd.xsd` schema. Use this as a reference for creating your own DRMD XML documents.

### XSLT Stylesheet

The `drmc_visualization.xsl` file is an XSLT stylesheet that can be used to transform DRMD XML documents into human-readable HTML format. To use this stylesheet, reference it in your XML document as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="drmd.xsl"?>
<drmd:digitalReferenceMaterialDocument >
  <!-- XML content here -->
</drmd:digitalReferenceMaterialDocument>
```


## Project Structure

```
dcrm-project/
├── v0.0.1/
│   ├── xml/
│   │   ├── dcrm-001.xml
│   │   └── other-data-files.xml
│   ├── xsd/
│   │   ├── drmd.xsd
│   │   └── other-data-files.xml
│   ├── xslt/
│   │   ├── drmd.xslt
│   │   └── other-xslt-files.xslt
│   ├── html-output/
│   │   ├── dcrm-001.html
│   │   └── other-html-files.html
├── scripts/
│   ├── validate-schema.py
│   └── other-scripts.py
├── README.md
└── LICENSE
```

## Digital Reference Material Document (DRMD) Structure

The `drmd` (Digital Reference Material Document) structure is defined using an XSD schema and includes the following key components:

1. **digitalReferenceMaterialDocument**
    - **administrativeData**
        - **coreData**
            - titleOfTheDocument
            - uniqueIdentifier
            - periodOfValidity
            - dateOfDispatch
            - dateOfCertificateApproval
            - dataOfIssue
            - dateOfValidity
        - **referenceMaterialProducer**
            - name
            - contact

        - **items**
            - item
                - name
                - description
                - minimumSampleSize
                - identifications

        - **statements**
            - intendedUse
            - commutability
            - storageInformation
            - instructionsForHandlingAndUse
            - metrologicalTraceability
            - healthAndSafetyInformation
            - subcontractors
            - legalNotice
            - referenceToCertificationReport
            - statement
        - **respPersons**
            - respPerson

    - **measurementResults**
        - results
            - result

    - **digitalSignature**

    - **comments**


## Getting Started

### Prerequisites

- Python 3.x
- lxml library (`pip install lxml`)

### Utilities

Several helper scripts are provided in `scripts`.

- **convert_v0_1_to_v0_2.py** – convert an XML file from the `v0.1.x` format
  to the `v0.2.0` layout.

  ```bash
  python scripts/convert_v0_1_to_v0_2.py v0.1.1/xml/BAM-F017.xml \
      v0.2.0/xml/BAM-F017.xml
  ```

- **validate_v0_2.py** – validate a `v0.2.0` XML document against the schema.

  ```bash
  python scripts/validate_v0_2.py v0.2.0/xml/BAM-F017.xml \
      v0.2.0/xsd/drmd.xsd
  ```

- **xml2html.py** – transform a DRMD XML document into HTML using the
  project XSLT stylesheet.

  ```bash
  python scripts/xml2html.py v0.2.0/xml/BAM-F017.xml \
      v0.2.0/xsl/drmd.xsl v0.2.0/html/BAM-F017.html
  ```


## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

## License
This XML Schema Definition (XSD) is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, version 3 of the License.

This XSD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.