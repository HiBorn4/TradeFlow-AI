# server.py - MCP Server with Document Processing Tools
from mcp.server.fastmcp import FastMCP
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List
import shutil

mcp = FastMCP("Document Processing APIs")

# Configuration
BASE_DIR = Path(__file__).parent
CLASSIFICATION_SCRIPT = BASE_DIR / "classification.py"
VISION_SCRIPT = BASE_DIR / "vision.py"
OUTPUT_DIR = BASE_DIR / "extracted_data"
CLASSIFIED_DIR = BASE_DIR / "classified_pages"


@mcp.tool()
def classify_document(pdf_path: str) -> Dict:
    """
    Classify a PDF document into different document types (Packing List, Commercial Invoice, etc.).
    Each page is classified and saved to appropriate directory.
    
    Args:
        pdf_path: Absolute path to the PDF file to classify
        
    Returns:
        dict: Classification results with page counts per document type
    """
    try:
        # Validate PDF exists
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        # Run classification script
        result = subprocess.run(
            ["python", str(CLASSIFICATION_SCRIPT)],
            env={"PDF_PATH": pdf_path},
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Classification failed: {result.stderr}"
            }
        
        # Count classified pages
        classified_counts = {}
        if CLASSIFIED_DIR.exists():
            for class_dir in CLASSIFIED_DIR.iterdir():
                if class_dir.is_dir():
                    page_count = len(list(class_dir.glob("*.png")))
                    if page_count > 0:
                        classified_counts[class_dir.name] = page_count
        
        return {
            "success": True,
            "message": "Document classified successfully",
            "classified_pages": classified_counts,
            "output_directory": str(CLASSIFIED_DIR)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Classification timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Classification error: {str(e)}"
        }


