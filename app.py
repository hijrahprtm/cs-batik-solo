import streamlit as st
import chromadb
import ollama
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="CS Monggo Pinarak", page_icon="📞", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 12px; border: 1px solid #e0e0e0; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📞 CS Toko Monggo Pinarak")
st.caption("Layanan Pelanggan Otomatis - Basa Jawa Krama Alus (Final Stable)")
st.divider()

# 2. INISIALISASI DATABASE
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

# 4. DATA JAWABAN PASTI (KEYWORD ROUTING)
# Ditulis langsung dalam Krama Alus yang benar
keywords = {
    "rekening": "Nomer rekeningipun kagem transfer inggih punika BCA 1234567890 atas nama Monggo Pinarak. Matur nuwun.",
    "nomer": "Nomer rekeningipun kagem transfer inggih punika BCA 1234567890 atas nama Monggo Pinarak.",
    "bank": "Kita nampi transfer lewat BCA lan Mandiri, ugi saget COD (bayar ing nggon).",
    "stok": "Stok batik Parang kantun 5 lembar, Mega Mendung kantun 12. Menawi kaos Wayang taksih kathah.",
    "jne": "Saget kirim nganggo JNE, J&T, utawi GoSend kagem wilayah Solo.",
    "gosend": "Kagem wilayah Solo saget nganggo GoSend supados pesenan panjenengan dinten niki langsung dugi.",
    "jam": "Toko Monggo Pinarak buka saben dinten jam 08.00 enjing ngantos jam 21.00 dalu.",
    "buka": "Toko Monggo Pinarak buka saben dinten jam 08.00 enjing ngantos jam 21.00 dalu.",
    "tutup": "Toko tutupipun jam 21.00 dalu, Panjenengan.",
    "batik": "Kito sade macem-macem batik tulis asli, wonten Motif Parang, Mega Mendung, lan motif Solo kontemporer.",
    "perusahaan": "Toko Monggo Pinarak punika toko batik tulis asli lan kaos khas Solo ingkang nengenaken kualitas lan budoyo Jawi.",
    "apa": "Toko Monggo Pinarak punika toko batik tulis asli lan kaos khas Solo.",
    "ongkir": "Ongkir gratis kagem wilayah kuta Solo lan sekitare.",
    "alamat": "Alamatipun wonten ing Jalan Slamet Riyadi No. 10, Solo.",
    "lokasi": "Alamatipun wonten ing Jalan Slamet Riyadi No. 10, Solo."
}

# 5. LOGIC CHAT
if prompt := st.chat_input("Wonten ingkang saged kula bantu?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    prompt_lower = prompt.lower()
    final_response = ""

    # STRATEGI A: CEK KEYWORD (Prioritas Utama - Tanpa AI)
    for k, v in keywords.items():
        if k in prompt_lower:
            final_response = f"Sugeng siang, Panjenengan. {v}"
            break

    # STRATEGI B: CEK VECTOR DB (Jika keyword tidak kena)
    if not final_response and collection:
        results = collection.query(query_texts=[prompt_lower], n_results=1)
        if results['distances'][0][0] < 0.50:
            db_info = results['metadatas'][0][0]['info']
            final_response = f"Sugeng siang. {db_info}"

    # STRATEGI C: JIKA TIDAK ADA DATA (Tanya AI hanya untuk sapaan/basa-basi)
    if not final_response:
        with st.chat_message("assistant"):
            with st.spinner("Nembe ngetik..."):
                system_prompt = "Sampeyan CS Toko Batik Monggo Pinarak Solo. Jawab nganggo Basa Jawa Krama Alus sing cekak, sopan, lan gunakake tembung 'Panjenengan' (aja nganggo 'kowe'). Yen ora ngerti jawabane, aturana hubungi WA 08123456789."
                try:
                    response = ollama.generate(
                        model='llama3:8b', 
                        prompt=f"{system_prompt}\nUser: {prompt}\nCS:",
                        options={"temperature": 0.1}
                    )
                    final_response = response['response'].strip()
                except:
                    final_response = "Nyuwun sewu, sistem nembe gangguan. Mangga hubungi admin."

    # FILTER AKHIR (Double Safety)
    final_response = final_response.replace("Kowe", "Panjenengan").replace("kowe", "Panjenengan")
    
    # Tampilkan hasil
    if final_response:
        with st.chat_message("assistant"):
            st.markdown(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})

# Sidebar
with st.sidebar:
    st.header("Admin")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()