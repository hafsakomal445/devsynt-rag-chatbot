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