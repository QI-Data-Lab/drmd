import xml.etree.ElementTree as ET
import argparse

NS = {'drmd': 'https://example.org/drmd'}


def convert(xml_in, xml_out):
    tree = ET.parse(xml_in)
    root = tree.getroot()
    root.attrib['schemaVersion'] = '0.2.0'

    admin = root.find('drmd:administrativeData', NS)
    materials = None
    statements = None
    if admin is not None:
        materials = admin.find('drmd:materials', NS)
        if materials is not None:
            admin.remove(materials)
        statements = admin.find('drmd:statements', NS)
        if statements is not None:
            admin.remove(statements)

    children = list(root)
    idx_admin = children.index(admin) if admin is not None else 0
    if materials is not None:
        root.insert(idx_admin + 1, materials)
    if statements is not None:
        # find materialPropertiesList to insert before it
        mat_props = root.find('drmd:materialPropertiesList', NS)
        if mat_props is not None:
            idx = list(root).index(mat_props)
            root.insert(idx + 1, statements)
        else:
            root.append(statements)

    tree.write(xml_out, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert DRMD v0.1.x XML to v0.2.0 format')
    parser.add_argument('xml_in')
    parser.add_argument('xml_out')
    args = parser.parse_args()
    convert(args.xml_in, args.xml_out)
