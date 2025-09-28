"""
Admin routes for document management and system administration
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any, List
import os

from models.schemas import EmbedRequest, EmbedResponse
from services.firebase_service import firebase_service
from services.chroma_service import chroma_service

router = APIRouter()

async def verify_admin_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
 """Verify admin privileges"""
 if not authorization or not authorization.startswith("Bearer "):
 raise HTTPException(status_code=401, detail="Authorization header required")
 
 try:
 token = authorization.split("Bearer ")[1]
 user_info = await firebase_service.verify_token(token)
 if not user_info:
 raise HTTPException(status_code=401, detail="Invalid or expired token")
 
 # Check if user is admin (you can implement your admin logic here)
 admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
 if user_info.get("email") not in admin_emails:
 raise HTTPException(status_code=403, detail="Admin privileges required")
 
 return user_info
 except HTTPException:
 raise
 except Exception as e:
 raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.post("/embed", response_model=EmbedResponse)
async def embed_documents(
 request: EmbedRequest,
 admin_user: Dict[str, Any] = Depends(verify_admin_user)
):
 """
 Embed new documents into ChromaDB
 Admin-only endpoint for adding new legal documents
 """
 try:
 if not request.documents:
 raise HTTPException(status_code=400, detail="No documents provided")
 
 # Embed documents into ChromaDB
 documents_processed = await chroma_service.embed_documents(
 documents=request.documents,
 collection_name=request.collection_name
 )
 
 return EmbedResponse(
 success=documents_processed > 0,
 documents_processed=documents_processed,
 collection_name=request.collection_name
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: Document embedding error: {e}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to embed documents: {str(e)}"
 )

@router.get("/collections")
async def get_collections(admin_user: Dict[str, Any] = Depends(verify_admin_user)):
 """Get information about all ChromaDB collections"""
 try:
 collections_info = []
 
 # Get stats for known collections
 known_collections = ["legal_docs", "consumer_protection"]
 for collection_name in known_collections:
 stats = chroma_service.get_collection_stats(collection_name)
 collections_info.append(stats)
 
 return {
 "collections": collections_info,
 "total_collections": len(collections_info)
 }
 
 except Exception as e:
 print(f"ERROR: Collections info error: {e}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to get collections info: {str(e)}"
 )

@router.post("/collections/{collection_name}/reset")
async def reset_collection(
 collection_name: str,
 admin_user: Dict[str, Any] = Depends(verify_admin_user)
):
 """Reset/clear a specific collection"""
 try:
 success = chroma_service.reset_collection(collection_name)
 
 if success:
 return {
 "success": True,
 "message": f"Collection '{collection_name}' has been reset",
 "collection_name": collection_name
 }
 else:
 raise HTTPException(
 status_code=500,
 detail=f"Failed to reset collection '{collection_name}'"
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: Collection reset error: {e}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to reset collection: {str(e)}"
 )

@router.get("/system/status")
async def get_system_status(admin_user: Dict[str, Any] = Depends(verify_admin_user)):
 """Get comprehensive system status"""
 try:
 # Get ChromaDB status
 collections_info = []
 known_collections = ["legal_docs", "consumer_protection"]
 for collection_name in known_collections:
 stats = chroma_service.get_collection_stats(collection_name)
 collections_info.append(stats)
 
 # Get service statuses
 services_status = {
 "firebase": "configured" if firebase_service.db else "not_configured",
 "groq": "configured" if os.getenv("GROQ_API_KEY") else "not_configured",
 "chromadb": "active",
 "embedding_model": "active"
 }
 
 return {
 "status": "healthy",
 "services": services_status,
 "collections": collections_info,
 "environment": {
 "python_version": "3.11+",
 "fastapi_version": "0.104+",
 "admin_user": admin_user.get("email", "unknown")
 }
 }
 
 except Exception as e:
 print(f"ERROR: System status error: {e}")
 raise HTTPException(
 status_code=500,
 detail=f"Failed to get system status: {str(e)}"
 )
