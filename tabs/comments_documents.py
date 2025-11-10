# tabs/comments_documents.py
import streamlit as st
import base64

def render_comments_documents():
    # Single Comment (instead of multiple separate comment elements)
    st.markdown("###### Comment")
    comment = st.text_area("Enter your comment", value=st.session_state.get("comment", ""), key="comment")

    # --- Document Upload ---
    st.markdown("###### Upload Document")
    # Allow only one file upload (no multiple files)
    attachment = st.file_uploader("Attach Document", type=["pdf", "doc", "docx", "txt"], key="attachment")

    # Display currently loaded embedded document (if any)
    if st.session_state.get("embedded_files"):
        st.subheader("Existing Document from XML")
        # Only display the first one.
        file = st.session_state.embedded_files[0]
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.markdown(f"📄 **{file['name']}**")
        col1.text(f"Type: {file['mimeType']}")
        col2.download_button(
            label="Download",
            data=file["data"],
            file_name=file["name"],
            mime=file["mimeType"],
            key="download_embedded"
        )
        if col3.button("❌ Remove", key="remove_embedded"):
            st.session_state.embedded_files.pop(0)
            st.rerun()