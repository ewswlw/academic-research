"""
Extract all text from a PDF using pdfplumber.
- Source: Detecting Multivarite market regimes via a clustering algo.pdf
- Output: Prints and saves extracted text to a .txt file.
- Handles errors and logs progress for reproducibility.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

try:
    import pdfplumber
except ImportError:
    logging.error("pdfplumber not found. Please install it with 'poetry add pdfplumber'.")
    print("ERROR: pdfplumber is not installed. Run 'poetry add pdfplumber' and try again.")
    sys.exit(1)

PDF_PATH = "Academic Research/Detecting Multivarite market regimes via a clustering algo.pdf"
TXT_PATH = "Academic Research/Detecting Multivarite market regimes via a clustering algo.txt"

if not os.path.exists(PDF_PATH):
    logging.error(f"PDF file not found: {PDF_PATH}")
    print(f"ERROR: PDF file not found: {PDF_PATH}")
    sys.exit(2)

all_text = []
try:
    with pdfplumber.open(PDF_PATH) as pdf:
        logging.info(f"Opened PDF: {PDF_PATH} with {len(pdf.pages)} pages.")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                all_text.append(text)
                logging.info(f"Extracted text from page {i+1}/{len(pdf.pages)}.")
            else:
                logging.warning(f"No extractable text found on page {i+1}.")
    full_text = '\n\n'.join(all_text)
    print("\n--- Extracted PDF Text Start ---\n")
    print(full_text)
    print("\n--- Extracted PDF Text End ---\n")
    with open(TXT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_text)
    logging.info(f"Saved extracted text to {TXT_PATH}.")
except Exception as e:
    logging.exception("Failed to extract text from PDF.")
    print(f"ERROR: Exception occurred during extraction: {e}")
    sys.exit(3)

print("PDF text extraction completed successfully.")
