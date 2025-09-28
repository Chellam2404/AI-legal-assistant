"""
DEPRECATED - This file has been replaced by langchain_rag_pipeline.py
The old DIY RAG pipeline has been removed in favor of the improved LangChain-based implementation.
"""

# This file is kept for reference only and should not be imported
"""
Custom RAG pipeline for legal document retrieval and response generation
"""
import os
from typing import List, Dict, Any, Tuple
from groq import Groq
from .chroma_service import chroma_service
from .firebase_service import firebase_service
from .moderation_service import moderation_service

class RAGPipeline:
    """Custom RAG pipeline for legal assistant"""
    
    def __init__(self):
        self.groq_client = None
        self._initialize_groq()
    
    def _initialize_groq(self):
        """Initialize Groq client for LLM generation"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            self.groq_client = Groq(api_key=api_key)
            print("SUCCESS: Groq LLM client initialized")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize Groq client: {e}")
            raise
    
    async def process_query(self, query: str, user_id: str, 
                          conversation_id: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Complete RAG pipeline:
        1. Moderate user query
        2. Retrieve relevant documents
        3. Get conversation history
        4. Generate response with context
        5. Moderate response
        6. Return safe, contextual response
        """
        
        # Step 1: Content moderation on user query
        moderation_result = await moderation_service.moderate_user_query(query)
        if not moderation_result["is_safe"]:
            return self._create_safety_response(moderation_result), []
        
        # Step 2: Retrieve relevant documents from ChromaDB
        relevant_docs = await self._retrieve_documents(query)
        
        # Step 3: Get conversation history for context
        conversation_history = await firebase_service.get_conversation_history(
            user_id, conversation_id, limit=5
        )
        
        # Step 4: Generate response using LLM
        response = await self._generate_response(
            query, relevant_docs, conversation_history, moderation_result
        )
        
        # Step 5: Moderate AI response
        response_moderation = await moderation_service.moderate_ai_response(response, query)
        if not response_moderation["is_safe"]:
            response = moderation_service.filter_harmful_content(response)
        
        # Add legal disclaimer if needed
        if response_moderation.get("requires_disclaimer") or moderation_result.get("requires_disclaimer"):
            response = moderation_service.add_legal_disclaimer(response)
        
        # Step 6: Prepare source citations
        sources = self._format_sources(relevant_docs)
        
        return response, sources
    
    async def _retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from both law and consumer protection datasets"""
        try:
            # Search across multiple collections
            collections = ["legal_docs", "consumer_protection"]
            documents = await chroma_service.search_multiple_collections(
                query, collections, top_k_per_collection=3
            )
            
            # Filter by relevance threshold
            filtered_docs = [doc for doc in documents if doc.get("similarity", 0) > 0.3]
            
            return filtered_docs[:top_k]
            
        except Exception as e:
            print(f"ERROR: Document retrieval failed: {e}")
            return []
    
    async def _generate_response(self, query: str, documents: List[Dict[str, Any]], 
                               history: List[Dict[str, Any]], 
                               moderation_result: Dict[str, Any]) -> str:
        """Generate response using Groq LLM with retrieved context"""
        
        # Build context from retrieved documents
        context_text = self._build_document_context(documents)
        
        # Build conversation history context
        history_text = self._build_history_context(history)
        
        # Create system prompt
        system_prompt = self._create_system_prompt(moderation_result)
        
        # Create user prompt with context
        user_prompt = f"""
        Previous conversation context:
        {history_text}

        Relevant legal information:
        {context_text}

        Current question: {query}

        Please provide a helpful response based on the legal information provided. Be accurate, cite your sources, and include appropriate disclaimers.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ERROR: LLM generation failed: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
    def _create_system_prompt(self, moderation_result: Dict[str, Any]) -> str:
        """Create system prompt based on moderation results"""
        base_prompt = """You are a helpful AI legal assistant. Your role is to provide accurate legal information based on the provided documents.

        IMPORTANT GUIDELINES:
        - Provide information, not legal advice
        - Always cite your sources when possible
        - Be clear that you're providing general information
        - Suggest consulting a qualified attorney for specific legal advice
        - Stay within the bounds of the provided legal documents
        - Be helpful but cautious with legal matters"""
        
        # Add specific warnings based on moderation
        if moderation_result.get("requires_disclaimer"):
            base_prompt += "\n- This query may be seeking legal advice - be extra careful to provide information only"
        
        if moderation_result.get("severity") == "medium":
            base_prompt += "\n- Exercise additional caution in your response"
        
        return base_prompt
    
    def _build_document_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context text from retrieved documents"""
        if not documents:
            return "No specific legal documents found for this query."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled Document")
            content = doc.get("content", "")[:500]  # Limit content length
            source = doc.get("source", "Unknown")
            
            context_parts.append(f"""
            Document {i}: {title}
            Source: {source}
            Content: {content}
            """)
        
        return "\n".join(context_parts)
    
    def _build_history_context(self, history: List[Dict[str, Any]]) -> str:
        """Build context from conversation history"""
        if not history:
            return "No previous conversation context."
        
        history_parts = []
        for msg in history[-3:]:  # Last 3 exchanges
            user_msg = msg.get("user_message", "")
            bot_msg = msg.get("bot_response", "")
            
            history_parts.append(f"User: {user_msg}")
            history_parts.append(f"Assistant: {bot_msg}")
        
        return "\n".join(history_parts)
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source documents for frontend display"""
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            sources.append({
                "title": metadata.get("title", "Untitled"),
                "source": metadata.get("source", "Unknown"),
                "dataset_type": metadata.get("dataset_type", "legal"),
                "similarity": round(doc.get("similarity", 0), 3),
                "content_preview": doc.get("content", "")[:200] + "..."
            })
        
        return sources
    
    def _create_safety_response(self, moderation_result: Dict[str, Any]) -> str:
        """Create safe response for moderated content"""
        if moderation_result.get("severity") == "high":
            return "I cannot assist with requests that may involve harmful or dangerous content. Please rephrase your question in a constructive way."
        
        return "I understand you're looking for legal information. Could you please rephrase your question to focus on general legal concepts rather than specific advice?"
    
    async def stream_response(self, query: str, user_id: str, 
                            conversation_id: str):
        """Generate streaming response for real-time chat experience"""
        # This will be implemented for streaming support
        # For now, return regular response
        response, sources = await self.process_query(query, user_id, conversation_id)
        yield {"type": "complete", "content": response, "sources": sources}

# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
