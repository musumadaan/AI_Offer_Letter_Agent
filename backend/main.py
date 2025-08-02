from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from backend.offer_letter_agent import generate_offer_for, check_system_status, list_employees
import traceback
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
logger.info("Initializing Offer Letter Generator API")

# Load environment variables directly (no .env file on Railway)
openrouter_key = os.getenv("OPENROUTER_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")
logger.debug(f"Loaded OPENROUTER_API_KEY: {openrouter_key[:4] if openrouter_key else 'None'}...[REDACTED]")
logger.debug(f"Loaded PINECONE_API_KEY: {pinecone_key[:4] if pinecone_key else 'None'}...[REDACTED]")

app = FastAPI(
    title="Offer Letter Generator API",
    description="Generate professional offer letters using company policies",
    version="1.0.0"
)

# Mount the React build folder
app.mount("/static", StaticFiles(directory="frontend/build"), name="static")

# Root endpoint with API information
@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Offer Letter Generator API",
        "status": "running",
        "endpoints": {
            "generate_offer": "/generate-offer/?name={employee_name}",
            "check_system_status": "/check-system-status/",
            "health_check": "/health/",
            "list_employees": "/list-employees/"
        }
    }

# Basic health check
@app.get("/health/")
def health_check():
    logger.info("Health check performed")
    return {"status": "healthy", "message": "API is running"}

# Check system status
@app.get("/check-system-status/")
def check_system_status_endpoint():
    logger.info("Checking system status")
    try:
        status = check_system_status()
        logger.info(f"System status: {status['status']}")
        return status
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"system_status": "error", "message": f"Status check failed: {str(e)}"}
        )

# List all employees
@app.get("/list-employees/")
def get_employees():
    logger.info("Listing employees")
    try:
        employees = list_employees()
        logger.info(f"Successfully listed {employees['count']} employees")
        return employees
    except Exception as e:
        logger.error(f"Failed to list employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list employees: {str(e)}")

# Generate offer letter
@app.get("/generate-offer/")
def generate_offer(name: str = Query(..., description="Employee name to generate offer letter for")):
    try:
        logger.info(f"Generating offer letter for employee: {name}")
        response = generate_offer_for(name)
        
        if "error" in response:
            logger.warning(f"Employee not found: {name}")
            raise HTTPException(status_code=404, detail=response["error"])
        
        logger.info(f"Successfully generated offer letter for {name} using {response.get('method', 'unknown')} method")
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"Error generating offer for {name}: {str(e)}")
        print(traceback_str)
        
        error_str = str(e).lower()
        if "quota" in error_str or "429" in error_str or "insufficient_quota" in error_str:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "OpenRouter.ai quota exceeded. Template generation should be available.",
                    "suggestion": "The system should automatically use template generation. Check your OpenRouter.ai configuration if persistent."
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Internal Server Error: {str(e)}",
                    "message": "An unexpected error occurred during offer generation"
                }
            )

# Global exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    logger.warning(f"404 Not Found for request {request.url}: {str(exc.detail) if hasattr(exc, 'detail') else 'Resource not found'}")
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Unhandled server error for request {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"}
    )

# CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # Added "*" for deployed app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)