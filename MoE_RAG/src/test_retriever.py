import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "../faiss_index/faiss_index_ivfpq.index"
MAPPING_PATH = "../faiss_index/vector_id_to_chunk_id.pkl"

# Load FAISS index
index = faiss.read_index(INDEX_PATH)

# Load chunk_id mapping
with open(MAPPING_PATH, "rb") as f:
    chunk_ids = pickle.load(f)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Example query
query = "Regulations for higher education institutions"
query_emb = model.encode([query]).astype("float32")

# Search top 5
k = 5
D, I = index.search(query_emb, k)
print("Top chunks:")
for rank, idx in enumerate(I[0]):
    print(f"{rank+1}. chunk_id: {chunk_ids[idx]}, distance: {D[0][rank]}")
