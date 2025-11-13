import streamlit as st
import base64
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
import xml.etree.ElementTree as ET
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods
import tempfile
import os

def generate_test_certificate():
    """Generate a self-signed certificate for testing purposes"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BAM Test Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.bam.de"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    return private_key, cert


def sign_xml_document(xml_string, private_key, certificate):
    """
    Sign an XML document using W3C XML-DSig standard with enveloped signature.
    
    Args:
        xml_string: The XML document as string
        private_key: Private key for signing
        certificate: X.509 certificate
        
    Returns:
        Signed XML string
    """
    try:
        # Parse the XML
        root = etree.fromstring(xml_string.encode('utf-8'))
        
        # Prepare private key in PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Prepare certificate in PEM format
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        
        # Create signer with enveloped signature method
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        
        # Sign the document
        signed_root = signer.sign(
            root,
            key=private_key_pem,
            cert=cert_pem
        )
        
        # Convert back to string with proper formatting
        # We must serialize to bytes (e.g., 'utf-8') to include the xml_declaration.
        # Then, we decode back to a string (unicode) for use in Streamlit.
        signed_xml_bytes = etree.tostring(
            signed_root,
            encoding='utf-8',
            pretty_print=True,
            xml_declaration=True
        )
        signed_xml = signed_xml_bytes.decode('utf-8')
        
        return signed_xml
        
    except Exception as e:
        raise Exception(f"Error signing XML document: {str(e)}")

def verify_xml_signature(xml_string):
    """
    Verify the XML digital signature.
    
    Args:
        xml_string: Signed XML document as string
        
    Returns:
        Tuple of (is_valid, message, cert_info)
    """
    try:
        root = etree.fromstring(xml_string.encode('utf-8'))
        
        # Create verifier
        verifier = XMLVerifier()
        
        # Verify the signature
        verified_data = verifier.verify(root, require_x509=False)
        
        # Extract certificate info if present
        cert_info = {}
        sig_elem = root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
        if sig_elem is not None:
            x509_cert = sig_elem.find(".//{http://www.w3.org/2000/09/xmldsig#}X509Certificate")
            if x509_cert is not None and x509_cert.text:
                try:
                    cert_der = base64.b64decode(x509_cert.text)
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
                    cert_info = {
                        'subject': cert.subject.rfc4514_string(),
                        'issuer': cert.issuer.rfc4514_string(),
                        'serial': cert.serial_number,
                        'valid_from': cert.not_valid_before,
                        'valid_until': cert.not_valid_after
                    }
                except Exception as e:
                    cert_info['error'] = str(e)
        
        return True, "Signature is valid", cert_info
        
    except Exception as e:
        return False, f"Signature verification failed: {str(e)}", {}

def create_verifiable_credential_metadata(drmd_data):
    """
    Create W3C Verifiable Credentials compatible metadata for DRMD.
    
    Args:
        drmd_data: Dictionary containing DRMD administrative data
        
    Returns:
        Dictionary with VC metadata
    """
    vc_metadata = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://example.org/drmd/credentials/v1"
        ],
        "type": ["VerifiableCredential", "DigitalReferenceMaterialCredential"],
        "issuer": {
            "id": f"did:web:{drmd_data.get('producerName', 'unknown')}",
            "name": drmd_data.get('producerName', '')
        },
        "issuanceDate": datetime.utcnow().isoformat() + "Z",
        "credentialSubject": {
            "id": f"urn:drmd:{drmd_data.get('uniqueIdentifier', '')}",
            "referenceIdentifier": drmd_data.get('uniqueIdentifier', ''),
            "materialName": drmd_data.get('materialName', ''),
            "certificateType": drmd_data.get('titleOfTheDocument', '')
        }
    }
    return vc_metadata

def render_digital_signature():
    """Main rendering function for the Digital Signature tab"""
    st.header("🔐 Digital Signature & Verifiable Credentials")
    
    st.markdown("""
    This tab allows you to:
    - Add W3C XML Digital Signatures to your DRMD document
    - Generate Verifiable Credentials metadata
    - Verify existing signatures
    - Manage cryptographic certificates
    """)
    
    # Initialize session state
    if 'signature_key' not in st.session_state:
        st.session_state.signature_key = None
    if 'signature_cert' not in st.session_state:
        st.session_state.signature_cert = None
    if 'signed_xml' not in st.session_state:
        st.session_state.signed_xml = None
    
    tabs = st.tabs(["Sign Document", "Verify Signature", "Verifiable Credentials", "Certificate Management"])
    
    # Tab 1: Sign Document
    with tabs[0]:
        st.subheader("Sign DRMD Document")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            **W3C XML-DSig Enveloped Signature**
            
            The signature will be embedded in your DRMD document following the W3C standard:
            - **Canonicalization**: C14N (xml-c14n-20010315)
            - **Signature Algorithm**: RSA-SHA256
            - **Digest Algorithm**: SHA256
            - **Transform**: Enveloped Signature
            """)
        
        with col2:
            if st.button("📋 Generate Test Certificate", use_container_width=True):
                try:
                    key, cert = generate_test_certificate()
                    st.session_state.signature_key = key
                    st.session_state.signature_cert = cert
                    st.success("✅ Test certificate generated!")
                except Exception as e:
                    st.error(f"Error generating certificate: {str(e)}")
        
        # Certificate upload option
        st.markdown("---")
        st.markdown("**Or upload your own certificate:**")
        
        col1, col2 = st.columns(2)
        with col1:
            key_file = st.file_uploader("Private Key (PEM)", type=['pem', 'key'])
        with col2:
            cert_file = st.file_uploader("Certificate (PEM)", type=['pem', 'crt', 'cer'])
        
        if key_file and cert_file:
            try:
                key_pem = key_file.read()
                cert_pem = cert_file.read()
                
                st.session_state.signature_key = serialization.load_pem_private_key(
                    key_pem, password=None, backend=default_backend()
                )
                st.session_state.signature_cert = x509.load_pem_x509_certificate(
                    cert_pem, default_backend()
                )
                st.success("✅ Certificate loaded successfully!")
            except Exception as e:
                st.error(f"Error loading certificate: {str(e)}")
        
        # Sign button
        st.markdown("---")
        if st.button("🔏 Sign Document", type="primary", use_container_width=True):
            if st.session_state.signature_key is None:
                st.error("Please generate or upload a certificate first!")
            else:
                try:
                    from utils import build_xml_from_session
            
                    xml_string = build_xml_from_session()
                    if isinstance(xml_string, tuple):
                        xml_string = xml_string[0]

            
                    signed_xml = sign_xml_document(
                        xml_string,
                        st.session_state.signature_key,
                        st.session_state.signature_cert
                    )
            
                    st.session_state.signed_xml = signed_xml
            
                    st.success("✅ Document signed successfully!")
            
                    with st.expander("📄 View Signed XML"):
                        st.code(signed_xml, language='xml')
            
                    st.download_button(
                        label="⬇️ Download Signed DRMD",
                        data=signed_xml,
                        file_name=f"signed_drmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                        mime="application/xml",
                        use_container_width=True
                    )
            
                except Exception as e:
                    st.error(f"Error signing document: {str(e)}")
                    st.exception(e)

    
    # Tab 2: Verify Signature
    with tabs[1]:
        st.subheader("Verify XML Signature")
        
        verify_xml = st.text_area(
            "Paste signed XML here:",
            height=300,
            placeholder="<drmd:digitalReferenceMaterialDocument ...>"
        )
        
        uploaded_file = st.file_uploader("Or upload signed XML file", type=['xml'])
        
        if uploaded_file:
            verify_xml = uploaded_file.read().decode('utf-8')
        
        if st.button("🔍 Verify Signature", use_container_width=True):
            if not verify_xml.strip():
                st.warning("Please provide XML to verify")
            else:
                is_valid, message, cert_info = verify_xml_signature(verify_xml)
                
                if is_valid:
                    st.success(f"✅ {message}")
                    
                    if cert_info:
                        st.markdown("**Certificate Information:**")
                        for key, value in cert_info.items():
                            st.text(f"{key}: {value}")
                else:
                    st.error(f"❌ {message}")
    
    # Tab 3: Verifiable Credentials
    with tabs[2]:
        st.subheader("W3C Verifiable Credentials")
        
        st.info("""
        **Verifiable Credentials (VC)** provide a standardized way to express credentials on the web.
        
        This metadata can be:
        - Embedded in the DRMD XML as a comment or extension
        - Stored separately and linked via DIDs (Decentralized Identifiers)
        - Used for automated verification workflows
        """)
        
        if st.button("🎫 Generate VC Metadata", use_container_width=True):
            try:
                # Extract data from session state
                admin_data = {
                    'producerName': st.session_state.get('producerName', ''),
                    'uniqueIdentifier': st.session_state.get('uniqueIdentifier', ''),
                    'titleOfTheDocument': st.session_state.get('titleOfTheDocument', ''),
                    'materialName': st.session_state.get('materials', [{}])[0].get('materialName', '')
                }
                
                vc_metadata = create_verifiable_credential_metadata(admin_data)
                
                import json
                vc_json = json.dumps(vc_metadata, indent=2)
                
                st.success("✅ Verifiable Credential metadata generated!")
                
                st.code(vc_json, language='json')
                
                st.download_button(
                    label="⬇️ Download VC Metadata",
                    data=vc_json,
                    file_name=f"vc_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error generating VC metadata: {str(e)}")
    
    # Tab 4: Certificate Management
    with tabs[3]:
        st.subheader("Certificate Management")
        
        if st.session_state.signature_cert is not None:
            cert = st.session_state.signature_cert
            
            st.markdown("**Current Certificate Information:**")
            
            info_data = {
                "Subject": cert.subject.rfc4514_string(),
                "Issuer": cert.issuer.rfc4514_string(),
                "Serial Number": str(cert.serial_number),
                "Valid From": cert.not_valid_before.strftime('%Y-%m-%d %H:%M:%S'),
                "Valid Until": cert.not_valid_after.strftime('%Y-%m-%d %H:%M:%S'),
                "Signature Algorithm": cert.signature_algorithm_oid._name
            }
            
            for key, value in info_data.items():
                st.text(f"{key}: {value}")
            
            st.markdown("---")
            
            # Export certificate
            col1, col2 = st.columns(2)
            with col1:
                cert_pem = cert.public_bytes(serialization.Encoding.PEM)
                st.download_button(
                    "⬇️ Export Certificate",
                    data=cert_pem,
                    file_name="certificate.pem",
                    mime="application/x-pem-file"
                )
            
            with col2:
                if st.button("🗑️ Clear Certificate"):
                    st.session_state.signature_key = None
                    st.session_state.signature_cert = None
                    st.rerun()
        else:
            st.info("No certificate loaded. Generate or upload a certificate in the 'Sign Document' tab.")
        
        st.markdown("---")
        st.markdown("**Certificate Guidelines:**")
        st.markdown("""
        - For production use, obtain certificates from a trusted Certificate Authority (CA)
        - Store private keys securely (hardware security modules recommended)
        - Use at least 2048-bit RSA keys or equivalent elliptic curve keys
        - Consider using eIDAS-compliant certificates for EU regulatory compliance
        - Implement certificate revocation checking (CRL/OCSP)
        """)