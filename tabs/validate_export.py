import streamlit as st
import xml.etree.ElementTree as ET
import re
import base64
import hashlib
from lxml import etree
from signxml import XMLVerifier
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

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

# Import signing function from digital_signature tab
try:
    from tabs.digital_signature import sign_xml_document
except ImportError:
    def sign_xml_document(xml_string, private_key, certificate):
        raise ImportError("Could not import sign_xml_document from tabs.digital_signature")


def get_xml_filename():
    """Generate XML filename based on first material name"""
    if st.session_state.materials and st.session_state.materials[0].get("name"):
        # Get first material name
        material_name = st.session_state.materials[0]["name"].strip()
        
        # Clean the filename: remove special characters, replace spaces with underscores
        clean_name = re.sub(r'[^\w\s-]', '', material_name)
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        
        # Add .xml extension
        return f"{clean_name}.xml" if clean_name else "material_properties.xml"
    else:
        return "material_properties.xml"


def verify_xml_signature(xml_string):
    """Verify XML signature - FIXED VERSION"""
    try:
        xml_string = xml_string.replace("\u00A0", " ")
        parser = etree.XMLParser(remove_blank_text=False)
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
        
        # Extract certificate and pass it explicitly
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        x509_cert_elem = root.find(".//ds:X509Certificate", ns)
        
        cert_pem = None
        if x509_cert_elem is not None and x509_cert_elem.text:
            cert_der = base64.b64decode(x509_cert_elem.text)
            cert_obj = x509.load_der_x509_certificate(cert_der, default_backend())
            cert_pem = cert_obj.public_bytes(serialization.Encoding.PEM)
        
        verifier = XMLVerifier()
        
        if cert_pem:
            verified_data = verifier.verify(root, x509_cert=cert_pem)
        else:
            verified_data = verifier.verify(root)
        
        # Extract certificate info
        cert_info = {}
        if x509_cert_elem is not None and x509_cert_elem.text:
            try:
                cert_der = base64.b64decode(x509_cert_elem.text)
                cert = x509.load_der_x509_certificate(cert_der, default_backend())
                
                cert_info = {
                    'subject': cert.subject.rfc4514_string(),
                    'issuer': cert.issuer.rfc4514_string(),
                    'serial': str(cert.serial_number),
                    'valid_from': cert.not_valid_before.isoformat(),
                    'valid_until': cert.not_valid_after.isoformat(),
                    'signature_algorithm': cert.signature_algorithm_oid._name
                }
                
                try:
                    san_ext = cert.extensions.get_extension_for_oid(x509.OID_SUBJECT_ALTERNATIVE_NAME)
                    cert_info['subject_alternative_name'] = [str(name) for name in san_ext.value]
                except x509.extensions.ExtensionNotFound:
                    cert_info['subject_alternative_name'] = 'Not present'
                    
            except Exception as e:
                cert_info['error'] = f"Could not parse certificate: {str(e)}"
        
        return True, "Signature is valid", cert_info
        
    except Exception as e:
        error_msg = str(e)
        if "candidates exhausted" in error_msg.lower():
            error_msg += "\n\n**Note:** This may be a certificate validation issue."
        return False, f"Signature verification failed: {error_msg}", {}


