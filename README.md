# AI Legal Assistant - FastAPI Backend

A complete RAG-based legal chatbot backend built with FastAPI, ChromaDB, Firebase, and Groq LLM.

## Architecture Architecture

```
src/
├── main.py # FastAPI app entry point
├── models/
│ └── schemas.py # Pydantic request/response models
├── routes/
│ ├── chat.py # Chat endpoints with streaming
│ ├── admin.py # Admin endpoints for document management
│ └── history.py # Conversation history endpoints
├── services/
│ ├── firebase_service.py # Firebase auth & storage
│ ├── chroma_service.py # ChromaDB vector operations
│ ├── moderation_service.py # Content moderation
│ └── rag_pipeline.py # Custom RAG pipeline
├── scripts/
│ └── index_data.py # Data indexing script
└── data/
 └── RAG_data.jsonl # Legal documents dataset
```

## Starting Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
# - GROQ_API_KEY=your_groq_api_key
# - FIREBASE_CREDENTIALS=path/to/firebase-service-account.json
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Index Your Data

```bash
python src/scripts/index_data.py
```

### 4. Start the Server

```bash
# Development
python app.py

# Production
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API API Endpoints

### Chat Endpoints
- `POST /api/chat` - Standard chat with legal assistant
- `POST /api/chat/stream` - Streaming chat with real-time responses

### History Endpoints 
- `GET /api/history/{userId}` - Get user's conversation history
- `DELETE /api/history/{userId}` - Clear user's conversation history

### Admin Endpoints (Requires admin privileges)
- `POST /api/admin/embed` - Add new documents to ChromaDB
- `GET /api/admin/collections` - Get collection statistics
- `POST /api/admin/collections/{name}/reset` - Reset a collection
- `GET /api/admin/system/status` - System health status

## Auth Authentication

All endpoints require Firebase JWT authentication:

```javascript
// Frontend example
const response = await fetch('/api/chat', {
 method: 'POST',
 headers: {
 'Authorization': `Bearer ${firebaseIdToken}`,
 'Content-Type': 'application/json'
 },
 body: JSON.stringify({
 query: "What are my rights as a consumer?",
 userId: firebaseUser.uid
 })
});
```

## Security Security Features

- **Firebase JWT Verification** - All requests authenticated
- **Content Moderation** - Both user queries and AI responses moderated
- **Rate Limiting** - Built-in Groq API rate limiting
- **Input Validation** - Pydantic schema validation
- **Legal Disclaimers** - Automatic legal disclaimers when appropriate

## Stats: RAG Pipeline

The custom RAG pipeline follows this flow:

1. **Query Moderation** - Check user input for safety
2. **Document Retrieval** - Search ChromaDB for relevant legal docs
3. **Context Building** - Combine docs + conversation history
4. **LLM Generation** - Generate response using Groq Llama 3.2
5. **Response Moderation** - Validate AI response for safety
6. **Storage** - Save conversation to Firebase

## Data Management

### Supported Collections
- `legal_docs` - General legal documents (~1000 records)
- `consumer_protection` - Consumer protection laws (~1000 records)

### Adding New Documents

```python
# Admin endpoint example
documents = [
 {
 "id": "doc_1",
 "title": "New Legal Document",
 "content": "Document content here...",
 "source": "Legal Source",
 "dataset_type": "legal"
 }
]

response = await fetch('/api/admin/embed', {
 method: 'POST',
 headers: {
 'Authorization': `Bearer ${adminToken}`,
 'Content-Type': 'application/json'
 },
 body: JSON.stringify({
 documents: documents,
 collection_name: "legal_docs"
 })
});
```

## Config Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `FIREBASE_CREDENTIALS` | Path to Firebase service account JSON | Yes |
| `CHROMA_DB_PATH` | ChromaDB storage path | No (default: ./chroma_db) |
| `ADMIN_EMAILS` | Comma-separated admin emails | No |
| `HOST` | Server host | No (default: 0.0.0.0) |
| `PORT` | Server port | No (default: 8000) |

### Firebase Setup

1. Create Firebase project
2. Enable Authentication and Firestore
3. Download service account key
4. Set `FIREBASE_CREDENTIALS` path in `.env`

### Groq Setup

1. Sign up at [Groq Console](https://console.groq.com)
2. Create API key
3. Set `GROQ_API_KEY` in `.env`

## Starting Deployment

### Render Deployment

1. Connect GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with build command: `pip install -r requirements.txt`
4. Start command: `python app.py`

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
```

## Testing Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint (requires auth)
curl -X POST http://localhost:8000/api/chat \
 -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
 -H "Content-Type: application/json" \
 -d '{"query": "What are consumer rights?", "userId": "user123"}'
```

## Metrics Monitoring

- Health check: `GET /health`
- System status: `GET /api/admin/system/status`
- Collection stats: `GET /api/admin/collections`

## Processing Frontend Integration

The backend is designed to work seamlessly with your existing React frontend. Key integration points:

### Chat Component
```javascript
const sendMessage = async (message) => {
 const response = await fetch('/api/chat/stream', {
 method: 'POST',
 headers: {
 'Authorization': `Bearer ${idToken}`,
 'Content-Type': 'application/json'
 },
 body: JSON.stringify({
 query: message,
 userId: user.uid,
 conversationId: currentConversationId
 })
 });

 // Handle streaming response
 const reader = response.body.getReader();
 // Process SSE stream...
};
```

### Authentication Integration
```javascript
// Firebase auth integration
import { onAuthStateChanged } from 'firebase/auth';

onAuthStateChanged(auth, async (user) => {
 if (user) {
 const idToken = await user.getIdToken();
 // Use token for API calls
 }
});
```

## Creating Legal Compliance

- Responses include appropriate legal disclaimers
- Content moderation prevents harmful advice
- Clear distinction between information and legal advice
- Source citations for transparency

## Troubleshooting

### Common Issues

1. **ChromaDB Permission Error**
 - Ensure `chroma_db` directory is writable
 - Check `CHROMA_DB_PATH` environment variable

2. **Firebase Authentication Failed**
 - Verify service account JSON path
 - Check Firebase project configuration

3. **Groq API Rate Limits**
 - Monitor usage in Groq console
 - Implement request queuing if needed

4. **Import Errors**
 - Ensure all dependencies installed
 - Check Python path configuration

## Sources API Documentation

Once running, visit:
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Contributing

1. Follow the modular architecture
2. Add comprehensive docstrings
3. Include error handling
4. Test with your React frontend
5. Update documentation

---

**Ready to deploy!** Starting Your FastAPI backend is production-ready and fully integrated with your React frontend.
