#!/usr/bin/env python3
from lxml import etree as ET
from copy import deepcopy

NS = {
    'drmd': 'https://example.org/drmd',
    'dcc': 'https://ptb.de/dcc',
    'si': 'https://ptb.de/si',
}

def q(ns, tag):
    return f"{{{NS[ns]}}}{tag}"

def normalize(path: str) -> None:
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(path, parser)
    root = tree.getroot()

    # Ensure order: administrativeData, statements, materials, materialPropertiesList
    adm = root.find('drmd:administrativeData', namespaces=NS)
    stm = root.find('drmd:statements', namespaces=NS)
    mats = root.find('drmd:materials', namespaces=NS)
    mplist = root.find('drmd:materialPropertiesList', namespaces=NS)
    # Remove if present for controlled reinsertion
    for node in [stm, mats, mplist]:
        if node is not None:
            root.remove(node)
    # Ensure statements exists
    if stm is None:
        stm = ET.Element(q('drmd', 'statements'))
    # Reinsert in correct order
    insert_at = 0
    if adm is not None:
        # Find index of adm in current children
        elems = [e for e in root if isinstance(e.tag, str)]
        if adm in elems:
            insert_at = elems.index(adm) + 1
        else:
            # If adm got detached for some reason, add it first
            root.insert(0, adm)
            insert_at = 1
    root.insert(insert_at, stm)
    if mats is not None:
        root.insert(insert_at + 1, mats)
    if mplist is not None:
        root.insert(insert_at + 2, mplist)

    # Fix minimumSampleSize itemQuantity element name
    for ms in root.findall('.//drmd:minimumSampleSize', namespaces=NS):
        for dq in ms.findall('dcc:itemQuantity', namespaces=NS):
            dq.tag = q('drmd', 'itemQuantity')

    # Normalize results block under materialPropertiesList
    for mp in root.findall('.//drmd:materialProperties', namespaces=NS):
        results = mp.find('drmd:results', namespaces=NS)
        if results is None:
            continue
        # result elements should be dcc:result
        for res in list(results):
            if res.tag == q('drmd', 'result'):
                res.tag = q('dcc', 'result')
            # children name/description/data
            for ch in list(res):
                if ch.tag == q('drmd', 'name'):
                    ch.tag = q('dcc', 'name')
                elif ch.tag == q('drmd', 'description'):
                    ch.tag = q('dcc', 'description')
                elif ch.tag == q('drmd', 'data'):
                    ch.tag = q('dcc', 'data')
                # within data, ensure list/quantity are dcc
                if ch.tag == q('dcc', 'data'):
                    for node in list(ch):
                        if node.tag == q('drmd', 'list'):
                            node.tag = q('dcc', 'list')
                        # Convert quantities at any depth under data
                        for qty in ch.findall('.//drmd:quantity', namespaces=NS):
                            qty.tag = q('dcc', 'quantity')
                            for pi in qty.findall('drmd:propertyIdentifiers', namespaces=NS):
                                qty.remove(pi)
    # Global cleanup: remove any remaining drmd:propertyIdentifiers blocks
    for pi in root.findall('.//drmd:propertyIdentifiers', namespaces=NS):
        parent = pi.getparent()
        if parent is not None:
            parent.remove(pi)

    # Normalize statements children: ensure drmd:name and drmd:content wrappers
    stm = root.find('drmd:statements', namespaces=NS)
    if stm is not None:
        for st in list(stm):
            # Convert dcc:name element to drmd:name
            for dn in st.findall('dcc:name', namespaces=NS):
                dn.tag = q('drmd', 'name')
            # Wrap any direct dcc:content nodes into drmd:content
            direct_dcc_content = [c for c in list(st) if c.tag == q('dcc', 'content')]
            if direct_dcc_content:
                dc = ET.Element(q('drmd', 'content'))
                for c in direct_dcc_content:
                    st.remove(c)
                    dc.append(c)
                # Insert after name if present, else at start
                name_el = st.find('drmd:name', namespaces=NS)
                if name_el is not None:
                    idx = list(st).index(name_el) + 1
                    st.insert(idx, dc)
                else:
                    st.insert(0, dc)

    tree.write(path, pretty_print=True, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: normalize_v0_2_examples.py <xmlfile> [<xmlfile> ...]')
        sys.exit(1)
    for p in sys.argv[1:]:
        normalize(p)
        print(f'Normalized {p}')
