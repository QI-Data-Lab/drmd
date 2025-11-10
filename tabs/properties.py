# tabs/properties.py
import streamlit as st
import pandas as pd
from utils import INIT_ID, create_empty_result, qudt_quantities

def render_properties():
    # Loop over the two fixed materialProperties sets.
    for mp in st.session_state.materialProperties:
        mp_uuid = mp.get("uuid")

        # Use the set's name in the expander title
        with st.expander(mp.get("name"), expanded=True):
            # Main Material Properties data
            col1, col2 = st.columns(2)
            with col1:
                mp["id"] = st.text_input("ID (optional)", value=mp.get("id", ""), key=f"mp_id_{mp_uuid}")
                st.text_input("Name", value=mp.get("displayName", ""), key=f"mp_name_{mp_uuid}", disabled=True)
            with col2:
                mp["description"] = st.text_area("Description", value=mp.get("description", ""),
                                                 key=f"mp_desc_{mp_uuid}")
                mp["procedures"] = st.text_area("Procedures", value=mp.get("procedures", ""), key=f"mp_proc_{mp_uuid}")

            st.markdown("---")

            # For each measurement result table
            for res_idx, result in enumerate(mp.get("results", [])):
                st.markdown(f"##### Table {res_idx + 1}")
                
                # Remove table button outside of form
                col_name, col_remove = st.columns([4, 1])
                with col_remove:
                    if st.button("Remove Table", key=f"remove_res_{mp_uuid}_{res_idx}"):
                        mp["results"].pop(res_idx)
                        st.rerun()

                # Use form for smooth operation
                with st.form(key=f"res_form_{mp_uuid}_{res_idx}"):
                    result["result_name"] = st.text_input("Name", value=result.get("result_name", ""), key=f"res_name_{mp_uuid}_{res_idx}")
                    result["description"] = st.text_area("Description", value=result.get("description", ""), key=f"res_desc_{mp_uuid}_{res_idx}")
                    
                    # Initialize identifiers if not present
                    if "identifiers" not in result:
                        result["identifiers"] = [ [] for _ in range(len(result.get("quantities", pd.DataFrame()))) ]
                    
                    # Smooth data editor without D-SI units
                    result["quantities"] = st.data_editor(
                        result.get("quantities", pd.DataFrame(columns=[
                            "Name", "Label", "Identifier Scheme", "Identifier Value", "Identifier Link",
                            "Value", "Quantity Kind", "Unit",
                            "Uncertainty", "Coverage Factor", "Coverage Probability", "Distribution"
                        ])),
                        num_rows="dynamic",
                        disabled=["Identifier Scheme", "Identifier Value", "Identifier Link"],
                        key=f"quantities_{mp_uuid}_{res_idx}"
                    )
                    
                    # Form submit button
                    submitted = st.form_submit_button("Update Table")
                    if submitted:
                        # Update identifiers list length to match quantities
                        quantities_len = len(result["quantities"])
                        while len(result["identifiers"]) < quantities_len:
                            result["identifiers"].append([])
                        while len(result["identifiers"]) > quantities_len:
                            result["identifiers"].pop()

                # Identifiers editing section (outside form for immediate feedback)
                qlen = len(result.get("quantities", pd.DataFrame()))
                if qlen > 0:
                    st.markdown("###### Edit Identifiers for a Row")
                    sel = st.number_input("Select Row #", min_value=1, max_value=qlen, step=1,
                                          key=f"row_sel_{mp_uuid}_{res_idx}")
                    row_index = sel - 1  # Adjust for 0-based index

                    # Ensure identifiers list has enough empty lists for new rows
                    while len(result["identifiers"]) < qlen:
                        result["identifiers"].append([])

                    current_ids = result["identifiers"][row_index]
                    for pid_idx, pid in enumerate(current_ids):
                        cols_id = st.columns([2, 3, 4, 1])
                        pid["scheme"] = cols_id[0].text_input("Scheme", pid.get("scheme", ""),
                                                              key=f"prop_scheme_{mp_uuid}_{res_idx}_{row_index}_{pid_idx}")
                        pid["value"] = cols_id[1].text_input("Value", pid.get("value", ""),
                                                             key=f"prop_value_{mp_uuid}_{res_idx}_{row_index}_{pid_idx}")
                        pid["link"] = cols_id[2].text_input("Link", pid.get("link", ""),
                                                            key=f"prop_link_{mp_uuid}_{res_idx}_{row_index}_{pid_idx}")
                        if cols_id[3].button("🗑️", key=f"del_prop_id_{mp_uuid}_{res_idx}_{row_index}_{pid_idx}"):
                            current_ids.pop(pid_idx)
                            st.rerun()

                    if st.button("Add Identifier for this Row", key=f"add_prop_id_{mp_uuid}_{res_idx}_{row_index}"):
                        current_ids.append(INIT_ID.copy())
                        st.rerun()

                    # Update the main identifiers list and the flattened columns in the dataframe
                    result["identifiers"][row_index] = current_ids
                    # Update flattened columns in dataframe
                    if not result["quantities"].empty and len(result["quantities"]) > row_index:
                        if current_ids:
                            result["quantities"].loc[row_index, "Identifier Scheme"] = current_ids[0].get("scheme", "")
                            result["quantities"].loc[row_index, "Identifier Value"] = current_ids[0].get("value", "")
                            result["quantities"].loc[row_index, "Identifier Link"] = current_ids[0].get("link", "")
                        else:
                            result["quantities"].loc[row_index, ["Identifier Scheme", "Identifier Value", "Identifier Link"]] = ""

                st.markdown("---")
                st.markdown("**Default Uncertainty Values:**")
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    local_coverage_factor = st.number_input("Coverage Factor", min_value=1.0, max_value=10.0, value=2.0,
                                                            step=0.1, key=f"local_cf_{mp_uuid}_{res_idx}")
                with col2:
                    local_coverage_probability = st.number_input("Probability", min_value=0.0, max_value=1.0,
                                                                 value=0.95, step=0.01,
                                                                 key=f"local_cp_{mp_uuid}_{res_idx}")
                with col3:
                    local_distribution = st.selectbox("Distribution", ["normal", "log-normal", "uniform"], index=0,
                                                      key=f"local_dist_{mp_uuid}_{res_idx}")

                if st.button("Apply Defaults to All Rows", key=f"apply_defaults_{mp_uuid}_{res_idx}"):
                    if not result["quantities"].empty:
                        result["quantities"]["Coverage Factor"] = local_coverage_factor
                        result["quantities"]["Coverage Probability"] = local_coverage_probability
                        result["quantities"]["Distribution"] = local_distribution
                    st.rerun()

                st.markdown("---")

            if st.button("Add Table", key=f"add_result_{mp_uuid}"):
                mp.setdefault("results", []).append(create_empty_result())
                st.rerun()


    # with col_right:
    #     # Commented out quantity selection and QUDT selection
    #     # st.markdown("Quantity Selection", help="This panel shows available quantity types and their units from the QUDT ontology. Select a quantity to see applicable units.",)
    #     # st.session_state.selected_quantity = st.selectbox("Type", list(qudt_quantities.keys()) + ["Custom"], key="quantity_select")
    #     # st.session_state.selected_unit = st.selectbox("Unit", qudt_quantities.get(st.session_state.selected_quantity, ["Custom"]), key="unit_select")
    #     # st.markdown("---")

    #     # Removed uncertainty fields from right column - now they are under each table
    #     #st.write("Properties configuration panel")