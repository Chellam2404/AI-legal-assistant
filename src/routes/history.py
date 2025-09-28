"""
History routes for conversation management
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any

from models.schemas import HistoryResponse, DeleteHistoryResponse
from services.firebase_service import firebase_service

router = APIRouter()

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
 """Extract and verify Firebase JWT token"""
 if not authorization or not authorization.startswith("Bearer "):
 raise HTTPException(status_code=401, detail="Authorization header required")
 
 try:
 token = authorization.split("Bearer ")[1]
 user_info = await firebase_service.verify_token(token)
 if not user_info:
 raise HTTPException(status_code=401, detail="Invalid or expired token")
 return user_info
 except Exception as e:
 raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.get("/history/{user_id}", response_model=HistoryResponse)
async def get_user_history(
 user_id: str,
 current_user: Dict[str, Any] = Depends(get_current_user)
):
 """
 Get conversation history for a specific user
 Users can only access their own history
 """
 try:
 # Verify user can only access their own history
 if user_id != current_user["uid"]:
 raise HTTPException(status_code=403, detail="Access denied: Can only access your own history")
 
 # Get conversations from Firebase
 conversations = await firebase_service.get_user_conversations(user_id)
 
 return HistoryResponse(
 conversations=conversations,
 total_count=len(conversations)
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: History retrieval error: {e}")
 raise HTTPException(
 status_code=500,
 detail="Failed to retrieve conversation history"
 )

@router.delete("/history/{user_id}", response_model=DeleteHistoryResponse)
async def delete_user_history(
 user_id: str,
 current_user: Dict[str, Any] = Depends(get_current_user)
):
 """
 Delete all conversation history for a specific user
 Users can only delete their own history
 """
 try:
 # Verify user can only delete their own history
 if user_id != current_user["uid"]:
 raise HTTPException(status_code=403, detail="Access denied: Can only delete your own history")
 
 # Delete conversations from Firebase
 deleted_count = await firebase_service.delete_user_conversations(user_id)
 
 return DeleteHistoryResponse(
 success=True,
 deleted_count=deleted_count
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: History deletion error: {e}")
 raise HTTPException(
 status_code=500,
 detail="Failed to delete conversation history"
 )
