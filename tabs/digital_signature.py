import streamlit as st
import base64
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from lxml import etree
from signxml import XMLSigner, methods

def generate_test_certificate():
    """Generate self-signed certificate for testing"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    common_name = "test.bam.de"
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BAM Test Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    ski = x509.SubjectKeyIdentifier.from_public_key(private_key.public_key())
    aki = x509.AuthorityKeyIdentifier(
        key_identifier=ski.key_identifier,
        authority_cert_issuer=None,
        authority_cert_serial_number=None
    )
    
    key_usage = x509.KeyUsage(
        digital_signature=True,
        content_commitment=False,
        key_encipherment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False
    )
    
    san = x509.SubjectAlternativeName([x509.DNSName(common_name)])

    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(private_key.public_key())
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.utcnow())
    builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=365))
    builder = builder.add_extension(ski, critical=False)
    builder = builder.add_extension(aki, critical=False)
    builder = builder.add_extension(key_usage, critical=True)
    builder = builder.add_extension(san, critical=False)

    cert = builder.sign(private_key, hashes.SHA256(), default_backend())
    return private_key, cert


def sign_xml_document(xml_string, private_key, certificate):
    """Sign XML document using W3C XML-DSig"""
    try:
        xml_string = xml_string.replace("\u00A0", " ")
        parser = etree.XMLParser(remove_blank_text=False)
        root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
        
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        
        signed_root = signer.sign(root, key=private_key_pem, cert=cert_pem)
        
        signed_xml_bytes = etree.tostring(
            signed_root,
            encoding='utf-8',
            pretty_print=False,
            xml_declaration=True
        )
        
        return signed_xml_bytes.decode('utf-8')
        
    except Exception as e:
        raise Exception(f"Error signing XML: {str(e)}")


def render_digital_signature():
    """Main rendering function for Digital Signature tab"""
    st.header("🔐 Digital Signature")
    
    st.markdown("""
    This tab allows you to manage cryptographic certificates for signing your DRMD documents.
    After setting up your certificate here, you can sign the document in the **Validate & Export** tab.
    """)
    
    # Initialize session state
    if 'signature_key' not in st.session_state:
        st.session_state.signature_key = None
    if 'signature_cert' not in st.session_state:
        st.session_state.signature_cert = None
    
    # === CERTIFICATE SETUP ===
    st.subheader("Certificate Setup")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **W3C XML-DSig Enveloped Signature**
        
        - **Canonicalization**: C14N 1.0
        - **Signature Algorithm**: RSA-SHA256
        - **Digest Algorithm**: SHA256
        - **Transform**: Enveloped Signature
        """)
    
    with col2:
        if st.button("📋 Generate Test Certificate", use_container_width=True):
            try:
                with st.spinner("Generating certificate..."):
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
            
            try:
                st.session_state.signature_key = serialization.load_pem_private_key(
                    key_pem, password=None, backend=default_backend()
                )
                st.session_state.signature_cert = x509.load_pem_x509_certificate(
                    cert_pem, default_backend()
                )
                st.success("✅ Certificate loaded successfully!")
            except TypeError:
                st.warning("Private key is password protected.")
                password = st.text_input("Enter Private Key Password:", type="password")
                if password:
                    try:
                        st.session_state.signature_key = serialization.load_pem_private_key(
                            key_pem, password=password.encode(), backend=default_backend()
                        )
                        st.session_state.signature_cert = x509.load_pem_x509_certificate(
                            cert_pem, default_backend()
                        )
                        st.success("✅ Certificate loaded successfully!")
                    except Exception as e:
                        st.error(f"Failed to decrypt key: {e}")
                else:
                    st.info("Please enter the password to load the key.")
                    st.stop()
        except Exception as e:
            st.error(f"Error loading certificate: {str(e)}")
    
    st.divider()
    
    # === CERTIFICATE MANAGEMENT ===
    st.subheader("Certificate Management")
    
    if st.session_state.signature_cert is not None:
        cert = st.session_state.signature_cert
        
        st.markdown("**Current Certificate Information:**")
        
        info_data = {
            "Subject": cert.subject.rfc4514_string(),
            "Issuer": cert.issuer.rfc4514_string(),
            "Serial Number": str(cert.serial_number),
            "Valid From": cert.not_valid_before.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "Valid Until": cert.not_valid_after.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "Signature Algorithm": cert.signature_algorithm_oid._name
        }
        
        try:
            san_ext = cert.extensions.get_extension_for_oid(x509.OID_SUBJECT_ALTERNATIVE_NAME)
            info_data['SubjectAlternativeName'] = [str(name) for name in san_ext.value]
        except x509.extensions.ExtensionNotFound:
            info_data['SubjectAlternativeName'] = 'Not present'
        
        st.json(info_data, expanded=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            st.download_button(
                "⬇️ Export Certificate (.pem)",
                data=cert_pem,
                file_name="certificate.pem",
                mime="application/x-pem-file",
                use_container_width=True
            )
        
        with col2:
            if st.button("🗑️ Clear Certificate", use_container_width=True):
                st.session_state.signature_key = None
                st.session_state.signature_cert = None
                st.rerun()
        
        st.success("✅ Certificate ready! Go to **Validate & Export** tab to sign your document.")
    else:
        st.info("No certificate loaded. Generate or upload a certificate above.")
    
    st.markdown("---")
    st.markdown("**Certificate Guidelines:**")
    st.markdown("""
    - For production, use CA-issued certificates (not self-signed)
    - Store private keys securely (HSM, encrypted vaults)
    - Never commit private keys to version control
    - Use ≥2048-bit RSA or equivalent ECC keys
    - Consider eIDAS compliance for EU regulatory requirements
    - Implement certificate revocation checking (CRL/OCSP) in production
    """)
