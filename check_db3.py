# check_db3.py
import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")
collections = client.list_collections()
print(f"Total collections: {len(collections)}")
for col in collections:
    print(f"  - {col.name}: {col.count()} documents")