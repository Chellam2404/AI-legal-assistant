"""
Firebase service for authentication and conversation storage
"""
import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import HTTPException

class FirebaseService:
 """Firebase service for authentication and data storage"""
 
 def __init__(self):
 self.app = None
 self.db = None
 self._initialize_firebase()
 
 def _initialize_firebase(self):
 """Initialize Firebase Admin SDK"""
 try:
 # Check if Firebase is already initialized
 if firebase_admin._apps:
 self.app = firebase_admin.get_app()
 else:
 # Initialize from environment variable or service account file
 cred_path = os.getenv("FIREBASE_CREDENTIALS")
 if cred_path and os.path.exists(cred_path):
 cred = credentials.Certificate(cred_path)
 self.app = firebase_admin.initialize_app(cred)
 else:
 # Try to initialize from environment variables
 firebase_config = os.getenv("FIREBASE_CONFIG")
 if firebase_config:
 config_dict = json.loads(firebase_config)
 cred = credentials.Certificate(config_dict)
 self.app = firebase_admin.initialize_app(cred)
 else:
 print("WARNING: Firebase credentials not found. Authentication will be disabled.")
 return
 
 # Initialize Firestore
 self.db = firestore.client()
 print("SUCCESS: Firebase initialized successfully")
 
 except Exception as e:
 print(f"ERROR: Failed to initialize Firebase: {e}")
 self.app = None
 self.db = None
 
 async def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
 """Verify Firebase ID token and return user info"""
 if not self.app:
 return None
 
 try:
 # Verify the token
 decoded_token = auth.verify_id_token(id_token)
 
 return {
 "uid": decoded_token["uid"],
 "email": decoded_token.get("email"),
 "name": decoded_token.get("name"),
 "email_verified": decoded_token.get("email_verified", False)
 }
 except Exception as e:
 print(f"ERROR: Token verification failed: {e}")
 return None
 
 async def save_conversation(self, user_id: str, conversation_id: str, 
 user_message: str, bot_response: str, 
 sources: List[Dict[str, Any]]) -> bool:
 """Save conversation message to Firestore"""
 if not self.db:
 return False
 
 try:
 # Reference to user's conversations
 user_ref = self.db.collection("users").document(user_id)
 conv_ref = user_ref.collection("conversations").document(conversation_id)
 
 # Get existing conversation or create new one
 conv_doc = conv_ref.get()
 if conv_doc.exists:
 conv_data = conv_doc.to_dict()
 messages = conv_data.get("messages", [])
 else:
 messages = []
 # Create conversation metadata
 conv_ref.set({
 "created_at": datetime.now(),
 "updated_at": datetime.now(),
 "title": user_message[:50] + "..." if len(user_message) > 50 else user_message,
 "messages": []
 })
 
 # Add new message
 new_message = {
 "timestamp": datetime.now(),
 "user_message": user_message,
 "bot_response": bot_response,
 "sources": sources
 }
 messages.append(new_message)
 
 # Keep only last 20 messages per conversation
 if len(messages) > 20:
 messages = messages[-20:]
 
 # Update conversation
 conv_ref.update({
 "messages": messages,
 "updated_at": datetime.now(),
 "message_count": len(messages)
 })
 
 return True
 
 except Exception as e:
 print(f"ERROR: Failed to save conversation: {e}")
 return False
 
 async def get_conversation_history(self, user_id: str, conversation_id: str, 
 limit: int = 10) -> List[Dict[str, Any]]:
 """Get conversation history for context"""
 if not self.db:
 return []
 
 try:
 conv_ref = (self.db.collection("users").document(user_id)
 .collection("conversations").document(conversation_id))
 
 conv_doc = conv_ref.get()
 if not conv_doc.exists:
 return []
 
 conv_data = conv_doc.to_dict()
 messages = conv_data.get("messages", [])
 
 # Return last N messages for context
 return messages[-limit:] if messages else []
 
 except Exception as e:
 print(f"ERROR: Failed to get conversation history: {e}")
 return []
 
 async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
 """Get all conversations for a user"""
 if not self.db:
 return []
 
 try:
 conversations = []
 conv_ref = (self.db.collection("users").document(user_id)
 .collection("conversations"))
 
 docs = conv_ref.order_by("updated_at", direction=firestore.Query.DESCENDING).get()
 
 for doc in docs:
 data = doc.to_dict()
 conversations.append({
 "id": doc.id,
 "title": data.get("title", "Untitled"),
 "created_at": data.get("created_at"),
 "updated_at": data.get("updated_at"),
 "message_count": data.get("message_count", 0)
 })
 
 return conversations
 
 except Exception as e:
 print(f"ERROR: Failed to get user conversations: {e}")
 return []
 
 async def delete_user_conversations(self, user_id: str) -> int:
 """Delete all conversations for a user"""
 if not self.db:
 return 0
 
 try:
 deleted_count = 0
 conv_ref = (self.db.collection("users").document(user_id)
 .collection("conversations"))
 
 docs = conv_ref.get()
 for doc in docs:
 doc.reference.delete()
 deleted_count += 1
 
 return deleted_count
 
 except Exception as e:
 print(f"ERROR: Failed to delete conversations: {e}")
 return 0

# Global Firebase service instance
firebase_service = FirebaseService()
