import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import base64
from io import BytesIO
from pathlib import Path
from utils.class_prompts import CLASS_PROMPTS
from utils.class_schema_mappings import CLASS_SCHEMA_MAPPING
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()


# Packing List
# Get all the image data (10>) -> + Json schema -> + Prompt -> Call LLM -> Get structured data


# Commercial Invoice

# ==================================================
# CONFIG
# ==================================================
BASE_DIR = "classified_pages"
OUTPUT_DIR = "extracted_data"
MODEL = "gpt-4.1"  # Use GPT-4o for vision

CLASSES = [
    "Packing List",
    "Commercial Invoice",
    "Package Declaration",
    "Import Declaration",
    "Tax Invoice",
]

# ==================================================
# INIT
# ==================================================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================================================
# HELPER FUNCTIONS
# ==================================================
def load_image(image_path):
    """Load image from file path."""
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def image_to_base64(image):
    """Convert PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def load_schemas(schema_paths):
    """Load JSON schemas from file paths."""
    schemas = []
    for path in schema_paths:
        try:
            with open(path, 'r') as f:
                schema = json.load(f)
                schemas.append(schema)
        except FileNotFoundError:
            print(f"⚠️ Schema file not found: {path}")
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in schema file: {path}")
    return schemas

# ==================================================
# SYSTEM PROMPT
# ==================================================
SYSTEM_PROMPT = """You are a data extraction and structuring expert specializing in document processing for ERP systems.

## Core Responsibilities

1. **Extract ALL visible data** from provided document images with 100% accuracy
2. **Map extracted data** to the exact structure defined in provided JSON schemas
3. **Return clean, valid JSON** with no null/empty attributes

## Critical Rules

### Data Extraction
- Extract EVERY piece of information visible in the images
- Preserve exact values (numbers, dates, codes, names) as shown
- Do NOT infer, assume, or generate data not present in images
- Maintain original formatting for codes and identifiers

### Schema Compliance
- Use ONLY DocTypes and fields defined in provided schemas
- Follow exact field names and data types from schemas
- DO NOT create custom fields or attributes
- Remove any null, empty, or undefined attributes from output

### Data Structuring
- Understand parent-child relationships in schemas
- Nest child records within parent records where schemas indicate relationships
- For example: if "Ship Unit Content" schema references "Ship Unit", nest content array inside ship unit object
- Maintain referential integrity between related records

### Value Processing
- **Text Cleaning**: Remove line feeds, excess whitespace, and special characters from descriptions
- **Code Extraction**: Extract only relevant portions from composite strings (e.g., "LOT 3 (Jan 25)" → "LOT3")
- **Whitespace Removal**: Strip ALL whitespace from codes and identifiers (contract numbers, lot numbers, shipment parts)
- **Value Parsing**: Split composite fields into individual schema fields (e.g., "Sydney, NSW 2000" → city: "Sydney", state: "NSW", pincode: "2000")
- **PRESERVE Normal Text**: Keep spaces and punctuation in names, descriptions, and addresses

### Output Format
- Return ONLY a JSON array: `[{...}, {...}]`
- NO markdown formatting, NO code blocks, NO explanations
- NO null attributes - omit fields without values
- Ensure valid JSON syntax (proper quotes, commas, brackets)

## Quality Checklist

Before returning output, verify:
✓ All visible data from images is extracted
✓ All data maps to schema fields correctly
✓ No custom/undefined fields exist
✓ No null/empty attributes remain
✓ Parent-child relationships are properly nested
✓ Output is valid JSON array format
✓ Codes are cleaned of whitespace
✓ Text fields preserve readability"""

# ==================================================
# EXTRACTION FUNCTION
# ==================================================
def openai_extract_data_batch_vision(images_data, document_class):
    """
    Extract structured data from multiple images in a single LLM call.
    """
    if not images_data:
        return {"error": "No images provided", "document_class": document_class}
    
    # Load schemas
    schema_paths = CLASS_SCHEMA_MAPPING.get(document_class, [])
    schemas = load_schemas(schema_paths)
    
    # Get class-specific prompt
    class_prompt = CLASS_PROMPTS.get(document_class, "")
    
    # Build user prompt
    user_prompt = f"""**TASK: Extract Complete {document_class} Data**

