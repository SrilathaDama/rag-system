import streamlit as st
import requests

st.set_page_config(page_title="RAG Assistant", page_icon="🤖", layout="wide")

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🤖 RAG Assistant")
with col2:
    try:
        health_check = requests.get("http://127.0.0.1:8000/healthz", timeout=2)
        st.success("🟢 Online" if health_check.status_code == 200 else "🔴 Offline")
    except:
        st.error("🔴 Offline")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Settings sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    top_k = st.slider("Number of results", 1, 5, 3)
    mode = st.radio("Search mode", ["hybrid", "elser"], index=0)
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Chat display
if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message['content'])
            if message["role"] == "assistant" and message.get("citations"):
                with st.expander("📚 Sources"):
                    for i, citation in enumerate(message["citations"], 1):
                        st.markdown(f"**{i}. {citation.get('source_file', 'Unknown')}**")
                        st.markdown(f"> {citation.get('snippet', '')}")
                        if citation.get('link'):
                            st.markdown(f"[View Document]({citation['link']})")
else:
    st.info("👋 Welcome! Ask me anything about your documents.")

# Chat input
if question := st.chat_input("Ask a question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Add thinking placeholder
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Thinking...",
        "citations": []
    })
    
    st.rerun()

# Process API call if last message is "Thinking..."
if (st.session_state.messages and 
    st.session_state.messages[-1]["role"] == "assistant" and 
    st.session_state.messages[-1]["content"] == "Thinking..."):
    
    # Get the last user question
    user_question = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            user_question = msg["content"]
            break
    
    if user_question:
        try:
            resp = requests.post(
                "http://127.0.0.1:8000/query",
                json={"question": user_question, "top_k": top_k, "mode": mode},
                timeout=60,
            )
            data = resp.json()
            answer = data.get("answer", "No answer.")
            citations = data.get("citations", [])
        except Exception as e:
            answer = f"Error: {e}"
            citations = []
        
        # Replace thinking message with answer
        st.session_state.messages[-1] = {
            "role": "assistant", 
            "content": answer,
            "citations": citations
        }
        
        st.rerun()