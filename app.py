import streamlit as st
import os

# TRICK UNTUK CHROMADB DI STREAMLIT CLOUD
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
from groq import Groq

# 1. KONFIGURASI
st.set_page_config(page_title="CS Monggo Pinarak", page_icon="📞")

# AMBIL API KEY DARI SETTINGS -> SECRETS DI STREAMLIT
# Daftar di console.groq.com (Gratis)
if "GROQ_API_KEY" not in st.secrets:
    st.error("Mangga setting GROQ_API_KEY wonten ing Secrets Streamlit rumiyin.")
    st.stop()

client_groq = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 2. INISIALISASI DB
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "db_nusantara")

@st.cache_resource
def load_db():
    if not os.path.exists(db_path):
        return None
    client = chromadb.PersistentClient(path=db_path)
    return client.get_collection(name="koleksi_cs")

collection = load_db()

# 3. SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. KEYWORD JAWABAN PASTI
keywords = {
    "rekening": "Nomer rekeningipun kagem transfer inggih punika BCA 1234567890 atas nama Monggo Pinarak.",
    "nomer": "Nomer rekeningipun kagem transfer inggih punika BCA 1234567890.",
    "stok": "Stok batik Parang kantun 5 lembar, Mega Mendung kantun 12. Menawi kaos Wayang taksih kathah.",
    "jam": "Toko Monggo Pinarak buka saben dinten jam 08.00 enjing ngantos jam 21.00 dalu.",
    "alamat": "Alamatipun wonten ing Jalan Slamet Riyadi No. 10, Solo.",
    "perusahaan": "Toko Monggo Pinarak punika toko batik tulis asli lan kaos khas Solo."
}

# 5. LOGIC CHAT
if prompt := st.chat_input("Wonten ingkang saged kula bantu?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    prompt_lower = prompt.lower()
    final_response = ""

    # Cek Keywords
    for k, v in keywords.items():
        if k in prompt_lower:
            final_response = f"Sugeng siang, Panjenengan. {v}"
            break

    # Cek Vector DB
    if not final_response and collection:
        results = collection.query(query_texts=[prompt_lower], n_results=1)
        if results['distances'][0][0] < 0.50:
            final_response = f"Sugeng siang. {results['metadatas'][0][0]['info']}"

    # Tanya Groq (Llama 3) jika tidak ada data
    if not final_response:
        with st.chat_message("assistant"):
            with st.spinner("Nembe ngetik..."):
                try:
                    chat_completion = client_groq.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "Sampeyan CS Toko Batik Monggo Pinarak Solo. Jawab nganggo Basa Jawa Krama Alus sing cekak lan sopan. Gunakake 'Panjenengan'."},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-8b-8192",
                        temperature=0.1,
                    )
                    final_response = chat_completion.choices[0].message.content
                except:
                    final_response = "Nyuwun sewu, sistem nembe gangguan."

    # Filter Kowe
    final_response = final_response.replace("Kowe", "Panjenengan").replace("kowe", "Panjenengan")
    
    with st.chat_message("assistant"):
        st.markdown(final_response)
    st.session_state.messages.append({"role": "assistant", "content": final_response})