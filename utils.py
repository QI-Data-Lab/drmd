import re, math, uuid, base64, functools, traceback, io
from datetime import date
from xml.dom import minidom
import xml.etree.ElementTree as ET
import random
import re

import pandas as pd
import streamlit as st
# Optional dependency: xmlschema (used for deep validation & diagnostics). Gracefully degrade if absent.
try:
    import xmlschema  # type: ignore
except ImportError:  # pragma: no cover - allows lightweight tests without xmlschema installed
    xmlschema = None  # sentinel
from rdflib import Graph, Namespace
from pathlib import Path as _Path
import os as _os
import pint  # <-- FIX: Added pint import

# pretty‑print / XSLT (used in Export tab later)
try:
    from lxml import etree
except ImportError:
    st.error("lxml is required. Please install it via pip install lxml.")

ureg = pint.UnitRegistry()  # <-- FIX: Added pint UnitRegistry

# -----------------------------------------------------------------------------
# Helpers & constants
# <-- FIX: Corrected default paths to point to subfolders
_APP_DIR = _Path(__file__).parent 
DEFAULT_XSD_PATH = _os.environ.get("DRMD_XSD_PATH", str(_APP_DIR / "v0.3.0" / "xsd" / "drmd.xsd"))
DEFAULT_XSL_PATH = _os.environ.get("DRMD_XSL_PATH", str(_APP_DIR / "v0.3.0" / "xsl" / "drmd.xsl"))
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
ALLOWED_TITLES = ["referenceMaterialCertificate", "productInformationSheet"]  # default first
INIT_ID = {"scheme": "", "value": "", "link": ""}
DEFAULT_PRODUCER = {
    "producerName": "",
    "producerStreet": "",
    "producerStreetNo": "",
    "producerPostCode": "",
    "producerCity": "",
    "producerCountryCode": "",
    "producerPhone": "",
    "producerFax": "",
    "producerEmail": "",
    "organizationIdentifiers": [INIT_ID.copy()]
}
DEFAULT_PERSON = {
    "personName": "",
    "description": "",
    "role": "",
    "mainSigner": False,
    "cryptElectronicSeal": False,
    "cryptElectronicSignature": False,
    "cryptElectronicTimeStamp": False,
}
OFFICIAL_STMPL = {
    k: {"name": "", "content": ""} for k in [
        "intendedUse", "commutability", "storageInformation",
        "instructionsForHandlingAndUse", "metrologicalTraceability",
        "healthAndSafetyInformation", "subcontractors", "legalNotice",
        "referenceToCertificationReport",
    ]
}

# -----------------------------------------------------------------------------
# Misc helpers

@st.cache_resource
def get_default_ui_settings():
    return {
        "font_scale": 0.85,
    }

def render_ui_settings_panel():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### UI Settings")

    font_scale = st.sidebar.slider(
        "🔠 Font Size (rem)", 0.6, 1.2, st.session_state.ui_font_scale, 0.05
    )
    if font_scale != st.session_state.ui_font_scale:
        st.session_state.ui_font_scale = font_scale
        st.rerun()

    if st.sidebar.button("Reset UI Settings"):
        st.session_state.ui_font_scale = get_default_ui_settings()["font_scale"]
        st.rerun()

def clean_text(txt: str) -> str:
    return re.sub(r"\s+", " ", txt or "").strip()

def sanitize_xml_string(text: str) -> str:
    """Removes illegal XML characters from a string."""
    if not isinstance(text, str):
        text = str(text)
    # XML 1.0 spec defines the valid character range.
    # This regex removes any character outside that range, except for common whitespace.
    illegal_xml_chars_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]')
    return illegal_xml_chars_re.sub('', text)

def xs_duration_hint() -> str:
    return "Enter a valid xs:duration – e.g. P1Y6M means 1 year 6 months"

# Data‑editor wrapper

def data_editor_df(df: pd.DataFrame, key: str, **kwargs) -> pd.DataFrame:
    try:
        updated = st.data_editor(df, key=key, **kwargs)
    except TypeError:
        updated = st.data_editor(df, key=key)
    if key in st.session_state and hasattr(st.session_state[key], "edited_rows"):
        for row_idx, changes in st.session_state[key].edited_rows.items():
            for col, new_val in changes.items():
                updated.at[int(row_idx), col] = new_val
    return updated

# Helpers to support both drmd:* and dcc:* variants in examples
def _find_one(elem, ns, *paths):
    for xp in paths:
        found = elem.find(xp, ns)
        if found is not None:
            return found
    return None

def _findall_first(elem, ns, *paths):
    for xp in paths:
        lst = elem.findall(xp, ns)
        if lst:
            return lst
    return []

