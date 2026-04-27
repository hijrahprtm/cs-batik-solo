import pandas as pd
import chromadb
import os
import shutil

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "db_nusantara")

if os.path.exists(db_path):
    shutil.rmtree(db_path)

client = chromadb.PersistentClient(path=db_path)
collection = client.create_collection(name="koleksi_cs")

# Data Knowledge Base CS (Contoh Toko Online/Layanan)
data_cs = {
    'pertanyaan': [
        'jam buka', 'lokasi toko', 'cara pesen', 'ongkir', 'pembayaran', 
        'produk', 'garansi', 'salam', 'matur nuwun'
    ],
    'jawaban': [
        'Toko buka saben dinten jam 08.00 enjing ngantos jam 21.00 dalu.',
        'Alamatipun wonten ing Jalan Slamet Riyadi No. 10, Solo.',
        'Cara pesen saget lewat WA utawi langsung klik tombol keranjang.',
        'Ongkir gratis kanggo wilayah kuto Solo lan sekitare.',
        'Saget bayar lewat transfer bank utawi COD (bayar ing nggon).',
        'Kula sade batik tulis asli lan kaos khas Solo.',
        'Garansi barang wangsul yen wonten cacat (suwek utawi luntur).',
        'Sugeng enjing/siang/sonten, wonten ingkang saget dipun bantu?',
        'Sami-sami, mugi-mugi berkah.'
    ]
}

df = pd.DataFrame(data_cs)
list_tanya = df['pertanyaan'].tolist()
list_jawab = df['jawaban'].tolist()

collection.add(
    documents=list_tanya,
    metadatas=[{"info": j} for j in list_jawab],
    ids=[f"cs_{i}" for i in range(len(list_tanya))]
)

print(f"✅ Database CS Siap! {len(list_tanya)} poin layanan masuk.")