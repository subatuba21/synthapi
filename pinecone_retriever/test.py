from pinecone import Pinecone
import numpy as np

def search_by_text(query_text, index_name, top_k=10, namespace="", api_key="your_api_key"):
   pc = Pinecone(api_key=api_key)
   index = pc.Index(index_name)
   
   search_results = index.search_records(
       query={
          "inputs": {"text": query_text}, 
          "top_k": top_k
       },
       namespace=namespace
   )
   
   return search_results

query_vec = np.random.rand(384)

results = search_by_text(
#    query_vector=query_vec, 
   query_text="noodles",
   index_name="quickstart2",
   top_k=1,
   namespace="records",
   api_key="pcsk_5fjTMD_94yGbMH2Ujw2d3CEqfyvByLqeswYEP4LGLePfYQzfsiEKK1RoY2Z7UX9qnQ3sq3"
)

if results:
   for match in results.result.hits:
       print(f"ID: {match._id}")
       print(f"Score: {match._score}")
       print(f"Metadata: {match.metadata}\n")