Process these {document_class} images and structure ALL data according to the provided schemas.

---

**DOCUMENT TYPE: {document_class}**

**SCHEMA DEFINITIONS:**
{json.dumps(schemas, indent=2)}

---

{class_prompt}

---

**CRITICAL REMINDERS:**

1. Process ALL {len(images_data)} images together as ONE complete document
2. Extract data from EVERY row in tables - do not skip rows
3. Nest child records inside parent records (e.g., Ship Unit Content inside Ship Unit)
4. Remove ALL null/empty attributes from output
5. Clean codes by removing whitespace (source_contract_no, lot_no, etc.)
6. Parse composite address fields into separate schema fields
7. Preserve exact container IDs, seal numbers, and weights

**RETURN FORMAT:**
Return ONLY the JSON array. No markdown, no explanations, no code blocks.
Start with `[` and end with `]`.
"""
    
    # Build content array
    content = [{"type": "text", "text": user_prompt}]
    
    for idx, img_data in enumerate(images_data, 1):
        image_base64 = image_to_base64(img_data['image'])
        content.append({
            "type": "text",
            "text": f"\n{'='*50}\nIMAGE {idx} of {len(images_data)}: {img_data['filename']}\n{'='*50}"
        })
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}",
                "detail": "high"
            }
        })
    
    content.append({
        "type": "text",
        "text": f"\n{'='*50}\nEND OF IMAGES - Extract all data\n{'='*50}"
    })

    try:
        print(f"   🤖 [{document_class}] Calling OpenAI {MODEL} with {len(images_data)} images...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]
        )
        
        elapsed = time.time() - start_time
        print(f"   ⏱️  [{document_class}] Completed in {elapsed:.1f} seconds")
        
        raw_response = response.choices[0].message.content
        
        # Parse response
        if "```json" in raw_response:
            json_start = raw_response.find("```json") + 7
            json_end = raw_response.find("```", json_start)
            json_str = raw_response[json_start:json_end].strip()
        elif "```" in raw_response:
            json_start = raw_response.find("```") + 3
            json_end = raw_response.find("```", json_start)
            json_str = raw_response[json_start:json_end].strip()
        else:
            json_str = raw_response
        
        result = json.loads(json_str)
        
        # Validate
        if document_class == "Packing List" and isinstance(result, list):
            ship_units = [item for item in result if item.get("doctype") == "Ship Unit"]
            print(f"   📊 [{document_class}] Extracted {len(ship_units)} Ship Units")
        
        # Wrap in metadata
        final_result = {
            'data': result if isinstance(result, list) else [result],
            '_metadata': {
                'document_class': document_class,
                'total_images_processed': len(images_data),
                'source_files': [img['filename'] for img in images_data],
                'extraction_method': 'batch_extraction',
                'model_used': MODEL,
                'processing_time_seconds': elapsed
            }
        }
        
        return final_result
        
    except json.JSONDecodeError as e:
        print(f"🚨 [{document_class}] JSON Parse Error: {e}")
        return {
            "error": f"JSON parsing failed: {str(e)}", 
            "document_class": document_class
        }
    except Exception as e:
        print(f"🚨 [{document_class}] Error: {e}")
        return {
            "error": str(e), 
            "document_class": document_class
        }

# ==================================================
# PROCESS SINGLE CLASS
# ==================================================
def process_class_directory(class_dir, document_class):
    """Process all images in a class directory."""
    image_files = [f for f in class_dir.iterdir() if f.is_file() and f.suffix.lower() == '.png']
    
    if not image_files:
        print(f"   ⚠️  [{document_class}] No PNG files found")
        return None
    
    print(f"   📁 [{document_class}] Found {len(image_files)} PNG file(s)")
    
    images_data = []
    for img_file in sorted(image_files):
        image = load_image(img_file)
        if image is not None:
            images_data.append({
                'image': image, 
                'filename': img_file.name, 
                'filepath': str(img_file)
            })
    
    if not images_data:
        print(f"   ❌ [{document_class}] No images loaded")
        return None
    
    print(f"   📸 [{document_class}] Loaded {len(images_data)} image(s)")
    
    # Extract data
    return openai_extract_data_batch_vision(images_data, document_class)

# ==================================================
# PARALLEL PROCESSING
# ==================================================
def process_directory(base_directory=BASE_DIR):
    """Process all document classes in parallel."""
    base_path = Path(base_directory)

    if not base_path.exists():
        print(f"❌ Directory not found: {base_directory}")
        return

    print("🚀 Starting PARALLEL document processing")
    print(f"🤖 Using model: {MODEL}")
    print(f"📋 Processing {len(CLASSES)} document classes in parallel\n")

    start_time = time.time()

    # Prepare tasks
    tasks = []
    for document_class in CLASSES:
        class_dir = base_path / document_class
        if class_dir.exists():
            tasks.append((class_dir, document_class))
        else:
            print(f"⚠️  Skipping {document_class} - directory not found")

    if not tasks:
        print("❌ No document classes to process")
        return

    print(f"🔄 Processing {len(tasks)} classes in parallel...\n")

    # Process in parallel using ThreadPoolExecutor
    # Deploying cloud 32gb ram instances 
    # time
    all_results = {}
    total_images_processed = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_class = {
            executor.submit(process_class_directory, class_dir, doc_class): doc_class
            for class_dir, doc_class in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_class):
            document_class = future_to_class[future]

            try:
                result = future.result()

                if result and not result.get("error"):
                    all_results[document_class] = result
                    num_images = result.get('_metadata', {}).get('total_images_processed', 0)
                    total_images_processed += num_images

                    # Save individual result
                    output_path = Path(OUTPUT_DIR) / document_class
                    output_path.mkdir(parents=True, exist_ok=True)
                    output_filename = f"{document_class.replace(' ', '_').lower()}_batch_result_{MODEL}.json"

                    with open(output_path / output_filename, 'w') as f:
                        json.dump(result, f, indent=2)

                    # Print statistics
                    if 'data' in result and isinstance(result['data'], list):
                        doctype_counts = {}
                        for item in result['data']:
                            dt = item.get('doctype', 'Unknown')
                            doctype_counts[dt] = doctype_counts.get(dt, 0) + 1

                        print(f"   ✅ [{document_class}] Extracted from {num_images} image(s)")
                        print(f"   📊 [{document_class}] DocTypes: {dict(doctype_counts)}")
                        print(f"   💾 [{document_class}] Saved: {output_filename}\n")
                    else:
                        print(f"   ✅ [{document_class}] Completed")
                        print(f"   💾 [{document_class}] Saved: {output_filename}\n")

                elif result and result.get("error"):
                    print(f"   ❌ [{document_class}] Error: {result['error']}\n")
                    all_results[document_class] = result

            except Exception as e:
                print(f"   🚨 [{document_class}] Exception: {str(e)}\n")
                all_results[document_class] = {
                    "error": str(e),
                    "document_class": document_class
                }

    # Save consolidated results
    consolidated_path = Path(OUTPUT_DIR) / "all_extracted_data.json"
    with open(consolidated_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    elapsed_total = time.time() - start_time

    print(f"\n{'='*60}")
    print("🎉 Parallel Processing Complete!")
    print(f"{'='*60}")
    print(f"📊 Classes processed: {len(all_results)}/{len(CLASSES)}")
    print(f"📸 Total images processed: {total_images_processed}")
    print(f"⏱️  Total time: {elapsed_total:.1f} seconds ({elapsed_total/60:.1f} minutes)")
    print(f"💾 Results saved to: {OUTPUT_DIR}")
    print(f"📄 Consolidated file: {consolidated_path}")
    print(f"{'='*60}\n")

    # Summary by class
    print("📋 Summary by Document Class:")
    for doc_class, result in all_results.items():
        if result.get("error"):
            print(f"   ❌ {doc_class}: ERROR - {result['error']}")
        else:
            metadata = result.get('_metadata', {})
            images = metadata.get('total_images_processed', 0)
            time_taken = metadata.get('processing_time_seconds', 0)
            print(f"   ✅ {doc_class}: {images} images in {time_taken:.1f}s")

# ==================================================
# RUN
# ==================================================
# if __name__ == "__main__":
#     process_directory(BASE_DIR)