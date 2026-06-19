# check_db2.py
import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")

collections = client.list_collections()
print(f"Коллекций в базе: {len(collections)}")

for col in collections:
    print(f"\n--- Коллекция: {col.name} ---")
    print(f"    Документов: {col.count()}")