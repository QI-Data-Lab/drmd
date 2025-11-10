# tabs/materials.py
import streamlit as st
import uuid
from utils import INIT_ID

def render_materials():
    # same content as rev2 for Materials
    for i, mat in enumerate(st.session_state.materials):
        with st.expander(f"Material {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                mat["name"] = st.text_input("Material Name", mat["name"], key=f"mat_name_{mat['uuid']}")
                mat["materialClass"] = st.text_input("Material Class", mat["materialClass"], key=f"mat_class_{mat['uuid']}")
                mat["itemQuantities"] = st.text_input("Item Quantities", mat["itemQuantities"], key=f"mat_iq_{mat['uuid']}")
            with c2:
                mat["description"] = st.text_area("Description", mat["description"], key=f"mat_desc_{mat['uuid']}")
                mat["minimumSampleSize"] = st.text_input("Minimum Sample Size", mat["minimumSampleSize"], key=f"mat_min_{mat['uuid']}",help="Enter value with unit (e.g., '4.9 g'")
                mat["isCertified"] = st.checkbox("Certified", mat["isCertified"], key=f"mat_cert_{mat['uuid']}")

            st.markdown("#### Material Identifiers")
            if not mat.get("materialIdentifiers"):
                mat["materialIdentifiers"] = [INIT_ID.copy()]
            for midx, mid in enumerate(mat["materialIdentifiers"]):
                cols_id = st.columns([2,3,4,1])
                mid["scheme"] = cols_id[0].text_input("Scheme", mid.get("scheme", ""), key=f"mat_scheme_{mat['uuid']}_{midx}")
                mid["value"] = cols_id[1].text_input("Value", mid.get("value", ""), key=f"mat_value_{mat['uuid']}_{midx}")
                mid["link"] = cols_id[2].text_input("Link", mid.get("link", ""), key=f"mat_link_{mat['uuid']}_{midx}")
                if cols_id[3].button("🗑️", key=f"del_mat_id_{mat['uuid']}_{midx}") and len(mat["materialIdentifiers"])>1:
                    mat["materialIdentifiers"].pop(midx); st.rerun()
            if st.button("➕ Add Identifier", key=f"add_mat_id_{mat['uuid']}"):
                mat["materialIdentifiers"].append(INIT_ID.copy()); st.rerun()

            if st.button("Remove Material", key=f"rm_mat_{mat['uuid']}", disabled=len(st.session_state.materials)==1):
                st.session_state.materials.pop(i); st.rerun()

    if st.button("➕ Add Material", key="add_material"):
        st.session_state.materials.append({
            "uuid": str(uuid.uuid4()), "name": "", "description": "", "materialClass": "",
            "minimumSampleSize": "", "itemQuantities": "", "isCertified": False,
            "materialIdentifiers": [INIT_ID.copy()],
        }); st.rerun()