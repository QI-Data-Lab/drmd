# tabs/statements.py
import streamlit as st

def render_statements():
    # Official Statements (using dcc:richContentType structure)
    with st.expander("ISO 17034 Statements", expanded=True):

        # Intended Use
        content_val = st.text_area("Intended Use", value=st.session_state.official_statements.get("intendedUse", {}).get("content", ""), key="official_content_intendedUse")
        st.session_state.official_statements["intendedUse"] = {"name": "Intended Use", "content": content_val}

        # Commutability
        content_val = st.text_area("Commutability", value=st.session_state.official_statements.get("commutability", {}).get("content", ""), key="official_content_commutability")
        st.session_state.official_statements["commutability"] = {"name": "Commutability", "content": content_val}

        # Storage Information
        content_val = st.text_area("Storage Information", value=st.session_state.official_statements.get("storageInformation", {}).get("content", ""), key="official_content_storageInformation")
        st.session_state.official_statements["storageInformation"] = {"name": "Storage Information", "content": content_val}

        # Instructions For Handling And Use
        content_val = st.text_area("Instructions For Handling And Use", value=st.session_state.official_statements.get("instructionsForHandlingAndUse", {}).get("content", ""), key="official_content_instructionsForHandlingAndUse")
        st.session_state.official_statements["instructionsForHandlingAndUse"] = {"name": "Instructions For Handling And Use", "content": content_val}

        # Metrological Traceability
        content_val = st.text_area("Metrological Traceability", value=st.session_state.official_statements.get("metrologicalTraceability", {}).get("content", ""), key="official_content_metrologicalTraceability")
        st.session_state.official_statements["metrologicalTraceability"] = {"name": "Metrological Traceability", "content": content_val}

        # Health And Safety Information
        content_val = st.text_area("Health And Safety Information", value=st.session_state.official_statements.get("healthAndSafetyInformation", {}).get("content", ""), key="official_content_healthAndSafetyInformation")
        st.session_state.official_statements["healthAndSafetyInformation"] = {"name": "Health And Safety Information", "content": content_val}

        # Subcontractors
        content_val = st.text_area("Subcontractors", value=st.session_state.official_statements.get("subcontractors", {}).get("content", ""), key="official_content_subcontractors")
        st.session_state.official_statements["subcontractors"] = {"name": "Subcontractors", "content": content_val}

        # Legal Notice
        content_val = st.text_area("Legal Notice", value=st.session_state.official_statements.get("legalNotice", {}).get("content", ""), key="official_content_legalNotice")
        st.session_state.official_statements["legalNotice"] = {"name": "Legal Notice", "content": content_val}

        # Reference To Certification Report
        content_val = st.text_area("Reference To Certification Report", value=st.session_state.official_statements.get("referenceToCertificationReport", {}).get("content", ""), key="official_content_referenceToCertificationReport")
        st.session_state.official_statements["referenceToCertificationReport"] = {"name": "Reference To Certification Report", "content": content_val}

    # Custom Statements (all exported as <drmd:statement>)
    with st.expander("Other Statements", expanded=True):
        for idx, cs in enumerate(st.session_state.custom_statements):
            with st.container():
                # We ignore any custom tag; the export will use <drmd:statement>
                cs_name = st.text_input(f" Statement {idx+1} - Name", value=cs.get("name", "").strip(), key=f"cs_name_{idx}")
                cs_content = st.text_area(f" Statement {idx+1} - Content", value=cs.get("content", "").strip(), key=f"cs_content_{idx}")
                st.session_state.custom_statements[idx] = {"name": cs_name, "content": cs_content}
                if st.button(f"Remove", key=f"remove_cs_{idx}"):
                    st.session_state.custom_statements.pop(idx)
                    st.rerun()
        if st.button("Add Statement", key="add_cs"):
            st.session_state.custom_statements.append({"name": "", "content": ""})
            st.rerun()