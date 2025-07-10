#!/usr/bin/env python3
import lxml.etree as ET
import sys
import argparse

def transform_xml(xml_file: str, xslt_file: str = None, output_html: str = None, verbose: bool = False):
    try:
        # Parse the XML file
        xml_tree = ET.parse(xml_file)
        
        # Determine the XSLT file
        if xslt_file is None:
            xslt_file = xml_file.replace('.xml', '.xsl')
        
        xslt_tree = ET.parse(xslt_file)
        transform = ET.XSLT(xslt_tree)
        
        # Transform the XML
        result_tree = transform(xml_tree)

        # Determine the output HTML file
        if output_html is None:
            output_html = xml_file.replace('.xml', '.html')
        
        # Output the HTML
        with open(output_html, 'wb') as html_file:
            html_file.write(ET.tostring(result_tree, pretty_print=True, method="html"))

        if verbose:
            print(f"Transformation complete. HTML output written to {output_html}.")
            print(f"Debug Log for transforming {xml_file} with {xslt_file}:\n")
            print(f"XSLT Messages:\n{'-'*50}\n")
            for entry in transform.error_log:
                print(f"{entry.message}\n")

    except ET.XSLTParseError as e:
        print(f"XSLT parsing error: {e}")
    except ET.XMLSyntaxError as e:
        print(f"XML syntax error: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform XML to HTML using XSLT.")
    parser.add_argument("xml_file", help="The XML file to transform.")
    parser.add_argument("xslt_file", nargs='?', help="The XSLT file to use for transformation. If not provided, tries to retrieve from the XML file name.")
    parser.add_argument("output_html", nargs='?', help="The output HTML file. If not provided, uses the same name as the XML file with .html extension.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed debug information.")
    parser.add_argument("-x", "--xslt_file_opt", help="The XSLT file to use for transformation as an optional argument.")
    parser.add_argument("-o", "--output_html_opt", help="The output HTML file as an optional argument.")

    args = parser.parse_args()
    
    # Determine which XSLT file to use
    xslt_file = args.xslt_file_opt if args.xslt_file_opt else args.xslt_file
    
    # Determine which output HTML file to use
    output_html = args.output_html_opt if args.output_html_opt else args.output_html
    
    transform_xml(args.xml_file, xslt_file, output_html, args.verbose)
