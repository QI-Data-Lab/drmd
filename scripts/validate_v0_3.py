#!/usr/bin/env python3
from lxml import etree
import sys

def validate(xml_file, xsd_file):
    with open(xsd_file, 'rb') as f:
        schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
    doc = etree.parse(xml_file)
    schema.assertValid(doc)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python validate_v0_2.py <xml_file> <xsd_file>')
        sys.exit(1)
    validate(sys.argv[1], sys.argv[2])
    print('Validation succeeded')
