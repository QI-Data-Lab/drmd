# export.py
import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import math
import base64
from utils import add_if_valid, export_identifier_list, sanitize_xml_string

def export_materialProperties(ns_drmd, ns_dcc, ns_si):
    # Create the wrapping element for materialPropertiesList.
    mp_list_elem = ET.Element(f"{{{ns_drmd}}}materialPropertiesList")
    for mp in st.session_state.materialProperties:
        # Determine the certified status based on the set's name
        is_certified_flag = "true" if mp.get("name") == "Certified Properties Set" else "false"
        mp_elem = ET.SubElement(mp_list_elem, f"{{{ns_drmd}}}materialProperties", attrib={
            "isCertified": is_certified_flag
        })
        if mp.get("id", "").strip():
            mp_elem.set("id", mp.get("id").strip())
        # Required: name
        name_elem = ET.SubElement(mp_elem, f"{{{ns_drmd}}}name")
        ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(mp.get("name", ""))
        # Optional: description
        if mp.get("description", "").strip():
            desc_elem = ET.SubElement(mp_elem, f"{{{ns_drmd}}}description")
            ET.SubElement(desc_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(mp.get("description", ""))
        # Optional: procedures
        if mp.get("procedures", "").strip():
            # Create the main <drmd:procedures> container
            proc_elem = ET.SubElement(mp_elem, f"{{{ns_drmd}}}procedures")
            used_method_elem = ET.SubElement(proc_elem, f"{{{ns_dcc}}}usedMethod")
            name_elem = ET.SubElement(used_method_elem, f"{{{ns_dcc}}}name")
            ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = "Procedure"
            desc_elem = ET.SubElement(used_method_elem, f"{{{ns_dcc}}}description")
            ET.SubElement(desc_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(mp.get("procedures", ""))
        # Required: results
        results_elem = ET.SubElement(mp_elem, f"{{{ns_drmd}}}results")
        for res in mp.get("results", []):
            # drmd:result container
            res_elem = ET.SubElement(results_elem, f"{{{ns_drmd}}}result")
            # drmd:name (type dcc:textType)
            res_name_elem = ET.SubElement(res_elem, f"{{{ns_drmd}}}name")
            ET.SubElement(res_name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(res.get("result_name", ""))
            # drmd:description (type dcc:richContentType)
            if res.get("description", "").strip():
                res_desc_elem = ET.SubElement(res_elem, f"{{{ns_drmd}}}description")
                ET.SubElement(res_desc_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(res.get("description", ""))
            # drmd:data with drmd:list
            data_elem = ET.SubElement(res_elem, f"{{{ns_drmd}}}data")
            list_elem = ET.SubElement(data_elem, f"{{{ns_drmd}}}list")
            for q_idx, row in res.get("quantities", pd.DataFrame()).iterrows():
                # drmd:quantity (type drmd:quantityType extends dcc:primitiveQuantityType)
                quantity_elem = ET.SubElement(list_elem, f"{{{ns_drmd}}}quantity")
                # dcc:name inside the quantity (per dcc text type)
                qname_elem = ET.SubElement(quantity_elem, f"{{{ns_dcc}}}name")
                ET.SubElement(qname_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(str(row.get("Name", "")))

                # Use original values directly (no D-SI conversion)
                si_value = str(row.get("Value", ""))
                si_unit = str(row.get("Unit", ""))

                # Numerical value with SI block, using original values
                real_elem = ET.SubElement(quantity_elem, f"{{{ns_si}}}real")
                ET.SubElement(real_elem, f"{{{ns_si}}}value").text = sanitize_xml_string(si_value)
                ET.SubElement(real_elem, f"{{{ns_si}}}unit").text = sanitize_xml_string(si_unit)

                # Check uncertainty values.
                expandedMU_vals = {}
                for subtag, col in [("valueExpandedMU", "Uncertainty"),
                                    ("coverageFactor", "Coverage Factor"),
                                    ("coverageProbability", "Coverage Probability"),
                                    ("distribution", "Distribution")]:
                    val = row.get(col, "")
                    if val is None or (isinstance(val, float) and math.isnan(val)) or str(val).strip() == "":
                        continue
                    expandedMU_vals[subtag] = val
                # Only create the measurementUncertaintyUnivariate element if there is valid data.
                if expandedMU_vals:
                    mu_elem = ET.SubElement(real_elem, f"{{{ns_si}}}measurementUncertaintyUnivariate")
                    expMU_elem = ET.SubElement(mu_elem, f"{{{ns_si}}}expandedMU")
                    for tag, value in expandedMU_vals.items():
                        ET.SubElement(expMU_elem, f"{{{ns_si}}}{tag}").text = sanitize_xml_string(str(value))
                if res.get("identifiers") and q_idx < len(res["identifiers"]):
                    export_identifier_list(quantity_elem, "propertyIdentifiers", res["identifiers"][q_idx], ns_drmd)
    return mp_list_elem


def export_statements(ns_drmd, ns_dcc):
    # Create the <drmd:statements> element.
    statements_elem = ET.Element(f"{{{ns_drmd}}}statements")

    def add_statement(element_name, label, text):
        """Adds a statement element if text is not empty.
           element_name should be one of the official ones, e.g. 'intendedUse'.
        """
        if text.strip():
            stmt = ET.SubElement(statements_elem, f"{{{ns_drmd}}}{element_name}")
            # Only add a dcc:name if a label is provided.
            if label.strip():
                name_elem = ET.SubElement(stmt, f"{{{ns_dcc}}}name")
                ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = label.strip()
            # Add one or more content elements (one per nonempty line).
            for line in text.strip().splitlines():
                if line.strip():
                    ET.SubElement(stmt, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = line.strip()

    official = st.session_state.official_statements
    add_statement("intendedUse", "Intended Use", official.get("intendedUse", {}).get("content", ""))
    add_statement("commutability", "Commutability", official.get("commutability", {}).get("content", ""))
    add_statement("storageInformation", "Storage Information", official.get("storageInformation", {}).get("content", ""))
    add_statement("instructionsForHandlingAndUse", "Handling Instructions", official.get("instructionsForHandlingAndUse", {}).get("content", ""))
    add_statement("metrologicalTraceability", "Metrological Traceability", official.get("metrologicalTraceability", {}).get("content", ""))
    add_statement("healthAndSafetyInformation", "Health and Safety Information", official.get("healthAndSafetyInformation", {}).get("content", ""))
    add_statement("subcontractors", "Subcontractors", official.get("subcontractors", {}).get("content", ""))
    add_statement("legalNotice", "Legal Notice", official.get("legalNotice", {}).get("content", ""))
    add_statement("referenceToCertificationReport", "Reference to Certification Report", official.get("referenceToCertificationReport", {}).get("content", ""))

    # For custom statements, always export using the element name "statement".
    for cs in st.session_state.custom_statements:
        if cs.get("content", "").strip():
            cs_elem = ET.SubElement(statements_elem, f"{{{ns_drmd}}}statement")
            if cs.get("name", "").strip():
                name_elem = ET.SubElement(cs_elem, f"{{{ns_dcc}}}name")
                ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = cs.get("name", "").strip()
            for line in cs.get("content", "").strip().splitlines():
                if line.strip():
                    ET.SubElement(cs_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = line.strip()

    return statements_elem


def export_comment(ns_drmd):
    """Generate a single <comment> element if a comment is provided."""
    comment_text = st.session_state.get("comment", "").strip()
    if comment_text:
        comment_elem = ET.Element(f"{{{ns_drmd}}}comment")
        comment_elem.text = comment_text
        return comment_elem
    return None

def export_document(ns_drmd, ns_dcc):
    """Generate a single <document> element from the uploaded attachment,
       or from embedded_files if no attachment is present.
    """
    # Prefer the attachment uploaded in the UI.
    if st.session_state.get("attachment") is not None:
        uploaded_file = st.session_state.attachment
        file_content = uploaded_file.getvalue()
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        doc_elem = ET.Element(f"{{{ns_drmd}}}document")
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}fileName").text = uploaded_file.name
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}mimeType").text = uploaded_file.type or "application/octet-stream"
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}dataBase64").text = encoded_content
        return doc_elem
    # Otherwise, if an embedded file exists, use the first one.
    if st.session_state.get("embedded_files"):
        file = st.session_state.embedded_files[0]
        doc_elem = ET.Element(f"{{{ns_drmd}}}document")
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}fileName").text = file["name"]
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}mimeType").text = file["mimeType"]
        ET.SubElement(doc_elem, f"{{{ns_dcc}}}dataBase64").text = base64.b64encode(file["data"]).decode('utf-8')
        return doc_elem
    return None