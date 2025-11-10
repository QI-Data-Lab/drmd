# tabs/administrative_data.py
import streamlit as st
import re
import random
from datetime import date
from utils import INIT_ID, ALLOWED_TITLES

def render_administrative_data():
    with st.expander("Basic Information", expanded=True):
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.selectbox(
                "Title of the Document",
                ALLOWED_TITLES,
                key="title_option",
                placeholder="Select a document type...",
                index=None,
                format_func=lambda x: re.sub(r'(?<!^)(?=[A-Z])', ' ', x).title(),
            )
        # Initialize persistent_id_value if it doesn't exist
        if "persistent_id_value" not in st.session_state:
            st.session_state.persistent_id_value = ""

        # Define the callback function to generate 16-digit code  
        def generate_16_digit_code():
            # Generate 4 groups of 4 digits separated by hyphens
            group1 = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            group2 = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            group3 = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            group4 = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    
            persistent_id = f"{group1}-{group2}-{group3}-{group4}"
            st.session_state.persistent_id_value = persistent_id
            # Also update the persistent_id key to sync with the text input
            st.session_state.persistent_id = persistent_id

        with col2:  
            # Use the text input with the persistent_id key
            persistent_id_input = st.text_input(
                "Persistent Document Identifier",
                value=st.session_state.persistent_id_value,
                key="persistent_id",
                help="A globally unique, permanent identifier (e.g. UUID).",
            )
            # Keep both session state variables in sync
            if st.session_state.persistent_id != st.session_state.persistent_id_value:
                st.session_state.persistent_id_value = st.session_state.persistent_id

        with col3:
            # Add some vertical spacing
            st.write("")
            # Create the button with the callback
            if st.button("Generate", key="pid_gen", on_click=generate_16_digit_code):
                # Force a rerun to update the display
                st.rerun()


        st.markdown("#### Document Identifiers")
        for didx, did in enumerate(st.session_state.documentIdentifiers):
            cols = st.columns([2, 3, 4, 1])
            did["scheme"] = cols[0].text_input("Scheme", did.get("scheme", ""), key=f"doc_scheme_{didx}")
            did["value"] = cols[1].text_input("Value", did.get("value", ""), key=f"doc_value_{didx}")
            did["link"] = cols[2].text_input("Link", did.get("link", ""), key=f"doc_link_{didx}")
            if cols[3].button("🗑️", key=f"del_doc_id_{didx}") and len(st.session_state.documentIdentifiers) > 1:
                st.session_state.documentIdentifiers.pop(didx); st.rerun()
        if st.button("➕ Add Identifier", key="add_doc_id"):
            st.session_state.documentIdentifiers.append(INIT_ID.copy()); st.rerun()

        # Period of Validity row with new help text
        cols = st.columns([3, 3, 3])
        with cols[0]:
            v_type = st.selectbox("Period of Validity", ["Until Revoked", "Time After Dispatch", "Specific Time"],
                                  key="validity_type")
        if v_type == "Time After Dispatch":
            # Create separate input boxes for years and months
            with cols[1]:
                sub_cols = st.columns(2)
                with sub_cols[0]:
                    years = st.number_input("Years", min_value=0, step=1, key="duration_y")
                with sub_cols[1]:
                    months = st.number_input("Months", min_value=0, max_value=11, step=1, key="duration_m")

            # Dynamically build and display the ISO 8601 string
            with cols[2]:
                iso_parts = []
                if years > 0:
                    iso_parts.append(f"{years}Y")
                if months > 0:
                    iso_parts.append(f"{months}M")

                # Only form the string if there is a duration entered
                iso_duration = f"P{''.join(iso_parts)}" if iso_parts else ""

                # Store the final, valid string for XML generation
                st.session_state.raw_validity_period = iso_duration

                st.write("ISO 8601 Format:")
                if iso_duration:
                    st.success(f"`{iso_duration}`")
                else:
                    # Display a placeholder if no duration is entered
                    st.info("`P`")

                st.date_input("Dispatch Date", key="date_of_issue", max_value=date.max)
        elif v_type == "Specific Time":
            with cols[1]:
                st.date_input("Date", key="specific_time")
            cols[2].markdown(" ")
        else:
            cols[1].markdown(" "); cols[2].markdown(" ")

     # Reference Material Producer and Responsible Persons section remains unchanged.
    with st.expander("Reference Material Producer and Responsible Persons", expanded=True):
        with st.container():
            for idx, prod in enumerate(st.session_state.producers):
                # Use a container with a header instead of an expander
                st.markdown(f"###### Reference Material Producer")
                with st.container():
                    # Name and contact info
                    col1, col2 = st.columns(2)
                    with col1:
                        prod["producerName"] = st.text_input("Name", value=prod.get("producerName", ""), key=f"producerName_{idx}")
                        prod["producerEmail"] = st.text_input("Email", value=prod.get("producerEmail", ""), key=f"producerEmail_{idx}")
                        prod["producerPhone"] = st.text_input("Phone", value=prod.get("producerPhone", ""), key=f"producerPhone_{idx}")

                    # Address info in a more compact layout
                    with col2:
                        addr_cols = st.columns([3, 1])
                        with addr_cols[0]:
                            prod["producerStreet"] = st.text_input("Street", value=prod.get("producerStreet", ""), key=f"producerStreet_{idx}")
                        with addr_cols[1]:
                            prod["producerStreetNo"] = st.text_input("No.", value=prod.get("producerStreetNo", ""), key=f"producerStreetNo_{idx}")

                        city_cols = st.columns([1, 2, 1])
                        with city_cols[0]:
                            prod["producerPostCode"] = st.text_input("Post Code", value=prod.get("producerPostCode", ""), key=f"producerPostCode_{idx}")
                        with city_cols[1]:
                            prod["producerCity"] = st.text_input("City", value=prod.get("producerCity", ""), key=f"producerCity_{idx}")
                        with city_cols[2]:
                            prod["producerCountryCode"] = st.text_input("Country", value=prod.get("producerCountryCode", ""), key=f"producerCountryCode_{idx}")
                        prod["producerFax"] = st.text_input("Fax", value=prod.get("producerFax", ""), key=f"producerFax_{idx}")

                    st.markdown("#### Organization Identifiers")
                    if not prod.get("organizationIdentifiers"):
                        prod["organizationIdentifiers"] = [INIT_ID.copy()]
                    for oid_idx, oid in enumerate(prod["organizationIdentifiers"]):
                        cols_id = st.columns([2,3,4,1])
                        oid["scheme"] = cols_id[0].text_input("Scheme", oid.get("scheme", ""), key=f"org_scheme_{idx}_{oid_idx}")
                        oid["value"] = cols_id[1].text_input("Value", oid.get("value", ""), key=f"org_value_{idx}_{oid_idx}")
                        oid["link"] = cols_id[2].text_input("Link", oid.get("link", ""), key=f"org_link_{idx}_{oid_idx}")
                        if cols_id[3].button("🗑️", key=f"del_org_{idx}_{oid_idx}") and len(prod["organizationIdentifiers"])>1:
                            prod["organizationIdentifiers"].pop(oid_idx); st.rerun()
                    if st.button("➕ Add Identifier", key=f"add_org_{idx}"):
                        prod["organizationIdentifiers"].append(INIT_ID.copy()); st.rerun()

                    # if st.button("Remove", key=f"remove_prod_{idx}"):
                    #     st.session_state.producers.pop(idx)
                    #     st.rerun()

                # Add a separator between producers

            # if st.button("Add Producer", key="add_prod"):
            #     st.session_state.producers.append({
            #         "producerName": "",
            #         "producerStreet": "",
            #         "producerStreetNo": "",
            #         "producerPostCode": "",
            #         "producerCity": "",
            #         "producerCountryCode": "",
            #         "producerPhone": "",
            #         "producerFax": "",
            #         "producerEmail": ""
            #     })
            #     st.rerun()
        st.markdown("---")

        with st.container():
            for idx, rp in enumerate(st.session_state.responsible_persons):
                # Use a container with a header instead of an expander
                st.markdown(f"###### Responsible Person {idx+1}")
                with st.container():
                    cols = st.columns([2, 2, 2])
                    with cols[0]:
                        rp["personName"] = st.text_input("Name", value=rp.get("personName", ""), key=f"rp_name_{idx}")
                        rp["role"] = st.text_input("Role", value=rp.get("role", ""), key=f"rp_role_{idx}")
                    with cols[1]:
                        rp["description"] = st.text_area("Description", value=rp.get("description", ""), height=100, key=f"rp_desc_{idx}")
                    with cols[2]:
                        rp["mainSigner"] = st.checkbox("Main Signer", value=rp.get("mainSigner", False), key=f"rp_mainSigner_{idx}")
                        rp["cryptElectronicSeal"] = st.checkbox("Electronic Seal", value=rp.get("cryptElectronicSeal", False), key=f"rp_cryptSeal_{idx}")
                        rp["cryptElectronicSignature"] = st.checkbox("Electronic Signature", value=rp.get("cryptElectronicSignature", False), key=f"rp_cryptSig_{idx}")
                        rp["cryptElectronicTimeStamp"] = st.checkbox("Electronic TimeStamp", value=rp.get("cryptElectronicTimeStamp", False), key=f"rp_cryptTS_{idx}")
                    if st.button(f"Remove", key=f"remove_rp_{idx}"):
                        st.session_state.responsible_persons.pop(idx)
                        st.rerun()

                # Add a separator between responsible persons
                st.markdown("---")
            if st.button("Add Responsible Person", key="add_rp"):
                st.session_state.responsible_persons.append({
                    "personName": "",
                    "description": "",
                    "role": "",
                    "mainSigner": False,
                    "cryptElectronicSeal": False,
                    "cryptElectronicSignature": False,
                    "cryptElectronicTimeStamp": False
                })
                st.rerun()