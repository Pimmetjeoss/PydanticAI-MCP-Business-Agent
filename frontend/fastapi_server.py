"""
FastAPI server for PydanticAI Business Agent frontend.

This server provides REST API endpoints for the Streamlit frontend to interact
with the PydanticAI business agent, including streaming support.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import the business agent from parent directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mcp_business_agent.agent import business_agent
from mcp_business_agent.dependencies import MCPAgentDependencies, get_mcp_dependencies
from mcp_business_agent.settings import load_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    """Request model for chat endpoints."""
    message: str = Field(..., description="User message to send to the agent")
    system_prompt: Optional[str] = Field(None, description="Optional custom system prompt")
    model_name: Optional[str] = Field(None, description="Optional model name to use")

class ChatResponse(BaseModel):
    """Response model for non-streaming chat endpoint."""
    response: str = Field(..., description="Agent response")
    status: str = Field(default="success", description="Response status")

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(default="healthy", description="Service status")
    agent_loaded: bool = Field(..., description="Whether agent is loaded successfully")

# Global variables
settings = None
dependencies = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the FastAPI application with agent dependencies."""
    global settings, dependencies
    
    try:
        # Load settings and initialize dependencies
        settings = load_settings()
        dependencies = await get_mcp_dependencies(
            user_id="frontend_user",
            session_id="frontend_session"
        )
        logger.info("FastAPI server initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize FastAPI server: {e}")
        raise
    finally:
        logger.info("FastAPI server shutting down")

# Create FastAPI app
app = FastAPI(
    title="PydanticAI Business Agent API",
    description="REST API for PydanticAI Business Agent with streaming support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    agent_loaded = business_agent is not None and dependencies is not None
    return HealthResponse(agent_loaded=agent_loaded)

@app.post("/ask", response_model=ChatResponse)
async def ask_agent(request: ChatRequest):
    """
    Non-streaming endpoint for simple questions.
    Returns the complete response at once.
    """
    if not dependencies:
        raise HTTPException(status_code=500, detail="Agent dependencies not initialized")
    
    try:
        # Use the business agent to get a response
        agent_to_use = business_agent
        
        # Create a custom system prompt if provided
        if request.system_prompt:
            # Note: In production, you might want to create a new agent instance
            # with the custom system prompt rather than modifying the existing one
            logger.info(f"Using custom system prompt: {request.system_prompt[:100]}...")
        
        # Run the agent
        result = await agent_to_use.run(request.message, deps=dependencies)
        
        return ChatResponse(response=str(result.data))
        
    except Exception as e:
        logger.error(f"Error in ask_agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

async def stream_agent_response(message: str, deps: MCPAgentDependencies) -> AsyncGenerator[str, None]:
    """
    Stream agent responses using PydanticAI's run_stream method.
    """
    try:
        # Use run_stream for streaming responses
        async with business_agent.run_stream(message, deps=deps) as response:
            # Stream the response parts
            async for part in response.stream():
                # Format the streaming data as JSON for the frontend
                chunk_data = {
                    "type": "stream",
                    "content": str(part),
                    "done": False
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Send final completion signal
            final_data = {
                "type": "done",
                "content": "",
                "done": True
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        error_data = {
            "type": "error",
            "content": f"Error: {str(e)}",
            "done": True
        }
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Streaming endpoint for chat interactions.
    Returns Server-Sent Events (SSE) stream.
    """
    if not dependencies:
        raise HTTPException(status_code=500, detail="Agent dependencies not initialized")
    
    return StreamingResponse(
        stream_agent_response(request.message, dependencies),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/models")
async def get_available_models():
    """
    Get list of available models.
    """
    # This would ideally come from your settings or provider configuration
    models = [
        {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
        {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "anthropic"},
        {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "anthropic"},
    ]
    return {"models": models}

@app.get("/agent-info")
async def get_agent_info():
    """
    Get information about the loaded agent and its capabilities.
    """
    if not business_agent:
        raise HTTPException(status_code=500, detail="Agent not loaded")
    
    # Get agent tools information
    tools_info = []
    if hasattr(business_agent, '_tools'):
        for tool_name, tool_func in business_agent._tools.items():
            tools_info.append({
                "name": tool_name,
                "description": getattr(tool_func, '__doc__', 'No description available')
            })
    
    return {
        "agent_loaded": True,
        "tools_count": len(tools_info),
        "tools": tools_info,
        "model": str(business_agent.model) if hasattr(business_agent, 'model') else "Unknown"
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )