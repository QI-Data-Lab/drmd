#!/usr/bin/env python3
import os
import glob
import unittest
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(__file__))
XSD = os.path.join(ROOT, 'v0.2.0', 'xsd', 'drmd.xsd')
XSL = os.path.join(ROOT, 'v0.2.0', 'xsl', 'drmd.xsl')
IMPORTS = os.path.join(ROOT, 'imports')


class TestSchemaAndExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure imports exist
        assert os.path.isdir(IMPORTS), 'imports/ folder missing'
        # Load schema
        with open(XSD, 'rb') as f:
            schema_doc = etree.parse(f)
            cls.schema = etree.XMLSchema(schema_doc)
        # Load XSLT
        with open(XSL, 'rb') as f:
            cls.xslt = etree.XSLT(etree.parse(f))

    def test_examples_validate(self):
        xml_dir = os.path.join(ROOT, 'v0.2.0', 'xml')
        for xml_path in glob.glob(os.path.join(xml_dir, '*.xml')):
            with self.subTest(xml=xml_path):
                doc = etree.parse(xml_path)
                self.schema.assertValid(doc)

    def test_transform_to_html(self):
        xml_dir = os.path.join(ROOT, 'v0.2.0', 'xml')
        for xml_path in glob.glob(os.path.join(xml_dir, '*.xml')):
            with self.subTest(xml=xml_path):
                doc = etree.parse(xml_path)
                html = self.xslt(doc)
                s = str(html)
                self.assertIn('<html', s.lower())
                self.assertIn('</html>', s.lower())


if __name__ == '__main__':
    unittest.main()

