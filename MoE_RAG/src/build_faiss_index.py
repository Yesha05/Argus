import psycopg2
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import pickle
import os

# ----- CONFIG -----
DB_HOST = "localhost"
DB_NAME = "moe_rag_db"
DB_USER = "rag_user"
DB_PASSWORD = "YourStrongPassword123"  # same as before

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension
INDEX_PATH = "../faiss_index/faiss_index_ivfpq.index"
MAPPING_PATH = "../faiss_index/vector_id_to_chunk_id.pkl"

# ----- CONNECT TO POSTGRESQL -----
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# ----- FETCH ALL CHUNKS -----
cursor.execute("SELECT id, chunk_text FROM chunks")
rows = cursor.fetchall()
print(f"✅ Fetched {len(rows)} chunks from PostgreSQL")

chunk_ids = [r[0] for r in rows]
texts = [r[1] for r in rows]

# ----- LOAD EMBEDDING MODEL -----
model = SentenceTransformer("all-MiniLM-L6-v2")

# ----- GENERATE EMBEDDINGS -----
print("⏳ Generating embeddings...")
embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
embeddings = np.array(embeddings).astype("float32")
print(f"✅ Embeddings shape: {embeddings.shape}")

# ----- BUILD FAISS IVF-PQ INDEX -----
nlist = int(np.sqrt(len(embeddings)))  # number of clusters
m = 16  # number of subquantizers
nbits = 8  # bits per subvector

quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
index = faiss.IndexIVFPQ(quantizer, EMBEDDING_DIM, nlist, m, nbits)

# Train the index
print("⏳ Training FAISS index...")
index.train(embeddings)

# Add embeddings
index.add(embeddings)
print(f"✅ Added {index.ntotal} vectors to FAISS index")

# ----- SAVE INDEX AND MAPPING -----
os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
faiss.write_index(index, INDEX_PATH)
with open(MAPPING_PATH, "wb") as f:
    pickle.dump(chunk_ids, f)
print(f"✅ FAISS index saved at: {INDEX_PATH}")
print(f"✅ Vector ID to chunk ID mapping saved at: {MAPPING_PATH}")

# ----- CLOSE POSTGRESQL -----
cursor.close()
conn.close()
