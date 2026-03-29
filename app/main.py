import asyncio
import json
import logging
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

# Load environment variables FIRST
load_dotenv()

# ADK imports
from google.adk.agents import LlmAgent
from google.adk.runners import Runner, RunConfig
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.models.lite_llm import LiteLlm


# MCP
from mcp import StdioServerParameters

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("main")

app = FastAPI(title="Logistics Document Processing API")

# --------- Configuration ----------
MCP_SERVER_CMD = "python"
MCP_SERVER_ARGS = ["server.py"]
FLOW_MD_PATH = Path(__file__).with_name("agent_flow.md")
FLOW_MD = FLOW_MD_PATH.read_text(encoding="utf-8") if FLOW_MD_PATH.exists() else "You are a logistics document processing assistant."

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --------- Request/Response Models ----------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[dict] = None


# --------- Startup/Shutdown ----------
@app.on_event("startup")
async def startup():
    """Initialize ADK Runner with MCP toolset."""
    logger.info("[STARTUP] Initializing ADK Runner with MCP tools...")
    
    # Verify API key is loaded
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("[STARTUP] ❌ No GOOGLE_API_KEY or GEMINI_API_KEY found in environment!")
        raise RuntimeError("Missing Google API key. Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env file")
    
    logger.info(f"[STARTUP] ✅ API key loaded (length: {len(api_key)})")
    
    # Create MCPToolset
    toolset = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=MCP_SERVER_CMD,
                args=MCP_SERVER_ARGS
            ),
            timeout=60.0,
        )
    )
    
    # Create LlmAgent
    agent = LlmAgent(
    # Pass an instance of the LiteLlm class
        model=LiteLlm(model="openai/gpt-4.1"),
        name="logistics_agent",
        instruction=FLOW_MD,
        tools=[toolset],
    )

    
    # gemini >> openai
    
    
    # Create session service
    session_service = InMemorySessionService()
    
    # Create Runner with agent and session_service
    runner = Runner(
        app_name="logistics_document_processor",
        agent=agent,
        session_service=session_service
    )
    
    app.state.runner = runner
    logger.info("[STARTUP] ✅ ADK Runner initialized successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("[SHUTDOWN] Cleaning up...")


# --------- Main Chat Endpoint ----------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for document processing.
    """
    try:
        runner: Runner = app.state.runner
        
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"[CHAT] session={session_id[:8]}... | message: {request.message[:100]}")
        
        # Create session if it doesn't exist
        try:
            await runner.session_service.get_session(session_id)
            logger.info(f"[CHAT] Using existing session: {session_id[:8]}...")
        except:
            # Session doesn't exist, create it
            await runner.session_service.create_session(
                session_id=session_id,
                user_id="default_user",
                app_name="logistics_document_processor"
            )
            logger.info(f"[CHAT] Created new session: {session_id[:8]}...")
        
        # Create ADK message
        content = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )
        
        # Run agent and collect response
        response_parts = []
        async for event in runner.run_async(
            user_id="default_user",
            session_id=session_id,
            new_message=content,
            run_config=RunConfig()
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)
        
        # Combine response
        full_response = " ".join(response_parts).strip()
        
        if not full_response:
            full_response = "I apologize, but I couldn't generate a response. Please try again."
        
        logger.info(f"[CHAT] session={session_id[:8]}... | response length: {len(full_response)}")
        
        return ChatResponse(
            response=full_response,
            session_id=session_id,
            metadata={
                "model": "gemini-2.0-flash-exp",
                "message_length": len(request.message),
                "response_length": len(full_response)
            }
        )
        
    except Exception as e:
        logger.exception(f"[CHAT] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


# --------- File Upload Endpoint ----------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for processing.
    Returns the file path that can be used with process_document_end_to_end.
    """
    try:
        # Validate PDF
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"[UPLOAD] Saved: {file_path}")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": str(file_path.absolute()),
            "message": f"File uploaded successfully. Use this path: {file_path.absolute()}"
        }
        
    except Exception as e:
        logger.exception(f"[UPLOAD] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


# --------- Health Check ----------
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "runner_initialized": hasattr(app.state, "runner"),
        "service": "logistics_document_processor",
        "mcp_tools": [
            "classify_document",
            "extract_data_from_classified_pages",
            "process_document_end_to_end",
            "get_extracted_json",
            "get_all_extracted_data",
            "get_processing_status",
            "cleanup_workspace"
        ]
    }