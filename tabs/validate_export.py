# tabs/validate_export.py
import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import io
from lxml import etree

try:
    import xmlschema
except ImportError:
    xmlschema = None

from utils import (
    DEFAULT_XSD_PATH,
    DEFAULT_XSL_PATH,
    DS_NS,
    sanitize_xml_string,
    export_identifier_list
)
from export import (
    export_materialProperties,
    export_statements,
    export_comment,
    export_document
)

def render_validate_export():
    # Top row with Generate XML button and validation status
    col1, col2 = st.columns([2, 3])

    with col1:
        generate_button = st.button("Generate XML", key="generate_xml", use_container_width=True)

    # Only show this placeholder initially
    with col2:
        if not generate_button and not st.session_state.get('generated_xml'):
            st.write("Click the button to generate XML from your entered data.")

    if generate_button:
        # Define namespaces and register them.
        ns_drmd = "https://example.org/drmd"
        ns_dcc = "https://ptb.de/dcc"
        ns_si = "https://ptb.de/si"
        # DS_NS is imported from utils
        ET.register_namespace("drmd", ns_drmd)
        ET.register_namespace("dcc", ns_dcc)
        ET.register_namespace("si", ns_si)
        ET.register_namespace("ds", DS_NS)

        # Create the root element.
        root = ET.Element(f"{{{ns_drmd}}}digitalReferenceMaterialDocument", attrib={"schemaVersion": "0.3.0"})

        # --- Build administrativeData ---
        admin_data = ET.SubElement(root, f"{{{ns_drmd}}}administrativeData")
        # coreData: title, uniqueIdentifier, documentIdentifiers, validity.
        core_data = ET.SubElement(admin_data, f"{{{ns_drmd}}}coreData")
        ET.SubElement(core_data, f"{{{ns_drmd}}}titleOfTheDocument").text = sanitize_xml_string(st.session_state.title_option)
        ET.SubElement(core_data, f"{{{ns_drmd}}}uniqueIdentifier").text = sanitize_xml_string(st.session_state.persistent_id_value)
        if st.session_state.documentIdentifiers:
            export_identifier_list(core_data, "documentIdentifiers", st.session_state.documentIdentifiers, ns_drmd)
        # Validity (simplified example)
        validity_elem = ET.SubElement(core_data, f"{{{ns_drmd}}}validity")
        if st.session_state.validity_type == "Time After Dispatch":
            tad = ET.SubElement(validity_elem, f"{{{ns_drmd}}}timeAfterDispatch")
            ET.SubElement(tad, f"{{{ns_drmd}}}dispatchDate").text = str(st.session_state.date_of_issue)
            ET.SubElement(tad, f"{{{ns_drmd}}}period").text = st.session_state.raw_validity_period
        elif st.session_state.validity_type == "Specific Time":
            ET.SubElement(validity_elem, f"{{{ns_drmd}}}specificTime").text = str(st.session_state.specific_time)
        else:
            ET.SubElement(validity_elem, f"{{{ns_drmd}}}untilRevoked").text = "true"

        # Materials: using the list from the Materials form.
        materials_elem = ET.SubElement(root, f"{{{ns_drmd}}}materials")
        if not st.session_state.materials:
            # If no material was entered, add a dummy material.
            dummy = ET.SubElement(materials_elem, f"{{{ns_drmd}}}material")
            dummy_name = ET.SubElement(dummy, f"{{{ns_drmd}}}name")
            ET.SubElement(dummy_name, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = "Dummy Material"
        else:
            for material in st.session_state.materials:
                mat_elem = ET.SubElement(materials_elem, f"{{{ns_drmd}}}material")
                name_elem = ET.SubElement(mat_elem, f"{{{ns_drmd}}}name")
                ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = sanitize_xml_string(material.get("name", ""))
                if (material.get("description", "") or "").strip():
                    desc_elem = ET.SubElement(mat_elem, f"{{{ns_drmd}}}description")
                    ET.SubElement(desc_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = material.get("description", "")
                # minimumSampleSize (required) – parse value and unit properly
                min_sample_elem = ET.SubElement(mat_elem, f"{{{ns_drmd}}}minimumSampleSize")
                iq_elem = ET.SubElement(min_sample_elem, f"{{{ns_dcc}}}itemQuantity")
                realList_elem = ET.SubElement(iq_elem, f"{{{ns_si}}}realListXMLList")

                # Parse the minimum sample size to separate value and unit
                sample_size_str = material.get("minimumSampleSize", "").strip()
                if sample_size_str:
                    # Match patterns like "4.9 g", "3 kg", "7 mol", "100" (number only)
                    match = re.match(r'^(\d+(?:\.\d+)?)\s*(.*)$', sample_size_str)
                    if match:
                        value_part = match.group(1)
                        unit_part = match.group(2).strip()
                    else:
                    # Fallback: if no match, treat whole string as value
                        value_part = sample_size_str
                        unit_part = ""
                else:
                    value_part = "0"
                    unit_part = ""

                val_elem = ET.Element(f"{{{ns_si}}}valueXMLList")
                val_elem.text = value_part
                unit_elem = ET.Element(f"{{{ns_si}}}unitXMLList")
                unit_elem.text = unit_part
                realList_elem.append(val_elem)
                realList_elem.append(unit_elem)

                # Optional: itemQuantities
                if (material.get("itemQuantities", "") or "").strip():
                    itemQuant_elem = ET.SubElement(mat_elem, f"{{{ns_drmd}}}itemQuantities")
                    dummy_item = ET.SubElement(itemQuant_elem, f"{{{ns_dcc}}}itemQuantity")
                    dummy_rl = ET.SubElement(dummy_item, f"{{{ns_si}}}realListXMLList")
                    ET.SubElement(dummy_rl, f"{{{ns_si}}}valueXMLList").text = material.get("itemQuantities", "")
                    ET.SubElement(dummy_rl, f"{{{ns_si}}}unitXMLList").text = ""
                if material.get("materialIdentifiers"):
                    export_identifier_list(mat_elem, "materialIdentifiers", material["materialIdentifiers"], ns_drmd)

        # Reference Material Producer
        if not st.session_state.producers:
            prod_elem = ET.SubElement(admin_data, f"{{{ns_drmd}}}referenceMaterialProducer")
            prod_name_elem = ET.SubElement(prod_elem, f"{{{ns_drmd}}}name")
            ET.SubElement(prod_name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = "Dummy Producer"
        else:
            for prod in st.session_state.producers:
                prod_elem = ET.SubElement(admin_data, f"{{{ns_drmd}}}referenceMaterialProducer")
                prod_name_elem = ET.SubElement(prod_elem, f"{{{ns_drmd}}}name")
                ET.SubElement(prod_name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = prod.get("producerName", "")
                contact_elem = ET.SubElement(prod_elem, f"{{{ns_drmd}}}contact")
                contact_name_elem = ET.SubElement(contact_elem, f"{{{ns_dcc}}}name")
                ET.SubElement(contact_name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = prod.get("contactName", prod.get("producerName", "Contact Name"))
                if (prod.get("producerEmail", "") or "").strip():
                    ET.SubElement(contact_elem, f"{{{ns_dcc}}}eMail").text = sanitize_xml_string(prod.get("producerEmail", ""))
                if (prod.get("producerPhone", "") or "").strip():
                    ET.SubElement(contact_elem, f"{{{ns_dcc}}}phone").text = prod.get("producerPhone", "")
                if (prod.get("producerFax", "") or "").strip():
                    ET.SubElement(contact_elem, f"{{{ns_dcc}}}fax").text = prod.get("producerFax", "")
                if (prod.get("producerStreet", "") or prod.get("producerStreetNo", "") or prod.get("producerPostCode", "")
                    or prod.get("producerCity", "") or prod.get("producerCountryCode", "")):
                    location_elem = ET.SubElement(contact_elem, f"{{{ns_dcc}}}location")
                    if (prod.get("producerStreet", "") or "").strip():
                        ET.SubElement(location_elem, f"{{{ns_dcc}}}street").text = prod.get("producerStreet", "")
                    if (prod.get("producerStreetNo", "") or "").strip():
                        ET.SubElement(location_elem, f"{{{ns_dcc}}}streetNo").text = prod.get("producerStreetNo", "")
                    if (prod.get("producerPostCode", "") or "").strip():
                        ET.SubElement(location_elem, f"{{{ns_dcc}}}postCode").text = prod.get("producerPostCode", "")
                    if (prod.get("producerCity", "") or "").strip():
                        ET.SubElement(location_elem, f"{{{ns_dcc}}}city").text = prod.get("producerCity", "")
                if (prod.get("producerCountryCode", "") or "").strip():
                        ET.SubElement(location_elem, f"{{{ns_dcc}}}countryCode").text = prod.get("producerCountryCode", "")
                if prod.get("organizationIdentifiers"):
                    export_identifier_list(prod_elem, "organizationIdentifiers", prod["organizationIdentifiers"], ns_drmd)

        # Responsible Persons
        if not st.session_state.responsible_persons:
            respPersons_elem = ET.SubElement(admin_data, f"{{{ns_drmd}}}respPersons")
            rp_elem = ET.SubElement(respPersons_elem, f"{{{ns_dcc}}}respPerson")
            person_elem = ET.SubElement(rp_elem, f"{{{ns_dcc}}}person")
            name_elem = ET.SubElement(person_elem, f"{{{ns_dcc}}}name")
            ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = "Dummy Person"
            ET.SubElement(rp_elem, f"{{{ns_dcc}}}role").text = "Dummy Role"
        else:
            respPersons_elem = ET.SubElement(admin_data, f"{{{ns_drmd}}}respPersons")
            for rp in st.session_state.responsible_persons:
                rp_elem = ET.SubElement(respPersons_elem, f"{{{ns_dcc}}}respPerson")
                person_elem = ET.SubElement(rp_elem, f"{{{ns_dcc}}}person")
                name_elem = ET.SubElement(person_elem, f"{{{ns_dcc}}}name")
                ET.SubElement(name_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = rp.get("personName", "")
                if (rp.get("description", "") or "").strip():
                    desc_elem = ET.SubElement(rp_elem, f"{{{ns_dcc}}}description")
                    ET.SubElement(desc_elem, f"{{{ns_dcc}}}content", attrib={"lang": "en"}).text = rp.get("description", "")
                if (rp.get("role", "") or "").strip():
                    ET.SubElement(rp_elem, f"{{{ns_dcc}}}role").text = rp.get("role", "")
                if rp.get("mainSigner", False):
                    ET.SubElement(rp_elem, f"{{{ns_dcc}}}mainSigner").text = "true"
                if rp.get("cryptElectronicSeal", False):
                    ET.SubElement(rp_elem, f"{{{ns_dcc}}}cryptElectronicSeal").text = "true"
                if rp.get("cryptElectronicSignature", False):
                    ET.SubElement(rp_elem, f"{{{ns_dcc}}}cryptElectronicSignature").text = "true"
                if rp.get("cryptElectronicTimeStamp", False):
                    ET.SubElement(rp_elem, f"{{{ns_dcc}}}cryptElectronicTimeStamp").text = "true"

        # Prepare statements section (append later to maintain schema order)
        statements_elem = export_statements(ns_drmd, ns_dcc)

        # --- Material Properties ---
        # Next: materialPropertiesList.
        mp_list_elem = export_materialProperties(ns_drmd, ns_dcc, ns_si)
        root.append(mp_list_elem)
        # Now append statements after materialPropertiesList to respect sequence order
        root.append(statements_elem)

        # 3️ Add a single <comment> element, if provided.
        comment_elem = export_comment(ns_drmd)
        if comment_elem is not None:
            root.append(comment_elem)

        # 4️ Add a single <document> element, if provided.
        doc_elem = export_document(ns_drmd, ns_dcc)
        if doc_elem is not None:
            root.append(doc_elem)

        if st.session_state.get("digital_signature_cert"):
            ds_elem = ET.SubElement(root, f"{{{DS_NS}}}Signature")
            ds_elem.text = st.session_state.digital_signature_cert.name

        # Pretty-print XML.
        xml_str = ET.tostring(root, encoding="utf-8")
        try:
            reparsed = minidom.parseString(xml_str)
            pretty_xml = reparsed.toprettyxml(indent="  ")
        except Exception as e:
            st.error(f"Error during pretty-printing XML: {e}")
            pretty_xml = xml_str.decode("utf-8")

        # Validate XML against schema
        is_valid = False
        validation_message = ""
        if xmlschema:
            try:
                schema = xmlschema.XMLSchema(DEFAULT_XSD_PATH)
                is_valid = schema.is_valid(pretty_xml)
                if not is_valid:
                    # Get error log details
                    errors = schema.validate(pretty_xml, use_defaults=False)
                    validation_message = str(errors)
            except Exception as e:
                validation_message = f"Schema validation failed: {e}"
        else:
            validation_message = "xmlschema library not installed. Skipping validation."


        # --- XSL Transformation to HTML ---
        try:
            # Parse the XSL file
            xslt_doc = etree.parse(DEFAULT_XSL_PATH)
            transform = etree.XSLT(xslt_doc)
            # Parse the generated XML
            xml_doc = etree.fromstring(pretty_xml.encode("utf-8"))
            # Transform XML to HTML
            result_tree = transform(xml_doc)
            html_output = etree.tostring(result_tree, pretty_print=True, encoding="utf-8").decode("utf-8")
        except Exception as e:
            st.error(f"XSL Transformation Error: {e}")
            html_output = ""

        # Store the generated data in session state
        st.session_state.generated_xml = pretty_xml
        st.session_state.generated_html = html_output
        st.session_state.xml_is_valid = is_valid
        st.session_state.validation_message = validation_message

    # Show download buttons and COMAR functionality if XML has been generated
    if st.session_state.get('generated_xml'):
        pretty_xml = st.session_state.generated_xml
        html_output = st.session_state.generated_html
        is_valid = st.session_state.xml_is_valid
        validation_message = st.session_state.validation_message
        
        # Download buttons row
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.download_button("Download HTML", data=html_output, file_name="certificate.html", mime="text/html", use_container_width=True)
        with col2:
            st.download_button("Download XML", data=pretty_xml, file_name="material_properties.xml", mime="application/xml", use_container_width=True)
        with col3:
            st.link_button(
                "Upload to COMAR",
                "https://www.comar.bam.de/apex/r/eptiscomar/f_103106107107200990333500400/my-crms",
                disabled=not is_valid,
                use_container_width=True,
                help="Open COMAR database to upload XML"
            )
        
        # Validation status
        if is_valid:
            st.success("XML is valid against the schema!")
        else:
            st.error("XML is NOT valid against the schema!")
        
        # COMAR Upload Instructions (always visible)
        st.markdown("---")
        st.markdown("### 📤 COMAR Database Upload Procedure")
        st.markdown("""
        **Follow these steps to upload your XML to the COMAR database:**
        
        1. **Download XML**: Click the "Download XML" button above to save the XML file to your computer
        2. **Open COMAR Database**: Click the "Upload to COMAR" button to open the COMAR database in a new tab
        3. **Navigate to Upload**: In COMAR, go to the "My CRMs" section
        4. **Drag & Drop**: Use the drag and drop XML feature to upload your downloaded XML file
        5. **Verify**: Check that your reference material data appears correctly in COMAR
        
        ⚠️ **Note**: Make sure your XML file is valid (green checkmark above) before uploading.
        """)

        # HTML preview (expanded by default)
        with st.expander("HTML Preview", expanded=True):
            st.components.v1.html(html_output, height=600, scrolling=True)

        # XML content (collapsed by default)
        with st.expander("XML Content", expanded=False):
            st.text_area("Generated XML", pretty_xml, height=400)

            # Show validation errors if any
            if not is_valid and validation_message:
                st.error("Validation Errors:")
                st.code(validation_message)