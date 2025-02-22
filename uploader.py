from pinecone import Pinecone, ServerlessSpec
import os
import json

TOKEN = ""
with open("secrets.txt", "r") as f:
    TOKEN = f.read()

HOST = ""
with open("host.txt", "r") as f:
    HOST = f.read()

pc = Pinecone(api_key=TOKEN)
index_name = "quickstart2"

index = pc.Index(host=HOST)

# Load documents from sample folder
docs = []
for filename in os.listdir('sample'):
    if filename.endswith('.json'):
        with open(os.path.join('sample', filename), 'r') as f:
            doc = json.load(f)
            docs.append(doc)

# Embed documents into Pinecone index
for i, doc in enumerate(docs):
    index.upsert_records(
        records=[
            {
                "id": f"doc_{i}", 
                "text": str(doc), 
                # can also add:
                # "category": <cat>,
            }
        ], 
        namespace='records'
    )
    print(f"upserted {i}")

