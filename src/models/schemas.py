"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
 """Request model for chat endpoint"""
 query: str = Field(..., min_length=1, max_length=1000, description="User's legal question")
 userId: str = Field(..., description="Firebase user ID")
 conversationId: Optional[str] = Field(None, description="Conversation ID for context")

class ChatResponse(BaseModel):
 """Response model for chat endpoint"""
 response: str = Field(..., description="AI assistant response")
 sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
 conversationId: str = Field(..., description="Conversation ID")
 timestamp: datetime = Field(default_factory=datetime.now)
 metadata: Dict[str, Any] = Field(default_factory=dict)

class EmbedRequest(BaseModel):
 """Request model for embedding documents"""
 documents: List[Dict[str, Any]] = Field(..., description="Documents to embed")
 collection_name: Optional[str] = Field("legal_docs", description="ChromaDB collection name")

class EmbedResponse(BaseModel):
 """Response model for embedding operation"""
 success: bool = Field(..., description="Whether embedding was successful")
 documents_processed: int = Field(..., description="Number of documents processed")
 collection_name: str = Field(..., description="Collection name used")

class HistoryResponse(BaseModel):
 """Response model for chat history"""
 conversations: List[Dict[str, Any]] = Field(..., description="User's conversation history")
 total_count: int = Field(..., description="Total number of conversations")

class DeleteHistoryResponse(BaseModel):
 """Response model for deleting history"""
 success: bool = Field(..., description="Whether deletion was successful")
 deleted_count: int = Field(..., description="Number of conversations deleted")

class HealthResponse(BaseModel):
 """Response model for health check"""
 status: str = Field(..., description="Service status")
 version: str = Field(..., description="API version")
 services: Dict[str, str] = Field(..., description="Service statuses")
 timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
 """Standard error response model"""
 error: str = Field(..., description="Error message")
 detail: Optional[str] = Field(None, description="Detailed error information")
 code: Optional[str] = Field(None, description="Error code")

class StreamingChatResponse(BaseModel):
 """Response model for streaming chat"""
 type: str = Field(..., description="Message type: 'token', 'sources', 'complete'")
 content: str = Field(..., description="Content for this chunk")
 sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source documents")
 conversationId: str = Field(..., description="Conversation ID")
 metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
