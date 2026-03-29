import os
import fitz  # PyMuPDF, still needed for splitting the PDF
import json
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageOps # Import PIL for image processing
import pytesseract
from vision import process_directory

load_dotenv()

# ==================================================
# CONFIG
# ==================================================
PDF_PATH = "../data/InfrabuildTest invoice-3.pdf"
OUTPUT_DIR = "classified_pages"
MAX_WORDS = 50000000
DPI = 300
CLASSES = [
    "Packing List",
    "Commercial Invoice",
    "Package Declaration",
    "Import Declaration",
    "Tax Invoice",
    "Bill of Lading",
    "Certificate of Origin",
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

os.makedirs(OUTPUT_DIR, exist_ok=True)
for c in CLASSES:
    os.makedirs(os.path.join(OUTPUT_DIR, c), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "Unclassified"), exist_ok=True)

# ==================================================
# IMAGE PREPROCESSING & TEXT EXTRACTION
# ==================================================
def preprocess_image(image_obj):
    """
    Converts a PIL image object to grayscale to improve OCR accuracy.
    """
    return ImageOps.grayscale(image_obj)

def extract_text_from_image(img_path):
    """
    Extracts text using Tesseract OCR.
    """
    try:
        image = Image.open(img_path)
        text = pytesseract.image_to_string(image, config='--psm 1')
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""
  
def truncate_text(text, word_limit=MAX_WORDS):
    """Truncates text to a specified word limit."""
    words = text.split()
    return " ".join(words[:word_limit])

