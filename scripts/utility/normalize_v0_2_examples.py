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

    # Ensure order: administrativeData, materials, materialPropertiesList, statements (per v0.2.0)
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
    # Reinsert in correct order (adm already present)
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
    # materials
    if mats is not None:
        root.insert(insert_at, mats)
        insert_at += 1
    # materialPropertiesList
    if mplist is not None:
        root.insert(insert_at, mplist)
        insert_at += 1
    # statements last
    root.insert(insert_at, stm)

    # Fix minimumSampleSize itemQuantity element name (use dcc:itemQuantity per v0.2.0)
    for ms in root.findall('.//drmd:minimumSampleSize', namespaces=NS):
        # convert any drmd:itemQuantity back to dcc:itemQuantity
        for dq in ms.findall('drmd:itemQuantity', namespaces=NS):
            dq.tag = q('dcc', 'itemQuantity')

    # Normalize results block under materialPropertiesList to DRMD result/data/list/quantity
    for mp in root.findall('.//drmd:materialProperties', namespaces=NS):
        results = mp.find('drmd:results', namespaces=NS)
        if results is None:
            continue
        # result elements should be drmd:result
        for res in list(results):
            if res.tag == q('dcc', 'result'):
                res.tag = q('drmd', 'result')
            # children name/description/data elements are in drmd namespace but typed with dcc types
            for ch in list(res):
                if ch.tag == q('dcc', 'name'):
                    ch.tag = q('drmd', 'name')
                elif ch.tag == q('dcc', 'description'):
                    ch.tag = q('drmd', 'description')
                elif ch.tag == q('dcc', 'data'):
                    ch.tag = q('drmd', 'data')
                # within data, ensure list/quantity are drmd
                if ch.tag == q('drmd', 'data'):
                    for node in list(ch):
                        if node.tag == q('dcc', 'list'):
                            node.tag = q('drmd', 'list')
                        if node.tag == q('dcc', 'quantity'):
                            node.tag = q('drmd', 'quantity')
                    # also convert any nested quantities
                    for qty in ch.findall('.//dcc:quantity', namespaces=NS):
                        qty.tag = q('drmd', 'quantity')

    # Normalize statements children: use DCC richContentType (dcc:name optional + dcc:content)
    stm = root.find('drmd:statements', namespaces=NS)
    if stm is not None:
        for st in list(stm):
            # Convert any mistaken drmd:name/content back to dcc:name/content
            for rn in st.findall('drmd:name', namespaces=NS):
                rn.tag = q('dcc', 'name')
            for rc in st.findall('drmd:content', namespaces=NS):
                # unwrap drmd:content by hoisting its children (dcc:content expected)
                idx = list(st).index(rc)
                for child in list(rc):
                    st.insert(idx, child)
                    idx += 1
                st.remove(rc)
            # flatten any dcc:content wrappers that incorrectly nest dcc:content
            for dc in list(st):
                if dc.tag == q('dcc', 'content'):
                    # If this dcc:content contains nested dcc:content elements, hoist them
                    nested = [c for c in list(dc) if c.tag == q('dcc', 'content')]
                    if nested:
                        idx = list(st).index(dc)
                        for child in nested:
                            st.insert(idx, child)
                            idx += 1
                        st.remove(dc)

    tree.write(path, pretty_print=True, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: normalize_v0_2_examples.py <xmlfile> [<xmlfile> ...]')
        sys.exit(1)
    for p in sys.argv[1:]:
        normalize(p)
        print(f'Normalized {p}')
