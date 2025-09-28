"""
FastAPI main application entry point for AI Legal Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routes.chat import router as chat_router
from routes.admin import router as admin_router
from routes.history import router as history_router

@asynccontextmanager
async def lifespan(app: FastAPI):
 """Application lifespan events"""
 # Startup
 print("Starting Starting AI Legal Assistant API...")
 yield
 # Shutdown
 print("🛑 Shutting down AI Legal Assistant API...")

# Create FastAPI app
app = FastAPI(
 title="AI Legal Assistant API",
 description="RAG-based legal chatbot with Firebase authentication and ChromaDB",
 version="2.0.0",
 lifespan=lifespan
)

# Configure CORS
app.add_middleware(
 CORSMiddleware,
 allow_origins=[
 "http://localhost:3000", # React dev server
 "http://localhost:5173", # Vite dev server
 "https://*.netlify.app", # Netlify deployments
 "https://*.vercel.app", # Vercel deployments
 ],
 allow_credentials=True,
 allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
 allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(history_router, prefix="/api", tags=["history"])

@app.get("/")
async def root():
 """Root endpoint"""
 return {
 "message": "AI Legal Assistant API",
 "version": "2.0.0",
 "status": "active",
 "docs": "/docs"
 }

@app.get("/health")
async def health_check():
 """Health check endpoint"""
 return {
 "status": "healthy",
 "version": "2.0.0",
 "services": {
 "firebase": "configured" if os.getenv("FIREBASE_CREDENTIALS") else "not_configured",
 "groq": "configured" if os.getenv("GROQ_API_KEY") else "not_configured",
 "chromadb": "active"
 }
 }