def verify_xml_signature_with_debug(xml_string):
    """Verify signature with detailed debugging"""
    try:
        xml_string = xml_string.replace("\u00A0", " ")
        parser = etree.XMLParser(remove_blank_text=False)
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
        
        ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        
        # Get expected digest
        digest_elem = root.find('.//ds:DigestValue', ns)
        expected_digest = digest_elem.text if digest_elem is not None else None
        
        # Get canonicalization method
        c14n_elem = root.find('.//ds:CanonicalizationMethod', ns)
        c14n_algo = c14n_elem.get('Algorithm') if c14n_elem is not None else None
        
        st.write(f"**Expected DigestValue:** `{expected_digest}`")
        st.write(f"**Canonicalization:** `{c14n_algo}`")
        
        # Compute digest manually
        sig = root.find('.//ds:Signature', ns)
        if sig is not None:
            sig.getparent().remove(sig)
        
        # Canonicalize
        if c14n_algo == "http://www.w3.org/TR/2001/REC-xml-c14n-20010315":
            canonical = etree.tostring(root, method='c14n')
        elif c14n_algo == "http://www.w3.org/2001/10/xml-exc-c14n#":
            canonical = etree.tostring(root, method='c14n', exclusive=True)
        else:
            canonical = etree.tostring(root, method='c14n')
        
        computed_digest = base64.b64encode(hashlib.sha256(canonical).digest()).decode()
        st.write(f"**Computed DigestValue:** `{computed_digest}`")
        
        # Compare digests
        if expected_digest == computed_digest:
            st.success("✅ DigestValue matches - proceeding with signature verification")
        else:
            st.error("❌ DigestValue mismatch!")
            st.download_button(
                "Download Canonical XML",
                data=canonical,
                file_name="canonical_form.xml"
            )
            return False, "Digest mismatch", {}
        
        # Verify signature
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
        
        x509_cert_elem = root.find(".//ds:X509Certificate", ns)
        cert_pem = None
        
        if x509_cert_elem is not None and x509_cert_elem.text:
            cert_der = base64.b64decode(x509_cert_elem.text)
            cert_obj = x509.load_der_x509_certificate(cert_der, default_backend())
            cert_pem = cert_obj.public_bytes(serialization.Encoding.PEM)
            st.write("**Certificate extracted:** ✅")
        
        verifier = XMLVerifier()
        
        if cert_pem:
            verified_data = verifier.verify(root, x509_cert=cert_pem)
        else:
            verified_data = verifier.verify(root)
        
        st.success("✅ Signature verification successful!")
        
        # Extract cert info
        cert_info = {}
        if x509_cert_elem is not None and x509_cert_elem.text:
            try:
                cert_der = base64.b64decode(x509_cert_elem.text)
                cert = x509.load_der_x509_certificate(cert_der, default_backend())
                
                cert_info = {
                    'subject': cert.subject.rfc4514_string(),
                    'issuer': cert.issuer.rfc4514_string(),
                    'serial': str(cert.serial_number),
                    'valid_from': cert.not_valid_before.isoformat(),
                    'valid_until': cert.not_valid_after.isoformat()
                }
                
                try:
                    san_ext = cert.extensions.get_extension_for_oid(x509.OID_SUBJECT_ALTERNATIVE_NAME)
                    cert_info['subject_alternative_name'] = [str(name) for name in san_ext.value]
                except:
                    cert_info['subject_alternative_name'] = 'Not present'
                    
            except Exception as e:
                cert_info['error'] = str(e)
        
        return True, "Signature is valid", cert_info
        
    except Exception as e:
        st.error(f"Verification error: {str(e)}")
        return False, f"Verification failed: {str(e)}", {}


