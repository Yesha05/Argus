import os
import nltk
import psycopg2
from sentence_transformers import SentenceTransformer

# ----- CONFIG -----
DATA_DIR = "../data"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# PostgreSQL connection
DB_HOST = "localhost"
DB_NAME = "moe_rag_db"
DB_USER = "rag_user"
DB_PASSWORD = "YourStrongPassword123"  # use the password you set

# Download punkt tokenizer
nltk.download('punkt_tab', quiet=True)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# ----- FUNCTION: sentence-based chunking -----
def chunk_text_sentences(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
            current_chunk = overlap_text + " " + sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# ----- CONNECT TO POSTGRESQL -----
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# ----- INGEST & STORE CHUNKS -----
all_chunks = []
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".txt"):
        path = os.path.join(DATA_DIR, filename)
        # robust file reading
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                text = f.read()

        file_chunks = chunk_text_sentences(text)
        all_chunks.extend([(filename, i, c) for i, c in enumerate(file_chunks)])

        # insert into PostgreSQL
        for i, chunk_text in enumerate(file_chunks):
            cursor.execute(
                """
                INSERT INTO chunks (doc_id, chunk_id, chunk_text, start_pos, end_pos, page_number, file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (filename, i, chunk_text, 0, len(chunk_text), 0, path)
            )
        conn.commit()  # save after each file

print(f"✅ Total chunks created and stored: {len(all_chunks)}")

# ----- EXAMPLE: Generate embeddings for first 5 chunks -----
if all_chunks:
    embeddings = model.encode([c[2] for c in all_chunks[:5]])
    print(f"✅ Example embeddings shape: {embeddings.shape}")
else:
    print("⚠️ No text files found in data/")

# Close PostgreSQL connection
cursor.close()
conn.close()
