"""
Improved RAG pipeline service using LangChain concepts with existing infrastructure
"""
import os
from typing import List, Dict, Any, Tuple, Optional
from groq import Groq

from .chroma_service import chroma_service
from .firebase_service import firebase_service
from .moderation_service import moderation_service


class LangChainRAGPipeline:
    """Improved RAG pipeline using LangChain concepts with existing infrastructure"""
    
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
            print("SUCCESS: Improved RAG pipeline with Groq LLM initialized")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize Groq client: {e}")
            raise
    
    async def process_query(self, query: str, user_id: str, 
                          conversation_id: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Improved RAG pipeline process:
        1. Moderate user query
        2. Retrieve relevant documents with better ranking
        3. Get conversation history
        4. Generate response with enhanced prompting
        5. Moderate response
        6. Return safe, contextual response
        """
        
        # Step 1: Content moderation on user query
        moderation_result = await moderation_service.moderate_user_query(query)
        if not moderation_result["is_safe"]:
            return self._create_safety_response(moderation_result), []
        
        try:
            # Step 2: Enhanced document retrieval
            print(f"Retrieving documents for query: {query[:50]}...")
            relevant_docs = await self._retrieve_documents_enhanced(query)
            print(f"Retrieved {len(relevant_docs)} documents")
            
            # Step 3: Get conversation history for context
            conversation_history = await firebase_service.get_conversation_history(
                user_id, conversation_id, limit=5
            )
            print(f"Retrieved {len(conversation_history)} conversation messages")
            
            # Step 4: Generate response with improved prompting
            print("Generating response...")
            response = await self._generate_response_enhanced(
                query, relevant_docs, conversation_history, moderation_result
            )
            print(f"Generated response: {response[:100]}...")
            
        except Exception as e:
            print(f"ERROR: Error in RAG pipeline: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later.", []
        
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
    
    async def _retrieve_documents_enhanced(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Enhanced document retrieval with better ranking and filtering"""
        try:
            # Search across multiple collections with improved strategy
            collections = ["legal_docs", "consumer_protection"]
            all_documents = []
            
            for collection_name in collections:
                docs = await chroma_service.search_documents(
                    query, collection_name, top_k=4
                )
                for doc in docs:
                    doc["collection"] = collection_name
                all_documents.extend(docs)
            
            # Enhanced filtering and ranking
            # 1. Filter by relevance threshold
            filtered_docs = [doc for doc in all_documents if doc.get("similarity", 0) > 0.25]
            
            # 2. Re-rank by combining similarity and content quality
            for doc in filtered_docs:
                content_length = len(doc.get("content", ""))
                # Boost score for documents with substantial content
                quality_boost = min(0.1, content_length / 2000)
                doc["enhanced_score"] = doc.get("similarity", 0) + quality_boost
            
            # 3. Sort by enhanced score and return top results
            filtered_docs.sort(key=lambda x: x.get("enhanced_score", 0), reverse=True)
            
            return filtered_docs[:top_k]
            
        except Exception as e:
            print(f"ERROR: Enhanced document retrieval failed: {e}")
            return []
    
    async def _generate_response_enhanced(self, query: str, documents: List[Dict[str, Any]], 
                                        history: List[Dict[str, Any]], 
                                        moderation_result: Dict[str, Any]) -> str:
        """Enhanced response generation with improved prompting"""
        
        # Build enhanced context from retrieved documents
        context_text = self._build_enhanced_context(documents)
        
        # Build conversation history context
        history_text = self._build_history_context(history)
        
        # Create enhanced system prompt
        system_prompt = self._create_enhanced_system_prompt(moderation_result)
        
        # Create enhanced user prompt with better structure
        user_prompt = f"""
        CONVERSATION CONTEXT:
        {history_text}

        RELEVANT LEGAL INFORMATION:
        {context_text}

        USER QUESTION: {query}

        INSTRUCTIONS:
        - Explain everything in simple, everyday language that anyone can understand
        - Replace legal jargon with plain English explanations
        - Use real-life examples and analogies from Indian context when helpful
        - Break complex ideas into simple steps
        - Be friendly and conversational, not formal
        - When you mention legal terms, immediately explain what they mean
        - Make it feel like you're talking to a friend who needs help understanding
        - ALWAYS focus on Indian law and legal system
        - Reference Indian legal acts, procedures, and court systems
        
        FORMATTING REQUIREMENTS:
        - Use bullet points (•) for lists and key points
        - Add line breaks between sections for better readability
        - Use **bold text** for important concepts and terms
        - Format legal terms as: "**FIR** (First Information Report - complaint to police)"
        - Use clear formatting for better readability
        - Structure responses with clear sections and spacing
        - End with a friendly, encouraging note about consulting an Indian advocate
        - Always clarify that information is based on Indian law
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.2,  # Lower temperature for more consistent legal responses
                max_tokens=1000,  # Increased token limit for comprehensive responses
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"ERROR: Enhanced LLM generation failed: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
    def _create_enhanced_system_prompt(self, moderation_result: Dict[str, Any]) -> str:
        """Create enhanced system prompt with better guidelines"""
        base_prompt = """You are a friendly AI legal assistant specializing in Indian law that helps everyday people understand legal matters in India. Your goal is to make Indian legal information easy to understand for someone without legal training.

        JURISDICTION & FOCUS:
        - You specialize exclusively in Indian law and legal system
        - Reference Indian legal acts, codes, and procedures
        - Use Indian legal terminology and concepts
        - Mention Indian courts (Supreme Court, High Courts, District Courts)
        - Reference Indian Constitution, IPC, CrPC, CPC, and other Indian laws
        - When unsure about jurisdiction, always clarify you're providing Indian law information

        COMMUNICATION STYLE:
        - Use simple, everyday language instead of legal jargon
        - Explain complex Indian legal terms in plain English
        - Use analogies and examples that Indian people can relate to
        - Break down complicated concepts into easy steps
        - Be conversational and approachable, not formal or intimidating

        CORE RESPONSIBILITIES:
        - Provide clear Indian legal information (not legal advice) in simple terms
        - Translate Indian legal concepts into everyday language
        - Use examples from Indian daily life to explain legal principles
        - Always explain what Indian legal terms mean in plain English
        - Recommend talking to an Indian lawyer/advocate for specific situations
        - Be helpful and easy to understand

        RESPONSE STRUCTURE & FORMATTING:
        1. Start with a clear, direct answer using simple language
        2. Use bullet points (•) or numbered lists for multiple points
        3. Add line breaks between different sections for readability
        4. Use **bold text** for important terms or key points
        5. Include practical examples from Indian context in separate paragraphs
        6. Format legal terms like: "**FIR** (First Information Report - the first complaint to police)"
        7. End with a friendly reminder about consulting an Indian advocate/lawyer
        8. Use clear visual formatting for better presentation

        INDIAN LEGAL TERMINOLOGY:
        - Use "advocate" or "lawyer" instead of "attorney"
        - Reference "High Court" and "Supreme Court of India"
        - Mention "District Court" and "Sessions Court" for lower courts
        - Use "complainant" and "accused" in criminal matters
        - Reference "Indian Penal Code (IPC)" for criminal law
        - Mention "Code of Criminal Procedure (CrPC)" and "Code of Civil Procedure (CPC)"
        - Always clarify Indian legal context when explaining procedures
        - Use "you" and "your" to make it personal and relatable

        IMPORTANT DISCLAIMERS:
        - Always specify that information is based on Indian law
        - Clarify that laws may vary between different Indian states
        - Recommend consulting a qualified Indian advocate for specific cases
        - Mention that legal procedures may differ across Indian jurisdictions"""
        
        # Add specific warnings based on moderation
        if moderation_result.get("requires_disclaimer"):
            base_prompt += "\n\nIMPORTANT: This query may be seeking specific legal advice. Be extra careful to provide general information only and strongly emphasize the need for professional legal consultation."
        
        if moderation_result.get("severity") == "medium":
            base_prompt += "\n\nCAUTION: Exercise additional care in your response due to the sensitive nature of this query."
        
        return base_prompt
    
    def _build_enhanced_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build enhanced context text with better organization"""
        if not documents:
            return "No specific legal documents found for this query."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled Document")
            content = doc.get("content", "")
            source = doc.get("source", "Unknown")
            collection = doc.get("collection", "legal")
            similarity = doc.get("similarity", 0)
            
            # Truncate content intelligently (try to end at sentence boundaries)
            truncated_content = content[:800]
            if len(content) > 800:
                last_period = truncated_content.rfind('.')
                if last_period > 600:  # Only truncate at period if it's not too early
                    truncated_content = truncated_content[:last_period + 1]
                else:
                    truncated_content += "..."
            
            context_parts.append(f"""
            SOURCE {i}: {title}
            Authority: {source} (Collection: {collection})
            Relevance Score: {similarity:.3f}
            Content: {truncated_content}
            """)
        
        return "\n" + "="*50 + "\n".join(context_parts) + "\n" + "="*50
    
    def _build_history_context(self, history: List[Dict[str, Any]]) -> str:
        """Build context from conversation history"""
        if not history:
            return "No previous conversation context."
        
        history_parts = ["RECENT CONVERSATION:"]
        for msg in history[-3:]:  # Last 3 exchanges
            user_msg = msg.get("user_message", "")
            bot_msg = msg.get("bot_response", "")
            
            if user_msg and bot_msg:
                history_parts.append(f"User: {user_msg}")
                history_parts.append(f"Assistant: {bot_msg[:200]}...")
                history_parts.append("---")
        
        return "\n".join(history_parts)
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source documents for frontend display"""
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            sources.append({
                "title": metadata.get("title", doc.get("title", "Untitled")),
                "source": metadata.get("source", doc.get("source", "Unknown")),
                "dataset_type": metadata.get("dataset_type", doc.get("collection", "legal")),
                "similarity": round(doc.get("similarity", 0), 3),
                "content_preview": doc.get("content", "")[:200] + "..."
            })
        
        return sources
    
    def _create_safety_response(self, moderation_result: Dict[str, Any]) -> str:
        """Create safe response for moderated content"""
        if moderation_result.get("severity") == "high":
            return """**Safety Notice**

I can't help with requests that might involve harmful content. 

**What I can do instead:**
• Answer general Indian legal questions in simple terms
• Explain how Indian legal processes work
• Help you understand your rights under Indian law
• Explain Indian legal procedures and court systems

Could you rephrase your question in a different way? I'm here to help with Indian legal information in a safe and constructive manner!"""
        
        return """**Happy to Help with Indian Law!**

I'd love to help you understand Indian legal information! 

**What I can explain:**
• General Indian legal concepts in simple terms
• How Indian legal processes work (courts, procedures, etc.)
• Your basic rights under Indian Constitution and laws
• What different Indian legal terms mean (IPC, CrPC, FIR, etc.)
• Indian court system (District Courts, High Courts, Supreme Court)

**What I can't do:**
• Give specific legal advice for your exact situation
• Tell you exactly what to do in your case

Could you rephrase your question to focus on general Indian legal concepts? 

**Remember:** For your specific situation, it's always best to talk with a qualified Indian advocate/lawyer who can give you personalized advice based on Indian law!"""
    
    async def search_multiple_collections(self, query: str, 
                                        collections: List[str] = ["legal_docs", "consumer_protection"]) -> List[Dict[str, Any]]:
        """Search across multiple ChromaDB collections using existing ChromaService"""
        return await chroma_service.search_multiple_collections(query, collections, top_k_per_collection=3)
    
    async def stream_response(self, query: str, user_id: str, conversation_id: str):
        """Generate streaming response for real-time chat experience"""
        # LangChain doesn't have built-in streaming for RetrievalQA yet
        # For now, return regular response (can be enhanced with custom streaming)
        response, sources = await self.process_query(query, user_id, conversation_id)
        yield {"type": "complete", "content": response, "sources": sources}


# Global LangChain RAG pipeline instance
langchain_rag_pipeline = LangChainRAGPipeline()
