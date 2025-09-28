"""
Chat routes for the AI Legal Assistant
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import json
import uuid
from datetime import datetime

from models.schemas import ChatRequest, ChatResponse, StreamingChatResponse
from services.firebase_service import firebase_service
from services.langchain_rag_pipeline import langchain_rag_pipeline

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

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
 request: ChatRequest,
 current_user: Dict[str, Any] = Depends(get_current_user)
):
 """
 Main chat endpoint for legal assistance
 
 Process flow:
 1. Authenticate user via Firebase JWT
 2. Validate and moderate user query
 3. Retrieve relevant documents from ChromaDB
 4. Generate contextual response using Groq LLM
 5. Moderate AI response
 6. Save conversation to Firebase
 7. Return structured response
 """
 try:
 # Verify user ID matches token
 if request.userId != current_user["uid"]:
 raise HTTPException(status_code=403, detail="User ID mismatch")
 
 # Generate conversation ID if not provided
 conversation_id = request.conversationId or f"conv_{uuid.uuid4().hex[:8]}"
 
 # Process query through LangChain RAG pipeline
 response_text, sources = await langchain_rag_pipeline.process_query(
 query=request.query,
 user_id=request.userId,
 conversation_id=conversation_id
 )
 
 # Save conversation to Firebase
 await firebase_service.save_conversation(
 user_id=request.userId,
 conversation_id=conversation_id,
 user_message=request.query,
 bot_response=response_text,
 sources=sources
 )
 
 # Return structured response
 return ChatResponse(
 response=response_text,
 sources=sources,
 conversationId=conversation_id,
 timestamp=datetime.now(),
 metadata={
 "model": "llama-3.1-8b-instant",
 "source_count": len(sources),
 "user_id": request.userId
 }
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: Chat endpoint error: {e}")
 raise HTTPException(
 status_code=500,
 detail="An error occurred while processing your request. Please try again."
 )

@router.post("/chat/stream")
async def chat_stream_endpoint(
 request: ChatRequest,
 current_user: Dict[str, Any] = Depends(get_current_user)
):
 """
 Streaming chat endpoint for real-time responses
 
 Returns Server-Sent Events (SSE) for real-time typing effect
 """
 try:
 # Verify user ID matches token
 if request.userId != current_user["uid"]:
 raise HTTPException(status_code=403, detail="User ID mismatch")
 
 # Generate conversation ID if not provided
 conversation_id = request.conversationId or f"conv_{uuid.uuid4().hex[:8]}"
 
 async def generate_stream():
 """Generate streaming response"""
 try:
 # Send initial status
 yield f"data: {json.dumps({'type': 'status', 'content': 'Processing your query...', 'conversationId': conversation_id})}\n\n"
 
 # Process query through LangChain RAG pipeline
 response_text, sources = await langchain_rag_pipeline.process_query(
 query=request.query,
 user_id=request.userId,
 conversation_id=conversation_id
 )
 
 # Stream response character by character for ChatGPT-style typing effect
 import asyncio
 
 for i, char in enumerate(response_text):
 chunk_data = {
 'type': 'token',
 'content': response_text[:i+1],
 'conversationId': conversation_id
 }
 yield f"data: {json.dumps(chunk_data)}\n\n"
 
 # Add small delay for realistic typing speed
 await asyncio.sleep(0.02) # 20ms delay between characters
 
 # Send sources
 if sources:
 sources_data = {
 'type': 'sources',
 'content': '',
 'sources': sources,
 'conversationId': conversation_id
 }
 yield f"data: {json.dumps(sources_data)}\n\n"
 
 # Send completion signal
 complete_data = {
 'type': 'complete',
 'content': response_text,
 'sources': sources,
 'conversationId': conversation_id,
 'metadata': {
 'model': 'llama-3.1-8b-instant',
 'source_count': len(sources)
 }
 }
 yield f"data: {json.dumps(complete_data)}\n\n"
 
 # Save conversation to Firebase
 await firebase_service.save_conversation(
 user_id=request.userId,
 conversation_id=conversation_id,
 user_message=request.query,
 bot_response=response_text,
 sources=sources
 )
 
 except Exception as e:
 error_data = {
 'type': 'error',
 'content': f'Error: {str(e)}',
 'conversationId': conversation_id
 }
 yield f"data: {json.dumps(error_data)}\n\n"
 
 return StreamingResponse(
 generate_stream(),
 media_type="text/plain",
 headers={
 "Cache-Control": "no-cache",
 "Connection": "keep-alive",
 "Content-Type": "text/event-stream"
 }
 )
 
 except HTTPException:
 raise
 except Exception as e:
 print(f"ERROR: Streaming chat error: {e}")
 raise HTTPException(
 status_code=500,
 detail="An error occurred while setting up the stream."
 )
