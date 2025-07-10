from lxml import etree
import argparse


def transform(xml_file, xsl_file, html_file):
    xml_tree = etree.parse(xml_file)
    xslt_tree = etree.parse(xsl_file)
    transform = etree.XSLT(xslt_tree)
    result = transform(xml_tree)
    with open(html_file, 'wb') as f:
        f.write(etree.tostring(result, pretty_print=True, method='html'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform DRMD XML to HTML')
    parser.add_argument('xml', help='XML input file')
    parser.add_argument('xsl', help='XSL stylesheet')
    parser.add_argument('html', help='Output HTML file')
    args = parser.parse_args()
    transform(args.xml, args.xsl, args.html)
    print(f'Generated {args.html}')