@mcp.tool()
def extract_data_from_classified_pages() -> Dict:
    """
    Extract structured data from all classified document pages.
    Processes 5 document classes in parallel: Packing List, Commercial Invoice, 
    Package Declaration, Import Declaration, Tax Invoice.
    
    Returns:
        dict: Extraction results with paths to generated JSON files
    """
    try:
        # Validate classified pages exist
        if not CLASSIFIED_DIR.exists():
            return {
                "success": False,
                "error": "No classified pages found. Run classify_document first."
            }
        
        # Run vision extraction script
        result = subprocess.run(
            ["python", str(VISION_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes for parallel processing
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Data extraction failed: {result.stderr}",
                "stdout": result.stdout
            }
        
        # Collect generated JSON files
        extracted_files = {}
        if OUTPUT_DIR.exists():
            for class_dir in OUTPUT_DIR.iterdir():
                if class_dir.is_dir():
                    json_files = list(class_dir.glob("*_batch_result*.json"))
                    if json_files:
                        extracted_files[class_dir.name] = [str(f) for f in json_files]
        
        # Also get consolidated file
        consolidated = OUTPUT_DIR / "all_extracted_data.json"
        if consolidated.exists():
            extracted_files["consolidated"] = str(consolidated)
        
        return {
            "success": True,
            "message": "Data extraction completed successfully",
            "extracted_files": extracted_files,
            "output_directory": str(OUTPUT_DIR)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Data extraction timed out after 30 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Extraction error: {str(e)}"
        }


@mcp.tool()
def process_document_end_to_end(pdf_path: str) -> Dict:
    """
    Complete document processing pipeline: classify PDF pages, then extract structured data.
    This is the main workflow that combines classification and extraction.
    
    Args:
        pdf_path: Absolute path to the PDF file to process
        
    Returns:
        dict: Complete processing results with classification counts and extracted JSON paths
    """
    # Step 1: Classify document
    classification_result = classify_document(pdf_path)
    
    if not classification_result.get("success"):
        return {
            "success": False,
            "step": "classification",
            "error": classification_result.get("error")
        }
    
    # Step 2: Extract data from classified pages
    extraction_result = extract_data_from_classified_pages()
    
    if not extraction_result.get("success"):
        return {
            "success": False,
            "step": "extraction",
            "classification_result": classification_result,
            "error": extraction_result.get("error")
        }
    
    # Return combined results
    return {
        "success": True,
        "message": "Document processed successfully",
        "classification": classification_result,
        "extraction": extraction_result,
        "summary": {
            "pages_classified": classification_result.get("classified_pages", {}),
            "json_files_generated": extraction_result.get("extracted_files", {})
        }
    }


@mcp.tool()
def get_extracted_json(document_class: str) -> Dict:
    """
    Retrieve the extracted JSON data for a specific document class.
    
    Args:
        document_class: Document type (e.g., "Packing List", "Commercial Invoice")
        
    Returns:
        dict: The extracted JSON data or error message
    """
    try:
        # Normalize class name for file path
        class_slug = document_class.replace(" ", "_").lower()
        class_dir = OUTPUT_DIR / document_class
        
        if not class_dir.exists():
            return {
                "success": False,
                "error": f"No extracted data found for {document_class}"
            }
        
        # Find the JSON file
        json_files = list(class_dir.glob(f"{class_slug}_batch_result*.json"))
        
        if not json_files:
            return {
                "success": False,
                "error": f"No JSON files found for {document_class}"
            }
        
        # Read the most recent file
        json_file = json_files[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "document_class": document_class,
            "file_path": str(json_file),
            "data": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading JSON: {str(e)}"
        }


@mcp.tool()
def get_all_extracted_data() -> Dict:
    """
    Retrieve all extracted JSON data from all document classes.
    
    Returns:
        dict: Consolidated data from all processed documents
    """
    try:
        consolidated_file = OUTPUT_DIR / "all_extracted_data.json"
        
        if not consolidated_file.exists():
            return {
                "success": False,
                "error": "No consolidated data found. Run extraction first."
            }
        
        with open(consolidated_file, 'r') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "message": "All extracted data retrieved successfully",
            "file_path": str(consolidated_file),
            "data": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading consolidated data: {str(e)}"
        }


@mcp.tool()
def cleanup_workspace() -> Dict:
    """
    Clean up all classified pages and extracted data.
    Use this to reset the workspace before processing a new document.
    
    Returns:
        dict: Cleanup status
    """
    try:
        cleaned = []
        
        # Remove classified pages
        if CLASSIFIED_DIR.exists():
            shutil.rmtree(CLASSIFIED_DIR)
            cleaned.append("classified_pages")
        
        # Remove extracted data
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
            cleaned.append("extracted_data")
        
        return {
            "success": True,
            "message": "Workspace cleaned successfully",
            "cleaned_directories": cleaned
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Cleanup error: {str(e)}"
        }


@mcp.tool()
def get_processing_status() -> Dict:
    """
    Check the current processing status and available data.
    
    Returns:
        dict: Status information about classified pages and extracted data
    """
    status = {
        "classified_pages": {},
        "extracted_data": {},
        "workspace_ready": True
    }
    
    # Check classified pages
    if CLASSIFIED_DIR.exists():
        for class_dir in CLASSIFIED_DIR.iterdir():
            if class_dir.is_dir():
                page_count = len(list(class_dir.glob("*.png")))
                if page_count > 0:
                    status["classified_pages"][class_dir.name] = page_count
    
    # Check extracted data
    if OUTPUT_DIR.exists():
        for class_dir in OUTPUT_DIR.iterdir():
            if class_dir.is_dir():
                json_files = list(class_dir.glob("*.json"))
                if json_files:
                    status["extracted_data"][class_dir.name] = len(json_files)
        
        # Check consolidated file
        consolidated = OUTPUT_DIR / "all_extracted_data.json"
        if consolidated.exists():
            status["extracted_data"]["consolidated"] = True
    
    status["has_classified_pages"] = len(status["classified_pages"]) > 0
    status["has_extracted_data"] = len(status["extracted_data"]) > 0
    
    return status


if __name__ == "__main__":
    mcp.run(transport="stdio")