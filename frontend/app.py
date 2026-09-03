import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Meridian Homes RAG Dashboard", layout="wide")

st.sidebar.title("📄 RAG Dashboard")
page = st.sidebar.radio("Navigate", ["Home", "Documents", "Chatbot"])


def get_stats():
    try:
        r = requests.get(f"{API_URL}/stats", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Could not reach backend: {e}")
        return None


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────
if page == "Home":
    st.title("Dashboard Overview")
    stats = get_stats()

    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Documents", stats["total_documents"])
        col2.metric("Processed", stats["processed"])
        col3.metric("Processing", stats["processing"])
        col4.metric("Failed", stats["failed"])
        col5.metric("Indexed Chunks", stats["total_indexed_chunks"])

        st.metric("Total Chats", stats["total_chats"])


# ─────────────────────────────────────────────
# DOCUMENTS PAGE
# ─────────────────────────────────────────────
elif page == "Documents":
    st.title("Document Management")

    st.subheader("Upload a Document")
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        if st.button("Upload & Process"):
            with st.spinner("Uploading and processing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    r = requests.post(f"{API_URL}/documents/upload", files=files, timeout=60)
                    if r.status_code == 200:
                        result = r.json()
                        st.success(f"Processed '{result['filename']}' — {result['chunks']} chunks indexed.")
                    else:
                        st.error(f"Upload failed: {r.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    st.divider()
    st.subheader("Your Documents")

    try:
        r = requests.get(f"{API_URL}/documents", timeout=5)
        docs = r.json()
    except Exception as e:
        st.error(f"Could not load documents: {e}")
        docs = []

    if not docs:
        st.info("No documents uploaded yet.")
    else:
        for doc in docs:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])

                with col1:
                    st.write(f"**{doc['filename']}**")
                    st.caption(f"Uploaded: {doc['uploaded_at'][:19]}")

                with col2:
                    status = doc["status"]
                    if status == "processed":
                        st.success(f"✅ {status} ({doc['chunk_count']} chunks)")
                    elif status == "processing":
                        st.warning(f"⏳ {status}")
                    else:
                        st.error(f"❌ {status}")
                        if doc.get("error"):
                            st.caption(doc["error"])

                with col3:
                    if st.button("Reprocess", key=f"reprocess_{doc['doc_id']}"):
                        with st.spinner("Reprocessing..."):
                            resp = requests.post(f"{API_URL}/documents/{doc['doc_id']}/reprocess", timeout=60)
                            if resp.status_code == 200:
                                st.success("Reprocessed!")
                                st.rerun()
                            else:
                                st.error("Reprocess failed")

                with col4:
                    if st.button("Delete", key=f"delete_{doc['doc_id']}"):
                        resp = requests.delete(f"{API_URL}/documents/{doc['doc_id']}", timeout=30)
                        if resp.status_code == 200:
                            st.success("Deleted")
                            st.rerun()
                        else:
                            st.error("Delete failed")


# ─────────────────────────────────────────────
# CHATBOT PAGE
# ─────────────────────────────────────────────
elif page == "Chatbot":
    st.title("Chat with Your Documents")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.button("🗑️ New Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # Render past messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.caption(f"📄 {src['doc_name']} — Page {src['page']}")

    # Chat input
    user_question = st.chat_input("Ask a question about your documents...")

    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Increased timeout — Gemini calls can occasionally take 60s+
                    r = requests.post(f"{API_URL}/chat", json={"question": user_question}, timeout=90)
                    if r.status_code == 200:
                        result = r.json()
                        st.write(result["answer"])
                        if result["sources"]:
                            with st.expander("Sources"):
                                for src in result["sources"]:
                                    st.caption(f"📄 {src['doc_name']} — Page {src['page']}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result["sources"],
                        })
                    else:
                        error_msg = f"Error: {r.json().get('detail', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg, "sources": []})
                except requests.exceptions.Timeout:
                    error_msg = "The request took too long to respond. Please try again."
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg, "sources": []})
                except Exception as e:
                    error_msg = f"Could not reach backend: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg, "sources": []})