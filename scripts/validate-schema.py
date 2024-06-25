import xmlschema
import sys

def validate_xml(xml_file: str, xsd_file: str):
    try:
        schema = xmlschema.XMLSchema(xsd_file)
        if schema.is_valid(xml_file):
            print(f"{xml_file} is valid according to {xsd_file}")
        else:
            print(f"{xml_file} is not valid according to {xsd_file}")
            for error in schema.iter_errors(xml_file):
                print(error)
    except xmlschema.XMLSchemaException as e:
        print(f"An error occurred while processing the schema: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_xml.py <xml_file> <xsd_file>")
    else:
        xml_file = sys.argv[1]
        xsd_file = sys.argv[2]
        validate_xml(xml_file, xsd_file)