# ==================================================
# LLM CLASSIFICATION (No changes needed here)
# ==================================================
def classify_with_llm(ocr_text):
    """
    Classifies the extracted OCR text using an LLM.
    """
    system_prompt = f"""You are a professional document classifier specializing in trade and logistics documentation.

Your task: Classify OCR-extracted text from a PDF page into ONE category from the list below.

**Available Categories:**
{', '.join(CLASSES)}

**Classification Guidelines:**

1. Tax Invoice
   - Primary key (must have at least one):
   - “Tax Invoice”, “Tax Invoice No.”, “ABN”, “GST”, “Amount Due”, “Total (inc. GST)”, “Invoice Date”
   - Negative key (if present → NOT Tax Invoice):
   - “Bill of Lading”, “BL#”, “Vessel”, “Voyage”, “Port of Loading”, “Consignee”, “HS Code”
   - Extra signals: currency symbol in $ or AUD, payment terms “EFT”, “BSB”, bank account, line items with “Qty” and unit price, final total ends in “.00”.

2. Commercial Invoice
   - Primary key (must have at least one):
   - “Commercial Invoice”, “Pro-forma Invoice”, “BL#”, “Bill of Lading”, “Vessel”, “Voyage No.”, “Port of Loading”, “Port of Discharge”, “Consignee”, “Shipper”, “Incoterm” (FOB, CIF, EXW), “HS Code”, “Country of Origin”
   - Negative key (if present → NOT Commercial Invoice):
   - “Tax Invoice”, “GST”, “ABN”, “Amount Due”, “Payment Due Date”
   - Extra signals: value shown in USD/EUR, freight charges, insurance, gross/net weight, packages counted in “CTNS”.

3. Bill of Lading
   - Primary key (any one):
   - “Bill of Lading”, “B/L No.”, “FIRST ORIGINAL”, “SECOND ORIGINAL”, “THIRD ORIGINAL”, “Carrier”, “Vessel Name”, “Freight Charges”, “Notify Party”
   - Negative key: “Tax Invoice”, “GST”, “Amount Due”
   - Extra signals: container ID regex [A-Z]{4}\d{7}, booking number, “Shipped on Board”, “Freight Prepaid / Collect”.

4. **Certificate of Origin**
   - Keywords: "Certificate of Origin", "Country of Origin", "Exporter", "Authorized Signature", "Chamber of Commerce"
   - Indicators: Declaration statements, official stamps/seals mentioned, certification date
   - Purpose: Document certifying where goods were manufactured/produced

5. **Packing List**
   - Keywords: "Packing List", "Container No", "Carton", "Gross Weight", "Net Weight", "Dimensions"
   - Indicators: Multiple container IDs, UOM (units of measure), quantity breakdowns, package counts
   - Purpose: Detailed inventory of shipped items and packaging

6. **Package Declaration**
   - Keywords: "Package Declaration", "Declared Value", "Contents Description", "Sender/Recipient"
   - Indicators: Customs declaration checkbox, signature line, "I hereby certify"
   - Purpose: Postal/courier customs declaration form

7. **Import Declaration**
   - Keywords: "Import Declaration", "Customs Entry", "Duty", "Tariff", "Broker", "Entry Number"
   - Indicators: HS codes with duty rates, customs broker details, clearance authorization
   - Purpose: Official customs clearance document

**Classification Rules:**
- Analyze the document structure, keywords, and purpose
- If multiple categories seem applicable, choose the PRIMARY purpose
- Consider document headers and titles as strong indicators
- Look for official formatting and reference numbers
- If confidence is low or text is unclear/incomplete, classify as "Unclassified"

**Response Format (JSON only):**
{{
  "class": "<one of {', '.join(CLASSES)} or Unclassified>",
  "reason": "<concise justification in 1-2 sentences, max 50 words>"
}}"""

    user_prompt = f"""Classify the following OCR-extracted text (first {MAX_WORDS} words):

---
{ocr_text}
---

Provide your classification as a JSON object."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"🚨 LLM Error: {e}")
        return {"class": "Unclassified", "reason": "LLM API call or JSON parsing failed."}


# ==================================================
# MAIN PIPELINE
# ==================================================
def classify_pdf(pdf_path=PDF_PATH):
    """
    Main pipeline that preprocesses, OCRs, classifies, and saves PDF pages.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at {pdf_path}")
        return

    try:
        doc = fitz.open(pdf_path)
    except fitz.errors.FitzError as e:
        print(f"❌ Error opening PDF with PyMuPDF: {e}")
        return
        
    print(f"🚀 Starting classification for '{os.path.basename(pdf_path)}'...")
    
    print(f"Converting PDF to images at {DPI} DPI...")
    images = convert_from_path(pdf_path, dpi=DPI)
    print(f"Found {len(images)} pages.")

    for i, image in enumerate(images, start=1):
        print(f"\n---- Processing Page {i} ----")
        
        # 1. Preprocess the image (convert to grayscale)
        print("Preprocessing image (converting to grayscale)...")
        processed_image = preprocess_image(image)
        
        img_path = f"/tmp/page_{i}_processed.png"
        processed_image.save(img_path, "PNG")
        
        # 2. Extract text using the OCR-only function
        print("Extracting text with Pytesseract...")
        text = extract_text_from_image(img_path)
        os.remove(img_path) 
        
        if not text.strip():
            print("⚠️ No text found by OCR on this page.")
            text = "empty OCR text"

        truncated = truncate_text(text)
      #   print(f"OCR Preview: {truncated}...")
        
        # 3. Classify using the LLM
        print("Classifying with LLM...")
        result = classify_with_llm(truncated)
        label = result.get("class", "Unclassified")
        reason = result.get("reason", "No reason provided.")
        
        dest_dir_name = label if label in CLASSES else "Unclassified"
        dest_dir      = os.path.join(OUTPUT_DIR, dest_dir_name)
        os.makedirs(dest_dir, exist_ok=True)

        out_img_path = os.path.join(dest_dir, f"page_{i:03d}.png")
        processed_image.save(out_img_path, "PNG")
        print(f"✅ Page {i:02d}: Saved to '{dest_dir_name}' | Reason: {reason}")

    doc.close()
    print(f"\n🎉 Classification complete. Files are saved in the '{OUTPUT_DIR}' directory.")

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    classify_pdf()
    process_directory(OUTPUT_DIR)