# QUDT cache (Properties tab later)
@st.cache_data
def load_qudt():
    # Resolve QUDT TTL path robustly: env override, else alongside this file
    _env_path = _os.environ.get("QUDT_TTL_PATH")
    # <-- FIX: Corrected path to look in 'imports' subfolder
    _default_path = _Path(__file__).parent / "imports" / "qudt.ttl"
    _ttl_path = _env_path or str(_default_path)
    g = Graph(); g.parse(_ttl_path, format="turtle")
    Q = Namespace("http://qudt.org/schema/qudt/")
    res = {}
    for s in g.subjects(None, Q.QuantityKind):
        qn = s.split("/")[-1]
        res[qn] = [u.split("/")[-1] for u in g.objects(s, Q.applicableUnit)] or ["Custom"]
    return res
qudt_quantities = load_qudt()

# Factories used later (Properties tab)

def create_empty_materialProperties():
    return {
        "uuid": str(uuid.uuid4()),
        "id": "",
        "name": "",
        "description": "",
        "procedures": "",
        "isCertified": False,
        "results": [],
    }

def create_empty_result():
    return {
        "result_name": "",
        "description": "",
        "quantities": pd.DataFrame(columns=[
            "Name", "Label", "Identifier Scheme", "Identifier Value", "Identifier Link",
            "Value", "Quantity Kind", "Unit",
            "Uncertainty", "Coverage Factor", "Coverage Probability", "Distribution"
        ]),
        "identifiers": [],
    }




def convert_to_dsi(value_str: str, unit_str: str) -> str:
    """Converts a value and unit to its base SI representation."""
    # More robust check for empty/invalid inputs from the data editor
    if pd.isna(value_str) or pd.isna(unit_str) or not str(value_str).strip() or not str(unit_str).strip():
        return ""

    try:
        # Handle both comma and period as decimal separators
        cleaned_value = float(str(value_str).replace(',', '.'))

        quantity = ureg.Quantity(cleaned_value, unit_str)
        base_quantity = quantity.to_base_units()

        # --- FIX ---
        # Explicitly handle dimensionless quantities
        if base_quantity.dimensionless:
            return f"{base_quantity.magnitude:.6g} (dimensionless)"
        else:
            return f"{base_quantity.magnitude:.6g} {base_quantity.units:~}"

    except (ValueError, pint.errors.UndefinedUnitError, AttributeError):
        return "ERROR: Invalid value or unit"


