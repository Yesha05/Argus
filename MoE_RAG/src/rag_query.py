import os
import psycopg2
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# ---------------- CONFIG ----------------
DB_HOST = "localhost"
DB_NAME = "moe_rag_db"
DB_USER = "rag_user"
DB_PASSWORD = "YourStrongPassword123"

INDEX_PATH = "../faiss_index/faiss_index_ivfpq.index"
MAPPING_PATH = "../faiss_index/vector_id_to_chunk_id.pkl"

TOP_K = 5  # number of chunks to retrieve
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"  # Use gated model path

DEVICE = "cpu"  # CPU safe
OFFLOAD_FOLDER = "./offload"  # Folder for offloading weights
MAX_NEW_TOKENS = 150  # Reduce tokens to avoid CPU overflow
TOP_K_GEN = 50
TOP_P_GEN = 0.95

# Allow multiple OpenMP runtimes to avoid libomp error
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ---------------- LOAD FAISS & MAPPING ----------------
index = faiss.read_index(INDEX_PATH)
with open(MAPPING_PATH, "rb") as f:
    chunk_ids = pickle.load(f)

# ---------------- LOAD EMBEDDING MODEL ----------------
embed_model = SentenceTransformer(EMBEDDING_MODEL)

# ---------------- CONNECT TO POSTGRESQL ----------------
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# ---------------- LOAD LLM ----------------
print("Loading LLM...")
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL,
    device_map={"": "cpu"},      # Everything on CPU
    offload_folder=OFFLOAD_FOLDER, 
    torch_dtype=torch.float32,   # safer on CPU
    low_cpu_mem_usage=True
)
print("LLM loaded!")

# ---------------- RETRIEVE CHUNKS ----------------
def retrieve_chunks(query, top_k=TOP_K):
    query_emb = embed_model.encode([query]).astype("float32")
    D, I = index.search(query_emb, top_k)
    results = []
    for dist, idx in zip(D[0], I[0]):
        chunk_id = chunk_ids[idx]
        cursor.execute("SELECT chunk_text, doc_id, page_number FROM chunks WHERE id=%s", (chunk_id,))
        row = cursor.fetchone()
        if row:
            text, doc_id, page_number = row
            confidence = max(0.0, 1 - dist)  # simple normalization
            results.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "page": page_number,
                "text": text,
                "confidence": confidence
            })
    return results

# ---------------- BUILD PROMPT ----------------
def build_prompt(query, chunks):
    context = ""
    for c in chunks:
        context += f"[{c['doc_id']} | {c['page']}] {c['text']}\n"
    prompt = f"""SYSTEM: You are an assistant for MoE. Use only the provided context. Cite sources as [doc_id | page]. Include a confidence score (0–1) for each answer.
USER QUERY: {query}
CONTEXT:
{context}
"""
    return prompt

# ---------------- GENERATE ANSWER ----------------
def generate_answer(query):
    chunks = retrieve_chunks(query)
    prompt = build_prompt(query, chunks)

    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    outputs = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=True,
        top_k=TOP_K_GEN,
        top_p=TOP_P_GEN,
        pad_token_id=tokenizer.eos_token_id
    )
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer, chunks

# ---------------- TEST RUN ----------------
if __name__ == "__main__":
    user_query = input("Enter your query: ")
    answer, chunks = generate_answer(user_query)
    print("\n✅ Answer:\n", answer)
    print("\n📄 Sources & Confidence:")
    for c in chunks:
        print(f"Doc: {c['doc_id']} | Page: {c['page']} | Confidence: {c['confidence']:.2f}")
