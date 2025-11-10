# tabs/statements.py - FINAL CLEAN VERSION
import streamlit as st

def render_statements():
    """Render the Statements tab with proper versioned widget binding."""
    
    # Get version counter for dynamic keys
    data_version = st.session_state.get("data_version", 0)
    
    # =============================================================================
    # Official ISO 17034 Statements
    # =============================================================================
    with st.expander("📋 ISO 17034 Statements", expanded=True):
        st.markdown("Standard statements required by ISO 17034 for reference material certificates.")
        st.markdown("---")
        
        # Intended Use
        intended_use = st.text_area(
            "Intended Use",
            value=st.session_state.official_statements.get("intendedUse", {}).get("content", ""),
            key=f"official_intendedUse_v{data_version}",
            height=100,
            help="Describe the intended purpose and applications of this reference material"
        )
        st.session_state.official_statements["intendedUse"] = {
            "name": "Intended Use",
            "content": intended_use
        }
        
        # Commutability
        commutability = st.text_area(
            "Commutability",
            value=st.session_state.official_statements.get("commutability", {}).get("content", ""),
            key=f"official_commutability_v{data_version}",
            height=100,
            help="Information about the commutability of the material"
        )
        st.session_state.official_statements["commutability"] = {
            "name": "Commutability",
            "content": commutability
        }
        
        # Storage Information
        storage_info = st.text_area(
            "Storage Information",
            value=st.session_state.official_statements.get("storageInformation", {}).get("content", ""),
            key=f"official_storageInformation_v{data_version}",
            height=100,
            help="Instructions for proper storage conditions (temperature, humidity, etc.)"
        )
        st.session_state.official_statements["storageInformation"] = {
            "name": "Storage Information",
            "content": storage_info
        }
        
        # Instructions For Handling And Use
        handling_instructions = st.text_area(
            "Instructions For Handling And Use",
            value=st.session_state.official_statements.get("instructionsForHandlingAndUse", {}).get("content", ""),
            key=f"official_instructionsForHandlingAndUse_v{data_version}",
            height=100,
            help="Detailed instructions for proper handling and usage"
        )
        st.session_state.official_statements["instructionsForHandlingAndUse"] = {
            "name": "Instructions For Handling And Use",
            "content": handling_instructions
        }
        
        # Metrological Traceability
        metrological_traceability = st.text_area(
            "Metrological Traceability",
            value=st.session_state.official_statements.get("metrologicalTraceability", {}).get("content", ""),
            key=f"official_metrologicalTraceability_v{data_version}",
            height=100,
            help="Information about traceability to SI units or other recognized standards"
        )
        st.session_state.official_statements["metrologicalTraceability"] = {
            "name": "Metrological Traceability",
            "content": metrological_traceability
        }
        
        # Health And Safety Information
        health_safety = st.text_area(
            "Health And Safety Information",
            value=st.session_state.official_statements.get("healthAndSafetyInformation", {}).get("content", ""),
            key=f"official_healthAndSafetyInformation_v{data_version}",
            height=100,
            help="Safety data, hazard warnings, and precautions"
        )
        st.session_state.official_statements["healthAndSafetyInformation"] = {
            "name": "Health And Safety Information",
            "content": health_safety
        }
        
        # Subcontractors
        subcontractors = st.text_area(
            "Subcontractors",
            value=st.session_state.official_statements.get("subcontractors", {}).get("content", ""),
            key=f"official_subcontractors_v{data_version}",
            height=100,
            help="Information about any subcontractors involved in production or testing"
        )
        st.session_state.official_statements["subcontractors"] = {
            "name": "Subcontractors",
            "content": subcontractors
        }
        
        # Legal Notice
        legal_notice = st.text_area(
            "Legal Notice",
            value=st.session_state.official_statements.get("legalNotice", {}).get("content", ""),
            key=f"official_legalNotice_v{data_version}",
            height=100,
            help="Legal disclaimers, terms of use, and liability limitations"
        )
        st.session_state.official_statements["legalNotice"] = {
            "name": "Legal Notice",
            "content": legal_notice
        }
        
        # Reference To Certification Report
        cert_report = st.text_area(
            "Reference To Certification Report",
            value=st.session_state.official_statements.get("referenceToCertificationReport", {}).get("content", ""),
            key=f"official_referenceToCertificationReport_v{data_version}",
            height=100,
            help="Reference to detailed certification or technical reports"
        )
        st.session_state.official_statements["referenceToCertificationReport"] = {
            "name": "Reference To Certification Report",
            "content": cert_report
        }

    # =============================================================================
    # Custom Statements (Other Statements)
    # =============================================================================
    with st.expander("📝 Other Statements", expanded=True):
        st.markdown("Add custom statements beyond the standard ISO 17034 requirements.")
        st.markdown("---")
        
        if len(st.session_state.custom_statements) == 0:
            st.info("ℹ️ No custom statements added yet. Click 'Add Statement' below to create one.")
        
        for idx, cs in enumerate(st.session_state.custom_statements):
            st.markdown(f"#### Statement {idx+1}")
            
            cols = st.columns([3, 1])
            
            with cols[0]:
                # Statement Name
                cs_name = st.text_input(
                    f"Statement {idx+1} - Name",
                    value=cs.get("name", "").strip(),
                    key=f"cs_name_{idx}_v{data_version}",
                    placeholder="e.g., Chemical Composition, Sample Preparation",
                    label_visibility="collapsed"
                )
                
                # Statement Content
                cs_content = st.text_area(
                    f"Statement {idx+1} - Content",
                    value=cs.get("content", "").strip(),
                    key=f"cs_content_{idx}_v{data_version}",
                    height=100,
                    label_visibility="collapsed",
                    placeholder="Enter the statement content here..."
                )
                
                # Update session state
                st.session_state.custom_statements[idx] = {
                    "name": cs_name,
                    "content": cs_content
                }
            
            with cols[1]:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                if st.button(
                    "🗑️ Remove",
                    key=f"remove_cs_{idx}_v{data_version}",
                    help=f"Remove statement {idx+1}"
                ):
                    st.session_state.custom_statements.pop(idx)
                    st.session_state.data_version += 1  # Increment version
                    st.rerun()
            
            st.markdown("---")
        
        # Add Statement Button
        if st.button(
            "➕ Add Statement",
            key=f"add_cs_v{data_version}",
            help="Add a new custom statement"
        ):
            st.session_state.custom_statements.append({
                "name": "",
                "content": ""
            })
            st.session_state.data_version += 1  # Increment version
            st.rerun()
