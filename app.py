import os
# --- FIX DATABASE & PROTOCOL ---
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import chromadb
from groq import Groq

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="CS Batik Solo AI", page_icon="🛍️")
st.title("🛍️ CS Batik Solo - AI Assistant")

# --- LOAD API KEY ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Mangga setting GROQ_API_KEY wonten ing Secrets Streamlit rumiyin.")
    st.stop()

client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- LOAD DATABASE (DENGAN PROTEKSI ERROR) ---
db_path = os.path.join(os.getcwd(), "db_nusantara")

@st.cache_resource
def load_db():
    if not os.path.exists(db_path):
        return None
    try:
        # Menggunakan konfigurasi dasar untuk menghindari error kolom
        client_chroma = chromadb.PersistentClient(path=db_path)
        colls = client_chroma.list_collections()
        if colls:
            # Ambil koleksi pertama yang tersedia
            return client_chroma.get_collection(name=colls[0].name)
    except Exception as e:
        # Jika database error (seperti masalah 'collections.topic'), kita biarkan None
        # Agar aplikasi tetap jalan meski tanpa database lokal
        return None
    return None

collection = load_db()

# --- LOGIKA CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan history chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input user
if prompt := st.chat_input("Wonten ingkang saged dipun bantu?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Cari referensi di database (RAG)
    context_data = ""
    if collection:
        try:
            results = collection.query(query_texts=[prompt], n_results=1)
            if results and results['documents'] and len(results['documents'][0]) > 0:
                context_data = results['documents'][0][0]
        except:
            context_data = "Info umum toko batik Solo."
    else:
        context_data = "Info umum toko batik Solo."

    # Kirim ke Groq AI
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # System Prompt yang lebih kuat
        prompt_system = f"""
        Sampeyan minangka Customer Service Toko Batik Solo ingkang sopan banget.
        Gunakake Basa Jawa krama alus.
        Yen ana pitakon alamat utawa stok, gunakake referensi iki: {context_data}
        Yen data ora ana, jawab nganggo kawruh umum babagan batik Solo kanthi sopan.
        """
        
        try:
            completion = client_groq.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": prompt_system},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Pangapunten, wonten gangguan teknis: {e}")