def inject_highlighting_code():
    """Injects CSS and JavaScript to highlight the active expander."""
    highlight_js = """
    <script>
    // Function to add the highlight class
    function addHighlight(element) {
        const expander = element.closest('details');
        if (expander) {
            expander.classList.add('highlighted-expander');
        }
    }

    // Function to remove the highlight class
    function removeHighlight(element) {
        const expander = element.closest('details');
        if (expander) {
            expander.classList.remove('highlighted-expander');
        }
    }

    // Use event delegation to listen for focus events on the body
    document.body.addEventListener('focusin', function(e) {
        // e.target is the element that gained focus
        addHighlight(e.target);
    });

    document.body.addEventListener('focusout', function(e) {
        // e.target is the element that lost focus
        removeHighlight(e.target);
    });
    </script>
    """

    highlight_css = """
    <style>
        .highlighted-expander {
            border: 2px solid #4A90E2 !important;
            border-radius: 0.5rem; /* Match Streamlit's default radius */
            box-shadow: 0 0 10px rgba(74, 144, 226, 0.5);
            transition: all 0.3s ease-in-out;
        }
    </style>
    """

    st.markdown(highlight_css, unsafe_allow_html=True)
    st.markdown(highlight_js, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# XML → session‑state loader (comprehensive - loads all tabs and fields)
# <-- FIX: This is the fully corrected function from the previous steps
# -----------------------------------------------------------------------------
def load_xml_into_state(xml_bytes: bytes):
    """
    Parse XML and fully populate st.session_state, then trigger st.rerun().
    Single source of truth for loading XML templates with complete data extraction.
    """
    try:
        tree = ET.parse(io.BytesIO(xml_bytes))
        root = tree.getroot()

        # =========================================================================
        # STEP 1: Extract namespace from root tag FIRST
        # =========================================================================
        ns_match = re.match(r'\{(.*?)\}', root.tag)
        ns_drmd = ns_match.group(1) if ns_match else "https://example.org/drmd"
        
        # Define all namespaces upfront
        ns = {
            "drmd": ns_drmd,
            "dcc": "https://ptb.de/dcc",
            "si": "https://ptb.de/si",
            "ds": DS_NS
        }
        
        # Debug: Print detected namespaces
        print(f"DEBUG: Detected namespaces: {ns}")
        st.sidebar.info(f"🔍 Namespace: {ns_drmd}")

        # =========================================================================
        # STEP 2: Load Title and Unique Identifier
        # =========================================================================
        title_elem = root.find(".//drmd:titleOfTheDocument", ns)
        if title_elem is not None and title_elem.text:
            st.session_state.title_option = title_elem.text.strip() if title_elem.text.strip() in ALLOWED_TITLES else ALLOWED_TITLES[0]
        else:
            st.session_state.title_option = ALLOWED_TITLES[0]

        uid_elem = root.find(".//drmd:uniqueIdentifier", ns)
        if uid_elem is not None and uid_elem.text:
            st.session_state.persistent_id = uid_elem.text.strip()
            st.session_state.persistent_id_value = uid_elem.text.strip()
        else:
            st.session_state.persistent_id = ""
            st.session_state.persistent_id_value = ""

        # =========================================================================
        # STEP 3: Load Validity
        # =========================================================================
        validity_elem = root.find(".//drmd:validity", ns)
        if validity_elem is not None:
            if validity_elem.find("drmd:untilRevoked", ns) is not None:
                st.session_state.validity_type = "Until Revoked"
            elif validity_elem.find("drmd:timeAfterDispatch", ns) is not None:
                st.session_state.validity_type = "Time After Dispatch"
                period_elem = validity_elem.find("drmd:timeAfterDispatch/drmd:period", ns)
                if period_elem is not None and period_elem.text:
                    period_str = period_elem.text.strip()
                    st.session_state.raw_validity_period = period_str
                    
                    # Parse duration string (e.g., P3Y6M)
                    years_match = re.search(r'(\d+)Y', period_str)
                    months_match = re.search(r'(\d+)M', period_str)
                    st.session_state.duration_y = int(years_match.group(1)) if years_match else 0
                    st.session_state.duration_m = int(months_match.group(1)) if months_match else 0
                    
                dd_elem = validity_elem.find("drmd:timeAfterDispatch/drmd:dispatchDate", ns)
                if dd_elem is not None and dd_elem.text:
                    try:
                        st.session_state.date_of_issue = date.fromisoformat(dd_elem.text.strip())
                    except ValueError:
                        st.session_state.date_of_issue = date.today()
            elif validity_elem.find("drmd:specificTime", ns) is not None:
                st.session_state.validity_type = "Specific Time"
                spec_elem = validity_elem.find("drmd:specificTime", ns)
                if spec_elem is not None and spec_elem.text:
                    try:
                        st.session_state.specific_time = date.fromisoformat(spec_elem.text.strip())
                    except ValueError:
                        st.session_state.specific_time = date.today()
        else:
            st.session_state.validity_type = "Until Revoked"

        # =========================================================================
        # STEP 4: Load Document Identifiers
        # =========================================================================
        dids = []
        for did in root.findall(".//drmd:documentIdentifiers/drmd:documentIdentifier", ns):
            scheme = did.find("drmd:scheme", ns)
            value = did.find("drmd:value", ns)
            link_elem = did.find("drmd:link", ns)
            dids.append({
                "scheme": scheme.text.strip() if scheme is not None and scheme.text else "",
                "value": value.text.strip() if value is not None and value.text else "",
                "link": link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            })
        
        # Fallback to legacy identification structure
        if not dids:
            legacy_ident = root.find(".//drmd:identifications/drmd:identification", ns)
            if legacy_ident is not None:
                issuer = legacy_ident.find("drmd:issuer", ns)
                val_elem = legacy_ident.find("drmd:value", ns)
                dids = [{
                    "scheme": issuer.text.strip() if issuer is not None and issuer.text else "",
                    "value": val_elem.text.strip() if val_elem is not None and val_elem.text else "",
                    "link": ""
                }]
        
        st.session_state.documentIdentifiers = dids if dids else [INIT_ID.copy()]

        # =========================================================================
        # STEP 5: Load Administrative Data (Producers & Responsible Persons)
        # =========================================================================
        admin_data = root.find("drmd:administrativeData", ns)
        prods = []
        rps = []

        if admin_data is not None:
            print("DEBUG: Found administrativeData element")
            
            # -------------------------------------------------------------------------
            # Extract Producers
            # -------------------------------------------------------------------------
            prod_elems = admin_data.findall("drmd:referenceMaterialProducer", ns)
            print(f"DEBUG: Found {len(prod_elems)} producer(s)")
            
            for idx, prod_elem in enumerate(prod_elems):
                name_elem = prod_elem.find("drmd:name/dcc:content", ns)
                contact_elem = prod_elem.find("drmd:contact", ns)
                
                street = streetNo = postCode = city = country = ""
                phone = fax = email = ""
                
                if contact_elem is not None:
                    loc = contact_elem.find("dcc:location", ns)
                    if loc is not None:
                        street_elem = loc.find("dcc:street", ns)
                        street = street_elem.text.strip() if street_elem is not None and street_elem.text else ""
                        
                        streetNo_elem = loc.find("dcc:streetNo", ns)
                        streetNo = streetNo_elem.text.strip() if streetNo_elem is not None and streetNo_elem.text else ""
                        
                        postCode_elem = loc.find("dcc:postCode", ns)
                        postCode = postCode_elem.text.strip() if postCode_elem is not None and postCode_elem.text else ""
                        
                        city_elem = loc.find("dcc:city", ns)
                        city = city_elem.text.strip() if city_elem is not None and city_elem.text else ""
                        
                        country_elem = loc.find("dcc:countryCode", ns)
                        country = country_elem.text.strip() if country_elem is not None and country_elem.text else ""
                    
                    phone_elem = contact_elem.find("dcc:phone", ns)
                    phone = phone_elem.text.strip() if phone_elem is not None and phone_elem.text else ""
                    
                    fax_elem = contact_elem.find("dcc:fax", ns)
                    fax = fax_elem.text.strip() if fax_elem is not None and fax_elem.text else ""
                    
                    email_elem = contact_elem.find("dcc:eMail", ns)
                    email = email_elem.text.strip() if email_elem is not None and email_elem.text else ""
                
                org_ids = []
                for oid in prod_elem.findall("drmd:organizationIdentifiers/drmd:organizationIdentifier", ns):
                    sch = oid.find("drmd:scheme", ns)
                    val = oid.find("drmd:value", ns)
                    link = oid.find("drmd:link", ns)
                    org_ids.append({
                        "scheme": sch.text.strip() if sch is not None and sch.text else "",
                        "value": val.text.strip() if val is not None and val.text else "",
                        "link": link.text.strip() if link is not None and link.text else ""
                    })
                
                prod = {
                    "producerName": name_elem.text.strip() if name_elem is not None and name_elem.text else "",
                    "producerStreet": street,
                    "producerStreetNo": streetNo,
                    "producerPostCode": postCode,
                    "producerCity": city,
                    "producerCountryCode": country,
                    "producerPhone": phone,
                    "producerFax": fax,
                    "producerEmail": email,
                    "organizationIdentifiers": org_ids if org_ids else [INIT_ID.copy()]
                }
                prods.append(prod)
                print(f"DEBUG: Producer {idx+1}: {prod['producerName']}")

            # -------------------------------------------------------------------------
            # Extract Responsible Persons
            # -------------------------------------------------------------------------
            rp_elems = admin_data.findall("drmd:respPersons/dcc:respPerson", ns)
            print(f"DEBUG: Found {len(rp_elems)} responsible person(s)")
            
            if len(rp_elems) == 0:
                # Debug: Check if respPersons parent exists
                resp_parent = admin_data.find("drmd:respPersons", ns)
                if resp_parent is not None:
                    print(f"DEBUG: Found respPersons parent, children: {[child.tag for child in resp_parent]}")
                else:
                    print("DEBUG: respPersons parent NOT FOUND")
            
            for idx, rp_elem in enumerate(rp_elems):
                # Extract person name
                person_elem = rp_elem.find("dcc:person/dcc:name/dcc:content", ns)
                name = person_elem.text.strip() if person_elem is not None and person_elem.text else ""
                
                # Extract description (can have multiple dcc:content children)
                desc_elems = rp_elem.findall("dcc:description/dcc:content", ns)
                description = " ".join([d.text.strip() for d in desc_elems if d is not None and d.text]) if desc_elems else ""
                
                # Extract role
                role_elem = rp_elem.find("dcc:role", ns)
                role = role_elem.text.strip() if role_elem is not None and role_elem.text else ""
                
                # Extract boolean flags
                mainSigner_elem = rp_elem.find("dcc:mainSigner", ns)
                mainSigner = (mainSigner_elem.text.strip().lower() == "true") if mainSigner_elem is not None and mainSigner_elem.text else False
                
                cryptElectronicSeal_elem = rp_elem.find("dcc:cryptElectronicSeal", ns)
                cryptElectronicSeal = (cryptElectronicSeal_elem.text.strip().lower() == "true") if cryptElectronicSeal_elem is not None and cryptElectronicSeal_elem.text else False
                
                cryptElectronicSignature_elem = rp_elem.find("dcc:cryptElectronicSignature", ns)
                cryptElectronicSignature = (cryptElectronicSignature_elem.text.strip().lower() == "true") if cryptElectronicSignature_elem is not None and cryptElectronicSignature_elem.text else False
                
                cryptElectronicTimeStamp_elem = rp_elem.find("dcc:cryptElectronicTimeStamp", ns)
                cryptElectronicTimeStamp = (cryptElectronicTimeStamp_elem.text.strip().lower() == "true") if cryptElectronicTimeStamp_elem is not None and cryptElectronicTimeStamp_elem.text else False
                
                rp = {
                    "personName": name,
                    "description": description,
                    "role": role,
                    "mainSigner": mainSigner,
                    "cryptElectronicSeal": cryptElectronicSeal,
                    "cryptElectronicSignature": cryptElectronicSignature,
                    "cryptElectronicTimeStamp": cryptElectronicTimeStamp
                }
                rps.append(rp)
                print(f"DEBUG: Responsible Person {idx+1}: {name} | Role: {role} | MainSigner: {mainSigner}")
        
        else:
            print("DEBUG: administrativeData element NOT FOUND!")

        # CRITICAL: Always replace session state (no merge)
        st.session_state.producers = prods if prods else [DEFAULT_PRODUCER.copy()]
        st.session_state.responsible_persons = rps if rps else [DEFAULT_PERSON.copy()]
        
        print(f"DEBUG: Loaded {len(st.session_state.producers)} producer(s)")
        print(f"DEBUG: Loaded {len(st.session_state.responsible_persons)} responsible person(s)")

        # =========================================================================
        # STEP 6: Load Materials
        # =========================================================================
        mats = []
        for mat_elem in root.findall(".//drmd:materials/drmd:material", ns):
            name_elem = mat_elem.find("drmd:name/dcc:content", ns)
            desc_elem = mat_elem.find("drmd:description/dcc:content", ns)
    
            # Extract minimumSampleSize with both value and unit
            min_sample_value = ""
            min_sample_unit = ""
            sample_elem = mat_elem.find("drmd:minimumSampleSize/dcc:itemQuantity/si:realListXMLList", ns)
            if sample_elem is not None:
                value_elem = sample_elem.find("si:valueXMLList", ns)
                unit_elem = sample_elem.find("si:unitXMLList", ns)
                min_sample_value = value_elem.text.strip() if value_elem is not None and value_elem.text else ""
                min_sample_unit = unit_elem.text.strip() if unit_elem is not None and unit_elem.text else ""
    
            # Extract itemQuantities with both value and unit
            item_qty_value = ""
            item_qty_unit = ""
            item_qty_elem = mat_elem.find("drmd:itemQuantities/dcc:itemQuantity/si:realListXMLList", ns)
            if item_qty_elem is not None:
                value_elem = item_qty_elem.find("si:valueXMLList", ns)
                unit_elem = item_qty_elem.find("si:unitXMLList", ns)
                item_qty_value = value_elem.text.strip() if value_elem is not None and value_elem.text else ""
                item_qty_unit = unit_elem.text.strip() if unit_elem is not None and unit_elem.text else ""

            mat = {
                "uuid": str(uuid.uuid4()),
                "name": name_elem.text.strip() if name_elem is not None and name_elem.text else "",
                "description": " ".join(desc_elem.text.split()) if desc_elem is not None and desc_elem.text else "",
                "materialClass": "",
                "minimumSampleSize": f"{min_sample_value} {min_sample_unit}".strip() if min_sample_value else "",
                "itemQuantities": f"{item_qty_value} {item_qty_unit}".strip() if item_qty_value else "",
                "isCertified": mat_elem.get("isCertified", "false").lower() == "true",
                "materialIdentifiers": []
            }

            # Load material identifiers
            for mid in mat_elem.findall("drmd:materialIdentifiers/drmd:materialIdentifier", ns):
                sch = mid.find("drmd:scheme", ns)
                val = mid.find("drmd:value", ns)
                link_elem = mid.find("drmd:link", ns)
                mat["materialIdentifiers"].append({
                    "scheme": sch.text.strip() if sch is not None and sch.text else "",
                    "value": val.text.strip() if val is not None and val.text else "",
                    "link": link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                })

            if not mat["materialIdentifiers"]:
                mat["materialIdentifiers"].append(INIT_ID.copy())

            mats.append(mat)

        st.session_state.materials = mats if mats else [SESSION_DEFAULTS["materials"][0].copy()]

        # =========================================================================
        # STEP 7: Load Material Properties
        # =========================================================================
        mps = []
        mp_list_elem = root.find("drmd:materialPropertiesList", ns)
        if mp_list_elem is not None:
            for mp_elem in mp_list_elem.findall("drmd:materialProperties", ns):
                mp_dict = {
                    "uuid": str(uuid.uuid4()),
                    "id": mp_elem.attrib.get("id", "").strip(),
                    "isCertified": mp_elem.attrib.get("isCertified", "false").lower() == "true",
                    "results": []
                }
                
                # Name (required)
                name_elem = mp_elem.find("drmd:name/dcc:content", ns)
                mp_dict["name"] = clean_text(name_elem.text) if name_elem is not None and name_elem.text else ""
                mp_dict["displayName"] = mp_dict["name"]
                
                # Description (optional)
                desc_elem = mp_elem.find("drmd:description/dcc:content", ns)
                mp_dict["description"] = clean_text(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                
                # Procedures (optional)
                proc_elem = mp_elem.find("drmd:procedures", ns)
                if proc_elem is not None:
                    used_method = proc_elem.find("dcc:usedMethod", ns)
                    if used_method is not None:
                        # Get method name
                        name_elem = used_method.find("dcc:name/dcc:content", ns)
                        method_name = clean_text(name_elem.text) if name_elem is not None and name_elem.text else ""
                        # Get method description
                        desc_elem = used_method.find("dcc:description/dcc:content", ns)
                        method_desc = clean_text(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                        mp_dict["procedures"] = f"{method_name}: {method_desc}" if method_name or method_desc else ""
                    else:
                        mp_dict["procedures"] = ""
                else:
                    mp_dict["procedures"] = ""

                # Results (required)
                results = []
                results_elem = _find_one(mp_elem, ns, "drmd:results")
                if results_elem is not None:
                    for res_elem in _findall_first(results_elem, ns, "drmd:result", "dcc:result"):
                        res_dict = {}
                        
                        # Result name
                        res_name_elem = _find_one(res_elem, ns, "drmd:name/dcc:content", "dcc:name/dcc:content")
                        res_dict["result_name"] = clean_text(res_name_elem.text) if res_name_elem is not None and res_name_elem.text else ""
                        
                        # Result description
                        res_desc_elem = _find_one(res_elem, ns, "drmd:description/dcc:content", "dcc:description/dcc:content")
                        res_dict["description"] = clean_text(res_desc_elem.text) if res_desc_elem is not None and res_desc_elem.text else ""
                        
                        # Quantities
                        quantities = []
                        row_ids = []
                        
                        data_elem = _find_one(res_elem, ns, "drmd:data", "dcc:data")
                        if data_elem is not None:
                            list_elem = _find_one(data_elem, ns, "drmd:list", "dcc:list")
                            if list_elem is not None:
                                for quant_elem in _findall_first(list_elem, ns, "drmd:quantity", "dcc:quantity"):
                                    quant = {}
                                    q_ids = []
                                    
                                    # Quantity name
                                    qname_elem = _find_one(quant_elem, ns, "drmd:name/dcc:content", "dcc:name/dcc:content")
                                    quant["Name"] = clean_text(qname_elem.text) if qname_elem is not None and qname_elem.text else ""
                                    quant["Label"] = ""
                                    quant["Quantity Kind"] = ""
                                    
                                    # Get real value
                                    real_elem = quant_elem.find("si:real", ns)
                                    if real_elem is not None:
                                        value_elem = real_elem.find("si:value", ns)
                                        quant["Value"] = float(value_elem.text.strip()) if value_elem is not None and value_elem.text and value_elem.text.strip().replace('.', '', 1).replace('-', '', 1).isdigit() else None
                                        
                                        unit_elem = real_elem.find("si:unit", ns)
                                        quant["Unit"] = unit_elem.text.strip() if unit_elem is not None and unit_elem.text else ""
                                        
                                        # Measurement uncertainty
                                        mu_elem = real_elem.find("si:measurementUncertaintyUnivariate/si:expandedMU", ns)
                                        if mu_elem is not None:
                                            val_mu = mu_elem.find("si:valueExpandedMU", ns)
                                            quant["Uncertainty"] = float(val_mu.text.strip()) if val_mu is not None and val_mu.text else None
                                            
                                            cf_elem = mu_elem.find("si:coverageFactor", ns)
                                            quant["Coverage Factor"] = float(cf_elem.text.strip()) if cf_elem is not None and cf_elem.text else None
                                            
                                            cp_elem = mu_elem.find("si:coverageProbability", ns)
                                            quant["Coverage Probability"] = float(cp_elem.text.strip()) if cp_elem is not None and cp_elem.text else None
                                            
                                            dist_elem = mu_elem.find("si:distribution", ns)
                                            quant["Distribution"] = dist_elem.text.strip() if dist_elem is not None and dist_elem.text else ""
                                        else:
                                            quant["Uncertainty"] = None
                                            quant["Coverage Factor"] = None
                                            quant["Coverage Probability"] = None
                                            quant["Distribution"] = ""
                                    else:
                                        quant["Value"] = None
                                        quant["Unit"] = ""
                                        quant["Uncertainty"] = None
                                        quant["Coverage Factor"] = None
                                        quant["Coverage Probability"] = None
                                        quant["Distribution"] = ""
                                    
                                    # Property identifiers
                                    for pid in quant_elem.findall("drmd:propertyIdentifiers/drmd:propertyIdentifier", ns):
                                        s = pid.find("drmd:scheme", ns)
                                        v = pid.find("drmd:value", ns)
                                        l = pid.find("drmd:link", ns)
                                        q_ids.append({
                                            "scheme": s.text.strip() if s is not None and s.text else "",
                                            "value": v.text.strip() if v is not None and v.text else "",
                                            "link": l.text.strip() if l is not None and l.text else ""
                                        })
                                    
                                    # Flatten first identifier into columns
                                    if q_ids:
                                        quant["Identifier Scheme"] = q_ids[0]["scheme"]
                                        quant["Identifier Value"] = q_ids[0]["value"]
                                        quant["Identifier Link"] = q_ids[0]["link"]
                                    else:
                                        quant["Identifier Scheme"] = ""
                                        quant["Identifier Value"] = ""
                                        quant["Identifier Link"] = ""
                                    
                                    quantities.append(quant)
                                    row_ids.append(q_ids or [])
                        
                        # Convert to DataFrame
                        df_quant = pd.DataFrame(quantities, columns=[
                            "Name", "Label", "Identifier Scheme", "Identifier Value", "Identifier Link",
                            "Value", "Quantity Kind", "Unit",
                            "Uncertainty", "Coverage Factor", "Coverage Probability", "Distribution"
                        ])
                        res_dict["quantities"] = df_quant
                        res_dict["identifiers"] = row_ids
                        
                        results.append(res_dict)
                
                mp_dict["results"] = results
                mps.append(mp_dict)
        
        st.session_state.materialProperties = mps if mps else SESSION_DEFAULTS["materialProperties"]

        # =========================================================================
        # STEP 8: Load Statements
        # =========================================================================
        official_keys = [
            "intendedUse", "commutability", "storageInformation",
            "instructionsForHandlingAndUse", "metrologicalTraceability",
            "healthAndSafetyInformation", "subcontractors",
            "legalNotice", "referenceToCertificationReport"
        ]
        official_statements = {key: {"name": "", "content": ""} for key in official_keys}
        custom_statements = []

        statements_elem = root.find(".//drmd:statements", ns)
        if statements_elem is not None:
            for child in statements_elem:
                tag = child.tag.split("}")[1] if "}" in child.tag else child.tag
                
                name_elem = child.find("dcc:name/dcc:content", ns)
                name_text = clean_text(name_elem.text) if name_elem is not None and name_elem.text else ""
                
                contents = []
                for elem in child.findall("dcc:content", ns):
                    if elem.text:
                        contents.append(clean_text(elem.text))
                content_text = "\n".join(contents)

                if tag in official_keys:
                    official_statements[tag] = {"name": name_text, "content": content_text}
                elif tag == "statement":
                    custom_statements.append({"name": name_text, "content": content_text})

        st.session_state.official_statements = official_statements
        st.session_state.custom_statements = custom_statements

        # =========================================================================
        # STEP 9: Load Comments
        # =========================================================================
        comments = []
        for comment_elem in root.findall(".//drmd:comment", ns):
            if comment_elem.text:
                comments.append(comment_elem.text.strip())
        st.session_state.comment = "\n".join(comments) if comments else ""

        # =========================================================================
        # STEP 10: Load Embedded Files
        # =========================================================================
        embedded_files = []
        for doc_elem in root.findall(".//drmd:document", ns):
            file_name = doc_elem.find("dcc:fileName", ns).text if doc_elem.find("dcc:fileName", ns) is not None else "unknown"
            mime_type = doc_elem.find("dcc:mimeType", ns).text if doc_elem.find("dcc:mimeType", ns) is not None else "application/octet-stream"
            base64_data = doc_elem.find("dcc:dataBase64", ns).text if doc_elem.find("dcc:dataBase64", ns) is not None else ""

            file_bytes = base64.b64decode(base64_data) if base64_data else b""

            embedded_files.append({
                "name": file_name,
                "mimeType": mime_type,
                "data": file_bytes
            })

        if embedded_files:
            st.session_state.embedded_files = embedded_files

        # =========================================================================
        # STEP 11: Mark template as loaded and trigger rerun
        # =========================================================================
        st.session_state.template_loaded = True

        # CRITICAL FIX: Increment version counter to force widget refresh
        if "data_version" not in st.session_state:
            st.session_state.data_version = 0
        st.session_state.data_version += 1

        st.sidebar.success("✅ XML template loaded successfully!")

        # CRITICAL: Trigger rerun to rebind all widgets
        st.rerun()

    except Exception as e:
        st.error(f"❌ A critical error occurred during XML parsing:\n\n{traceback.format_exc()}")
        print(f"ERROR: {traceback.format_exc()}")
        return


# -----------------------------------------------------------------------------
# Robust session‑state initialisation (covers all tabs)
SESSION_DEFAULTS = {
    "documentIdentifiers": [INIT_ID.copy()],
    "materials": [{"uuid": str(uuid.uuid4()), "name": "", "description": "", "materialClass": "",
                    "minimumSampleSize": "", "itemQuantities": "", "isCertified": False,
                    "materialIdentifiers": [INIT_ID.copy()]}],
    "materialProperties": [
        {
            "uuid": str(uuid.uuid4()), "id": "",
            "name": "Certified Properties Set",
            "displayName": "Certified Values",
            "description": "", "procedures": "", "results": [],
        },
        {
            "uuid": str(uuid.uuid4()), "id": "",
            "name": "Informative Properties Set",
            "displayName": "Informative Values",
            "description": "", "procedures": "", "results": [],
        },
    ],
    "producers": [DEFAULT_PRODUCER.copy()],
    "responsible_persons": [DEFAULT_PERSON.copy()],
    "official_statements": OFFICIAL_STMPL.copy(),
    "custom_statements": [],
    "materials_df": pd.DataFrame(columns=["Material Name", "Description", "Minimum Sample Size", "Unit"]),
    "mp_tables": [],
    "selected_quantity": "", "selected_unit": "", "coverage_factor": 2.0,
    "coverage_probability": 0.95, "distribution": "normal",
    "title_option": None,  # default
    "persistent_id": "",
    "persistent_id_value": "",
    "validity_type": "Until Revoked", "raw_validity_period": "",
    "date_of_issue": date.today(), "specific_time": date.today(),
    "template_loaded": False,
    "comar_xml_data": "",
    "show_comar_instructions": False,
    "generated_xml": "",
    "generated_html": "",
    "xml_is_valid": False,
    "validation_message": "",
    "data_version": 0,
}

# -----------------------------------------------------------------------------
# Export-specific helpers
# -----------------------------------------------------------------------------

def add_if_valid(parent, tag, value, ns):
    """Adds a subelement with tag to parent if value is not None, empty, or NaN.
       Returns the new element or None.
    """
    if value is None:
        return None
    try:
        # If the value is a float and is NaN, skip it.
        if isinstance(value, float) and math.isnan(value):
            return None
    except Exception:
        pass
    if str(value).strip() == "":
        return None
    elem = ET.SubElement(parent, f"{{{ns}}}{tag}")
    elem.text = str(value).strip()
    return elem

def export_identifier_list(parent, tag, id_list, ns_drmd):
    """Export identifier list (e.g. propertyIdentifiers) respecting schema constraints.

    Rules:
    - Skip creation entirely if id_list is falsy or no entries have BOTH non-empty scheme & value.
    - Whitespace-only strings are treated as empty.
    - link is optional; only emitted if non-empty.
    - Returns created outer element or None.
    This prevents invalid empty containers like <drmd:propertyIdentifiers/> which violate
    the sequence requirement (must contain at least one child element).
    """
    singular = tag[:-1] if tag.endswith('s') else tag
    valid = []
    for ident in (id_list or []):
        if not isinstance(ident, dict):
            continue
        scheme = (ident.get("scheme") or "").strip()
        value = (ident.get("value") or "").strip()
        link = (ident.get("link") or "").strip()
        if scheme and value:
            valid.append({"scheme": scheme, "value": value, "link": link})
    if not valid:
        return None
    outer = ET.SubElement(parent, f"{{{ns_drmd}}}{tag}")
    for ident in valid:
        ident_elem = ET.SubElement(outer, f"{{{ns_drmd}}}{singular}")
        ET.SubElement(ident_elem, f"{{{ns_drmd}}}scheme").text = ident["scheme"]
        ET.SubElement(ident_elem, f"{{{ns_drmd}}}value").text = ident["value"]
        if ident["link"]:
            ET.SubElement(ident_elem, f"{{{ns_drmd}}}link").text = ident["link"]
    return outer