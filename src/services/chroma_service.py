"""
ChromaDB service for vector storage and retrieval
"""
import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import uuid
import requests

class ChromaService:
 """ChromaDB service for vector operations"""
 
 def __init__(self):
 self.client = None
 self.embedding_model = None
 self.collections = {}
 self._initialize_chroma()
 self._initialize_embeddings()
 
 def _initialize_chroma(self):
 """Initialize ChromaDB client"""
 try:
 # Use persistent storage
 chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
 os.makedirs(chroma_db_path, exist_ok=True)
 
 self.client = chromadb.PersistentClient(
 path=chroma_db_path,
 settings=Settings(
 anonymized_telemetry=False,
 allow_reset=True
 )
 )
 print(f"SUCCESS: ChromaDB initialized at {chroma_db_path}")
 
 except Exception as e:
 print(f"ERROR: Failed to initialize ChromaDB: {e}")
 raise
 
 def _initialize_embeddings(self):
 """Initialize sentence transformer for embeddings"""
 try:
 # Use a lightweight model for fast embeddings
 model_name = "all-MiniLM-L6-v2" # 384 dimensions, fast and efficient
 
 # Set offline mode to avoid network issues
 import os
 os.environ["TRANSFORMERS_OFFLINE"] = "1"
 
 self.embedding_model = SentenceTransformer(model_name)
 print(f"SUCCESS: Embedding model loaded: {model_name}")
 
 except Exception as e:
 print(f"ERROR: Failed to load embedding model: {e}")
 print("Processing Trying to use cached model...")
 try:
 # Try to load from cache without network
 self.embedding_model = SentenceTransformer(model_name, cache_folder="./models")
 print(f"SUCCESS: Embedding model loaded from cache: {model_name}")
 except Exception as e2:
 print(f"ERROR: Failed to load from cache: {e2}")
 raise
 
 def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
 """Get existing collection or create new one"""
 if collection_name in self.collections:
 return self.collections[collection_name]
 
 try:
 # Try to get existing collection
 collection = self.client.get_collection(collection_name)
 print(f"Found Retrieved existing collection: {collection_name}")
 except:
 # Create new collection
 collection = self.client.create_collection(
 name=collection_name,
 metadata={"description": f"Legal documents collection: {collection_name}"}
 )
 print(f"Found Created new collection: {collection_name}")
 
 self.collections[collection_name] = collection
 return collection
 
 async def embed_documents(self, documents: List[Dict[str, Any]], 
 collection_name: str = "legal_docs") -> int:
 """Embed and store documents in ChromaDB"""
 if not documents:
 return 0
 
 try:
 collection = self.get_or_create_collection(collection_name)
 
 # Prepare data for embedding
 texts = []
 metadatas = []
 ids = []
 
 for i, doc in enumerate(documents):
 # Extract text content
 content = doc.get("content", "")
 if not content:
 continue
 
 # Create unique ID
 doc_id = doc.get("id", f"{collection_name}_{uuid.uuid4().hex[:8]}")
 
 # Prepare metadata
 metadata = {
 "title": doc.get("title", f"Document {i+1}")[:100],
 "source": doc.get("source", "unknown"),
 "dataset_type": doc.get("dataset_type", collection_name),
 "page": doc.get("page", 1),
 "content_length": len(content)
 }
 
 texts.append(content)
 metadatas.append(metadata)
 ids.append(doc_id)
 
 if not texts:
 return 0
 
 # Generate embeddings
 print(f"Processing Generating embeddings for {len(texts)} documents...")
 embeddings = self.embedding_model.encode(texts).tolist()
 
 # Store in ChromaDB
 collection.add(
 embeddings=embeddings,
 documents=texts,
 metadatas=metadatas,
 ids=ids
 )
 
 print(f"SUCCESS: Embedded {len(texts)} documents in collection '{collection_name}'")
 return len(texts)
 
 except Exception as e:
 print(f"ERROR: Failed to embed documents: {e}")
 return 0
 
 async def search_documents(self, query: str, collection_name: str = "legal_docs", 
 top_k: int = 5) -> List[Dict[str, Any]]:
 """Search for relevant documents"""
 try:
 collection = self.get_or_create_collection(collection_name)
 
 # Generate query embedding
 query_embedding = self.embedding_model.encode([query]).tolist()[0]
 
 # Search in ChromaDB
 results = collection.query(
 query_embeddings=[query_embedding],
 n_results=top_k,
 include=["documents", "metadatas", "distances"]
 )
 
 # Format results
 documents = []
 if results["documents"] and results["documents"][0]:
 for i in range(len(results["documents"][0])):
 doc = {
 "content": results["documents"][0][i],
 "metadata": results["metadatas"][0][i],
 "similarity": 1 - results["distances"][0][i], # Convert distance to similarity
 "source": results["metadatas"][0][i].get("source", "unknown"),
 "title": results["metadatas"][0][i].get("title", "Untitled")
 }
 documents.append(doc)
 
 return documents
 
 except Exception as e:
 print(f"ERROR: Failed to search documents: {e}")
 return []
 
 async def search_multiple_collections(self, query: str, 
 collections: List[str] = ["legal_docs", "consumer_protection"],
 top_k_per_collection: int = 3) -> List[Dict[str, Any]]:
 """Search across multiple collections"""
 all_results = []
 
 for collection_name in collections:
 try:
 results = await self.search_documents(query, collection_name, top_k_per_collection)
 for result in results:
 result["collection"] = collection_name
 all_results.extend(results)
 except Exception as e:
 print(f"ERROR: Failed to search collection {collection_name}: {e}")
 continue
 
 # Sort by similarity and return top results
 all_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
 return all_results[:top_k_per_collection * len(collections)]
 
 def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
 """Get statistics for a collection"""
 try:
 collection = self.get_or_create_collection(collection_name)
 count = collection.count()
 
 return {
 "name": collection_name,
 "document_count": count,
 "status": "active"
 }
 except Exception as e:
 return {
 "name": collection_name,
 "document_count": 0,
 "status": "error",
 "error": str(e)
 }
 
 def reset_collection(self, collection_name: str) -> bool:
 """Reset/clear a collection"""
 try:
 if collection_name in self.collections:
 del self.collections[collection_name]
 
 # Delete existing collection
 try:
 self.client.delete_collection(collection_name)
 except:
 pass # Collection might not exist
 
 # Create fresh collection
 self.get_or_create_collection(collection_name)
 return True
 
 except Exception as e:
 print(f"ERROR: Failed to reset collection {collection_name}: {e}")
 return False

# Global ChromaDB service instance
chroma_service = ChromaService()
