import streamlit as st
import re
import random
from datetime import date
from utils import INIT_ID, ALLOWED_TITLES, DEFAULT_PRODUCER, DEFAULT_PERSON

def render_administrative_data():
    """Render the Administrative Data tab with proper versioned widget binding."""
    
    # Get version counter for dynamic keys
    data_version = st.session_state.get("data_version", 0)
    
    # =============================================================================
    # Basic Information Section
    # =============================================================================
    with st.expander("📄 Basic Information", expanded=True):
        col1, col2, col3 = st.columns([3, 3, 1])
        
        with col1:
            # Title selection
            title_idx = None
            if st.session_state.get("title_option") in ALLOWED_TITLES:
                title_idx = ALLOWED_TITLES.index(st.session_state.title_option)
            
            selected_title = st.selectbox(
                "Title of the Document",
                ALLOWED_TITLES,
                index=title_idx,
                placeholder="Select a document type...",
                format_func=lambda x: re.sub(r'(?<!^)(?=[A-Z])', ' ', x).title(),
                key=f"title_select_v{data_version}"
            )
            if selected_title:
                st.session_state.title_option = selected_title
        
        with col2:
            # --- FIX START ---
            # This logic ensures a UUID is always present in the session state.
            
            # 1. Ensure a UUID is always present on load
            if not st.session_state.get("uniqueIdentifier"):
                st.session_state.uniqueIdentifier = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            
            # 2. Get the guaranteed value from the session state
            current_uid = st.session_state.uniqueIdentifier

            # 3. Create the text input widget
            new_uid_from_input = st.text_input(
                "Unique Identifier",
                value=current_uid, # Bind directly to the guaranteed value
                placeholder="Click button to generate",
                disabled=False,
                help="A UUID automatically assigned to this document.",
                key=f"uid_input_v{data_version}"
            )
            
            # 4. Validate the user's change
            if new_uid_from_input != current_uid:
                if not new_uid_from_input:
                    # User tried to delete it
                    st.warning("Unique Identifier cannot be empty.")
                    # Revert the change by re-assigning the old value to the session state
                    st.session_state.uniqueIdentifier = current_uid
                    st.rerun() # Force a rerun to show the restored value
                else:
                    # User changed it to a new, non-empty value
                    st.session_state.uniqueIdentifier = new_uid_from_input
            # --- FIX END ---

        with col3:
            st.markdown("##") # Add vertical space
            if st.button("🔄", help="Generate new UUID", key=f"gen_uuid_v{data_version}"):
                new_uuid = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
                st.session_state.uniqueIdentifier = new_uuid
                st.session_state.data_version = st.session_state.get("data_version", 0) + 1
                st.rerun()



        # Document Identifiers
        st.markdown("#### Document Identifiers")
        
        for didx, did in enumerate(st.session_state.documentIdentifiers):
            cols = st.columns([2, 3, 4, 1])
            
            new_scheme = cols[0].text_input(
                "Scheme", 
                value=did.get("scheme", ""), 
                key=f"doc_scheme_{didx}_v{data_version}"
            )
            st.session_state.documentIdentifiers[didx]["scheme"] = new_scheme
            
            new_value = cols[1].text_input(
                "Value", 
                value=did.get("value", ""), 
                key=f"doc_value_{didx}_v{data_version}"
            )
            st.session_state.documentIdentifiers[didx]["value"] = new_value
            
            new_link = cols[2].text_input(
                "Link", 
                value=did.get("link", ""), 
                key=f"doc_link_{didx}_v{data_version}"
            )
            st.session_state.documentIdentifiers[didx]["link"] = new_link
            
            if cols[3].button("🗑️", key=f"del_doc_{didx}_v{data_version}") and len(st.session_state.documentIdentifiers) > 1:
                st.session_state.documentIdentifiers.pop(didx)
                st.rerun()
        
        if st.button("➕ Add Identifier", key=f"add_doc_id_v{data_version}"):
            st.session_state.documentIdentifiers.append(INIT_ID.copy())
            st.rerun()

        st.markdown("---")

        # Period of Validity
        st.markdown("#### Period of Validity")
        cols = st.columns([3, 3, 3])
        
        with cols[0]:
            v_type = st.selectbox(
                "Validity Type", 
                ["Until Revoked", "Time After Dispatch", "Specific Time"],
                index=["Until Revoked", "Time After Dispatch", "Specific Time"].index(st.session_state.get("validity_type", "Until Revoked")),
                key=f"validity_type_v{data_version}"
            )
            st.session_state.validity_type = v_type
        
        if v_type == "Time After Dispatch":
            with cols[1]:
                sub_cols = st.columns(2)
                with sub_cols[0]:
                    years = st.number_input(
                        "Years", 
                        min_value=0, 
                        step=1, 
                        value=st.session_state.get("duration_y", 0),
                        key=f"duration_y_v{data_version}"
                    )
                    st.session_state.duration_y = years
                
                with sub_cols[1]:
                    months = st.number_input(
                        "Months", 
                        min_value=0, 
                        max_value=11, 
                        step=1,
                        value=st.session_state.get("duration_m", 0),
                        key=f"duration_m_v{data_version}"
                    )
                    st.session_state.duration_m = months
            
            with cols[2]:
                iso_parts = []
                if years > 0:
                    iso_parts.append(f"{years}Y")
                if months > 0:
                    iso_parts.append(f"{months}M")
                iso_duration = f"P{''.join(iso_parts)}" if iso_parts else "P"
                st.session_state.raw_validity_period = iso_duration
                
                st.write("**ISO 8601 Format:**")
                if iso_parts:
                    st.success(f"`{iso_duration}`")
                else:
                    st.info("`P` (no duration set)")
            
            dispatch_date = st.date_input(
                "Dispatch Date", 
                value=st.session_state.get("date_of_issue", date.today()),
                max_value=date.max,
                key=f"dispatch_date_v{data_version}"
            )
            st.session_state.date_of_issue = dispatch_date
        
        elif v_type == "Specific Time":
            with cols[1]:
                specific_date = st.date_input(
                    "Valid Until Date", 
                    value=st.session_state.get("specific_time", date.today()),
                    max_value=date.max,
                    key=f"specific_time_v{data_version}"
                )
                st.session_state.specific_time = specific_date
            
            cols[2].markdown(" ")
        else:
            cols[1].markdown(" ")
            cols[2].markdown(" ")

    # =============================================================================
    # Reference Material Producer and Responsible Persons Section
    # =============================================================================
    with st.expander("🏢 Reference Material Producer and Responsible Persons", expanded=True):
        
        # -------------------------------------------------------------------------
        # PRODUCERS SECTION
        # -------------------------------------------------------------------------
        st.markdown("### Reference Material Producer")
        
        for idx, prod in enumerate(st.session_state.producers):
            if len(st.session_state.producers) > 1:
                st.markdown(f"#### Producer {idx+1}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Name *", 
                    value=prod.get("producerName", ""), 
                    key=f"prod_name_{idx}_v{data_version}",
                    help="Organization or company name"
                )
                st.session_state.producers[idx]["producerName"] = name
                
                email = st.text_input(
                    "Email *", 
                    value=prod.get("producerEmail", ""), 
                    key=f"prod_email_{idx}_v{data_version}",
                    placeholder="contact@example.com"
                )
                st.session_state.producers[idx]["producerEmail"] = email
                
                phone = st.text_input(
                    "Phone", 
                    value=prod.get("producerPhone", ""), 
                    key=f"prod_phone_{idx}_v{data_version}",
                    placeholder="+49 123 456789"
                )
                st.session_state.producers[idx]["producerPhone"] = phone

            with col2:
                addr_cols = st.columns([3, 1])
                with addr_cols[0]:
                    street = st.text_input(
                        "Street", 
                        value=prod.get("producerStreet", ""), 
                        key=f"prod_street_{idx}_v{data_version}"
                    )
                    st.session_state.producers[idx]["producerStreet"] = street
                
                with addr_cols[1]:
                    street_no = st.text_input(
                        "No.", 
                        value=prod.get("producerStreetNo", ""), 
                        key=f"prod_streetno_{idx}_v{data_version}"
                    )
                    st.session_state.producers[idx]["producerStreetNo"] = street_no

                city_cols = st.columns([1, 2, 1])
                with city_cols[0]:
                    postcode = st.text_input(
                        "Post Code", 
                        value=prod.get("producerPostCode", ""), 
                        key=f"prod_postcode_{idx}_v{data_version}"
                    )
                    st.session_state.producers[idx]["producerPostCode"] = postcode
                
                with city_cols[1]:
                    city = st.text_input(
                        "City", 
                        value=prod.get("producerCity", ""), 
                        key=f"prod_city_{idx}_v{data_version}"
                    )
                    st.session_state.producers[idx]["producerCity"] = city
                
                with city_cols[2]:
                    country = st.text_input(
                        "Country", 
                        value=prod.get("producerCountryCode", ""), 
                        key=f"prod_country_{idx}_v{data_version}",
                        placeholder="DE"
                    )
                    st.session_state.producers[idx]["producerCountryCode"] = country

                fax = st.text_input(
                    "Fax", 
                    value=prod.get("producerFax", ""), 
                    key=f"prod_fax_{idx}_v{data_version}"
                )
                st.session_state.producers[idx]["producerFax"] = fax

            # Organization Identifiers
            st.markdown("**Organization Identifiers**")
            
            if not prod.get("organizationIdentifiers"):
                st.session_state.producers[idx]["organizationIdentifiers"] = [INIT_ID.copy()]
            
            for oid_idx, oid in enumerate(prod["organizationIdentifiers"]):
                cols_id = st.columns([2, 3, 4, 1])
                
                scheme = cols_id[0].text_input(
                    "Scheme", 
                    value=oid.get("scheme", ""), 
                    key=f"org_scheme_{idx}_{oid_idx}_v{data_version}"
                )
                st.session_state.producers[idx]["organizationIdentifiers"][oid_idx]["scheme"] = scheme
                
                value = cols_id[1].text_input(
                    "Value", 
                    value=oid.get("value", ""), 
                    key=f"org_value_{idx}_{oid_idx}_v{data_version}"
                )
                st.session_state.producers[idx]["organizationIdentifiers"][oid_idx]["value"] = value
                
                link = cols_id[2].text_input(
                    "Link", 
                    value=oid.get("link", ""), 
                    key=f"org_link_{idx}_{oid_idx}_v{data_version}"
                )
                st.session_state.producers[idx]["organizationIdentifiers"][oid_idx]["link"] = link
                
                if cols_id[3].button("🗑️", key=f"del_org_{idx}_{oid_idx}_v{data_version}") and len(prod["organizationIdentifiers"]) > 1:
                    st.session_state.producers[idx]["organizationIdentifiers"].pop(oid_idx)
                    st.rerun()
            
            if st.button("➕ Add Organization Identifier", key=f"add_org_id_{idx}_v{data_version}"):
                st.session_state.producers[idx]["organizationIdentifiers"].append(INIT_ID.copy())
                st.rerun()
            
            if len(st.session_state.producers) > 1:
                if st.button(f"🗑️ Remove Producer {idx+1}", key=f"remove_prod_{idx}_v{data_version}"):
                    st.session_state.producers.pop(idx)
                    st.rerun()
            
            st.markdown("---")
        
        if st.button("➕ Add Producer", key=f"add_producer_v{data_version}"):
            st.session_state.producers.append(DEFAULT_PRODUCER.copy())
            st.rerun()
        
        st.markdown("---")
        st.markdown("---")

        # -------------------------------------------------------------------------
        # RESPONSIBLE PERSONS SECTION
        # -------------------------------------------------------------------------
        st.markdown("### 👥 Responsible Persons")
        
        for idx, rp in enumerate(st.session_state.responsible_persons):
            st.markdown(f"#### Responsible Person {idx+1}")
            
            cols = st.columns([2, 2, 2])
            
            with cols[0]:
                person_name = st.text_input(
                    "Name *", 
                    value=rp.get("personName", ""), 
                    key=f"rp_name_{idx}_v{data_version}",
                    help="Full name of the responsible person"
                )
                st.session_state.responsible_persons[idx]["personName"] = person_name
                
                role = st.text_input(
                    "Role *", 
                    value=rp.get("role", ""), 
                    key=f"rp_role_{idx}_v{data_version}",
                    placeholder="e.g., Chief Officer, Certifier"
                )
                st.session_state.responsible_persons[idx]["role"] = role

            with cols[1]:
                description = st.text_area(
                    "Description", 
                    value=rp.get("description", ""), 
                    height=100, 
                    key=f"rp_desc_{idx}_v{data_version}",
                    help="Additional information about the person's responsibilities"
                )
                st.session_state.responsible_persons[idx]["description"] = description

            with cols[2]:
                st.markdown("**Digital Signature Options:**")
                
                main_signer = st.checkbox(
                    "Main Signer", 
                    value=rp.get("mainSigner", False), 
                    key=f"rp_main_{idx}_v{data_version}",
                    help="Primary person responsible for signing"
                )
                st.session_state.responsible_persons[idx]["mainSigner"] = main_signer
                
                seal = st.checkbox(
                    "Electronic Seal", 
                    value=rp.get("cryptElectronicSeal", False), 
                    key=f"rp_seal_{idx}_v{data_version}"
                )
                st.session_state.responsible_persons[idx]["cryptElectronicSeal"] = seal
                
                signature = st.checkbox(
                    "Electronic Signature", 
                    value=rp.get("cryptElectronicSignature", False), 
                    key=f"rp_sig_{idx}_v{data_version}"
                )
                st.session_state.responsible_persons[idx]["cryptElectronicSignature"] = signature
                
                timestamp = st.checkbox(
                    "Electronic TimeStamp", 
                    value=rp.get("cryptElectronicTimeStamp", False), 
                    key=f"rp_ts_{idx}_v{data_version}"
                )
                st.session_state.responsible_persons[idx]["cryptElectronicTimeStamp"] = timestamp

            if len(st.session_state.responsible_persons) > 1:
                if st.button(f"🗑️ Remove Person {idx+1}", key=f"remove_rp_{idx}_v{data_version}"):
                    st.session_state.responsible_persons.pop(idx)
                    st.session_state.data_version += 1
                    st.rerun()

            st.markdown("---")

        if st.button("➕ Add Responsible Person", key=f"add_rp_v{data_version}"):
            st.session_state.responsible_persons.append(DEFAULT_PERSON.copy())
            st.session_state.data_version += 1
            st.rerun()