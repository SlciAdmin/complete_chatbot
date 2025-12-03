# prepare_data.py

import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Load your scraped data
with open("slci_clean_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Combine content into one list of texts
documents = []
for item in data:
    documents.append(f"{item['title']}\nURL: {item['url']}\n\n{item['content']}")

# Split into chunks (for better context retrieval)
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = splitter.create_documents(documents)

# Create embeddings (you can swap model to 'sentence-transformers/all-MiniLM-L6-v2' for speed)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Build FAISS index
vectorstore = FAISS.from_documents(docs, embeddings)

# Save locally
vectorstore.save_local("index")

print("✅ Data prepared and FAISS index saved successfully!")