def render_validate_export():
    """Main rendering function with signature verification always visible"""
    
    # ========================================================================
    # SECTION 1: VERIFY XML SIGNATURE (ALWAYS VISIBLE)
    # ========================================================================
    st.subheader("🔐 Verify XML Signature")
    
    st.info("Upload a signed XML file to verify its digital signature. This works independently of XML generation.")
    
    uploaded_file = st.file_uploader(
        "Upload Signed XML File", 
        type=['xml'], 
        key="verify_xml_uploader"
    )
    
    verify_xml_input = st.text_area(
        "Or paste signed XML here (not recommended):",
        height=200,
        placeholder="<drmd:digitalReferenceMaterialDocument ...>",
        key="verify_xml_textarea"
    )
    
    xml_to_verify = ""
    if uploaded_file:
        try:
            xml_bytes = uploaded_file.read()
            xml_to_verify = xml_bytes.decode('utf-8')
            st.success(f"✅ File uploaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    elif verify_xml_input:
        xml_to_verify = verify_xml_input
        st.warning("⚠️ You pasted the XML. Verification may fail if whitespace was modified during copy/paste.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Verify Signature", use_container_width=True, type="primary", key="verify_btn"):
            if not xml_to_verify.strip():
                st.warning("Please provide XML to verify (upload file or paste content)")
            else:
                with st.spinner("Verifying signature..."):
                    try:
                        is_valid_sig, message, cert_info = verify_xml_signature(xml_to_verify)
                        
                        if is_valid_sig:
                            st.success(f"✅ {message}")
                            if cert_info:
                                st.markdown("**Certificate Information:**")
                                st.json(cert_info, expanded=True)
                        else:
                            st.error(f"❌ {message}")
                            
                    except Exception as e:
                        st.error(f"Verification error: {e}")
                        st.exception(e)
    
    with col2:
        if st.button("🔬 Verify with Debug Info", use_container_width=True, key="verify_debug_btn"):
            if not xml_to_verify.strip():
                st.warning("Please provide XML to verify (upload file or paste content)")
            else:
                st.subheader("Debug Information")
                is_valid_sig, msg, info = verify_xml_signature_with_debug(xml_to_verify)
                
                if is_valid_sig:
                    st.balloons()
                    if info:
                        st.json(info, expanded=True)
                else:
                    with st.expander("🔧 Troubleshooting"):
                        st.markdown("""
                        **Common Issues:**
                        1. **File was modified after signing** - Re-download and verify
                        2. **Wrong file uploaded** - Ensure it's the correct signed XML
                        3. **Encoding issues** - File must be UTF-8 encoded
                        4. **Copy/paste whitespace changes** - Use file upload instead
                        
                        **Solution:** Generate a fresh certificate in the Digital Signature tab,
                        then regenerate and download the XML from this tab.
                        """)
    
    # ========================================================================
    # SECTION 2: GENERATE AND VALIDATE XML (SEPARATE SECTION)
    # ========================================================================
    st.divider()
    st.subheader("📝 Generate & Validate DRMD Document")
    
    # Top row with Generate XML button
    col1, col2 = st.columns([2, 3])

    with col1:
        generate_button = st.button("Generate XML", key="generate_xml", use_container_width=True)

    with col2:
        if not generate_button and not st.session_state.get('generated_xml'):
            st.write("Click the button to generate XML from your entered data.")

    if generate_button:
        # Define namespaces and register them.
        ns_drmd = "https://example.org/drmd"
        ns_dcc = "https://ptb.de/dcc"
        ns_si = "https://ptb.de/si"
        ET.register_namespace("drmd", ns_drmd)
        ET.register_namespace("dcc", ns_dcc)
        ET.register_namespace("si", ns_si)
        ET.register_namespace("ds", DS_NS)

        # Create the root element.
        root = ET.Element(f"{{{ns_drmd}}}digitalReferenceMaterialDocument", attrib={"schemaVersion": "0.3.0"})

        # --- Build administrativeData ---
        admin_data = ET.SubElement(root, f"{{{ns_drmd}}}administrativeData")
        core_data = ET.SubElement(admin_data, f"{{{ns_drmd}}}coreData")
        ET.SubElement(core_data, f"{{{ns_drmd}}}titleOfTheDocument").text = sanitize_xml_string(st.session_state.title_option)
        ET.SubElement(core_data, f"{{{ns_drmd}}}uniqueIdentifier").text = sanitize_xml_string(st.session_state.uniqueIdentifier)
        if st.session_state.documentIdentifiers:
            export_identifier_list(core_data, "documentIdentifiers", st.session_state.documentIdentifiers, ns_drmd)
        
        validity_elem = ET.SubElement(core_data, f"{{{ns_drmd}}}validity")
        if st.session_state.validity_type == "Time After Dispatch":
            tad = ET.SubElement(validity_elem, f"{{{ns_drmd}}}timeAfterDispatch")
            ET.SubElement(tad, f"{{{ns_drmd}}}dispatchDate").text = str(st.session_state.date_of_issue)
            ET.SubElement(tad, f"{{{ns_drmd}}}period").text = str(st.session_state.raw_validity_period)
        elif st.session_state.validity_type == "Specific Time":
            ET.SubElement(validity_elem, f"{{{ns_drmd}}}specificTime").text = str(st.session_state.specific_time)
        else:
            ET.SubElement(validity_elem, f"{{{ns_drmd}}}untilRevoked").text = "true"

        # Materials
        materials_elem = ET.SubElement(root, f"{{{ns_drmd}}}materials")
        if not st.session_state.materials:
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
                
                min_sample_elem = ET.SubElement(mat_elem, f"{{{ns_drmd}}}minimumSampleSize")
                iq_elem = ET.SubElement(min_sample_elem, f"{{{ns_dcc}}}itemQuantity")
                realList_elem = ET.SubElement(iq_elem, f"{{{ns_si}}}realListXMLList")

                sample_size_str = material.get("minimumSampleSize", "").strip()
                if sample_size_str:
                    match = re.match(r'^(\d+(?:\.\d+)?)\s*(.*)$', sample_size_str)
                    if match:
                        value_part = match.group(1)
                        unit_part = match.group(2).strip()
                    else:
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

        statements_elem = export_statements(ns_drmd, ns_dcc)
        mp_list_elem = export_materialProperties(ns_drmd, ns_dcc, ns_si)
        root.append(mp_list_elem)
        root.append(statements_elem)

        comment_elem = export_comment(ns_drmd)
        if comment_elem is not None:
            root.append(comment_elem)

        doc_elem = export_document(ns_drmd, ns_dcc)
        if doc_elem is not None:
            root.append(doc_elem)

        xml_bytes = ET.tostring(root, encoding="utf-8")
        
        try:
            lxml_root = etree.fromstring(xml_bytes)
            pretty_xml = etree.tostring(
                lxml_root, 
                pretty_print=True, 
                encoding='utf-8', 
                xml_declaration=True
            ).decode('utf-8')
        except Exception as e:
            st.error(f"Error during pretty-printing XML with lxml: {e}")
            pretty_xml = xml_bytes.decode("utf-8")

        # Automatic signing
        if st.session_state.get('signature_key') and st.session_state.get('signature_cert'):
            try:
                with st.spinner("Signing XML document..."):
                    signed_xml = sign_xml_document(
                        pretty_xml,
                        st.session_state.signature_key,
                        st.session_state.signature_cert
                    )
                pretty_xml = signed_xml
                st.success("✅ XML generated and digitally signed!")
            except Exception as e:
                st.error(f"Error signing XML: {e}")
                st.info("Proceeding with unsigned XML.")
        else:
            st.info("ℹ️ XML generated without digital signature. Set up a certificate in the **Digital Signature** tab to automatically sign documents.")

        # Validate XML against schema
        is_valid = False
        validation_message = ""
        if xmlschema:
            try:
                schema = xmlschema.XMLSchema(DEFAULT_XSD_PATH)
                is_valid = schema.is_valid(pretty_xml)
                if not is_valid:
                    errors = schema.validate(pretty_xml, use_defaults=False)
                    validation_message = str(errors)
            except Exception as e:
                validation_message = f"Schema validation failed: {e}"
        else:
            validation_message = "xmlschema library not installed. Skipping validation."

        # XSL Transformation to HTML
        try:
            xslt_doc = etree.parse(DEFAULT_XSL_PATH)
            transform = etree.XSLT(xslt_doc)
            xml_doc = etree.fromstring(pretty_xml.encode("utf-8"))
            result_tree = transform(xml_doc)
            html_output = etree.tostring(result_tree, pretty_print=True, encoding="utf-8").decode("utf-8")
        except Exception as e:
            st.error(f"XSL Transformation Error: {e}")
            html_output = ""

        st.session_state.generated_xml = pretty_xml
        st.session_state.generated_html = html_output
        st.session_state.xml_is_valid = is_valid
        st.session_state.validation_message = validation_message

    # Show results if XML has been generated
    if st.session_state.get('generated_xml'):
        pretty_xml = st.session_state.generated_xml
        html_output = st.session_state.generated_html
        is_valid = st.session_state.xml_is_valid
        validation_message = st.session_state.validation_message
        
        # Get dynamic filename
        xml_filename = get_xml_filename()
        html_filename = xml_filename.replace('.xml', '.html')
        
        # Download buttons row
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.download_button(
                "Download HTML", 
                data=html_output, 
                file_name=html_filename, 
                mime="text/html", 
                use_container_width=True
            )
        with col2:
            st.download_button(
                "Download XML", 
                data=pretty_xml, 
                file_name=xml_filename, 
                mime="application/xml", 
                use_container_width=True
            )
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
        
        # COMAR Upload Instructions
        st.markdown("---")
        st.markdown("### 📤 COMAR Database Upload Procedure")
        st.markdown("""
        **Follow these steps to upload your XML to the COMAR database:**
        
        1. **Download XML**: Click the "Download XML" button above
        2. **Open COMAR Database**: Click the "Upload to COMAR" button
        3. **Navigate to Upload**: In COMAR, go to "My CRMs"
        4. **Drag & Drop**: Upload your downloaded XML file
        5. **Verify**: Check that your data appears correctly
        
        ⚠️ **Note**: Ensure your XML is valid (green checkmark above) before uploading.
        """)

        # HTML preview
        with st.expander("HTML Preview", expanded=True):
            st.components.v1.html(html_output, height=600, scrolling=True)

        # XML content
        with st.expander("XML Content", expanded=False):
            st.text_area("Generated XML", pretty_xml, height=400, key="xml_content_display")
            if not is_valid and validation_message:
                st.error("Validation Errors:")
                st.code(validation_message)
