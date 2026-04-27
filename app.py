import os
# Fix untuk Protobuf dan SQLite di server Linux (Wajib di baris paling atas)
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import chromadb
from groq import Groq

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="CS Batik Solo AI", page_icon="🛍️")
st.title("🛍️ CS Batik Solo - AI Assistant")

# --- LOAD API KEY DARI SECRETS ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Mangga setting GROQ_API_KEY wonten ing Secrets Streamlit rumiyin.")
    st.stop()

client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- LOAD DATABASE ---
db_path = os.path.join(os.getcwd(), "db_nusantara")

@st.cache_resource
def load_db():
    if not os.path.exists(db_path):
        st.error(f"Folder database mboten kepanggih wonten ing: {db_path}")
        return None
    
    # Koneksi ke ChromaDB
    client_chroma = chromadb.PersistentClient(path=db_path)
    
    try:
        # OTOMATIS cari nama koleksi yang ada (biar nggak error salah nama)
        existing_collections = client_chroma.list_collections()
        if existing_collections:
            # Pakai koleksi pertama yang ditemukan
            return client_chroma.get_collection(name=existing_collections[0].name)
        else:
            # Kalau beneran kosong, buat baru biar aplikasi nggak mati
            return client_chroma.get_or_create_collection(name="koleksi_cs")
    except Exception as e:
        st.error(f"Error nalika mundhut data: {e}")
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
    if collection:
        results = collection.query(query_texts=[prompt], n_results=2)
        context = " ".join([res for res in results['documents'][0]])
    else:
        context = "Mboten wonten data referensi."

    # Kirim ke Groq AI
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        prompt_system = f"""
        Sampeyan minangka Customer Service Toko Batik Solo ingkang sopan banget.
        Gunakake Basa Jawa krama alus (utawa ngoko yen pantes).
        Referensi data toko: {context}
        Jawab kanthi ringkes lan mbantu.
        """
        
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
