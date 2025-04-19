import pdfplumber
import os
import logging

# Set up logging for detailed debug output
logging.basicConfig(
    filename='extract_pdf_text.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_pdf_text(pdf_path, txt_path):
    """
    Extracts text from a PDF file using pdfplumber and saves it to a TXT file.
    Logs each step for debugging and reproducibility.
    """
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        print(f"ERROR: PDF file not found: {pdf_path}")
        return

    extracted_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logging.info(f"Opened PDF: {pdf_path}")
            print(f"Opened PDF: {pdf_path}")
            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                        logging.info(f"Extracted text from page {i+1}/{len(pdf.pages)}")
                        print(f"Extracted text from page {i+1}/{len(pdf.pages)}")
                    else:
                        logging.warning(f"No text found on page {i+1}")
                        print(f"WARNING: No text found on page {i+1}")
                except Exception as e:
                    logging.error(f"Error extracting page {i+1}: {e}")
                    print(f"ERROR: Could not extract page {i+1}: {e}")
        if not extracted_text:
            logging.error("No text extracted from PDF. PDF may be image-based or corrupted.")
            print("ERROR: No text extracted from PDF. PDF may be image-based or corrupted.")
            return
        # Write extracted text to TXT file
        with open(txt_path, 'w', encoding='utf-8') as f:
            for page_num, page_text in enumerate(extracted_text, 1):
                f.write(f"\n--- Page {page_num} ---\n")
                f.write(page_text)
                f.write("\n")
        logging.info(f"Extraction complete. Output saved to: {txt_path}")
        print(f"Extraction complete. Output saved to: {txt_path}")
    except Exception as e:
        logging.error(f"Failed to extract PDF: {e}")
        print(f"ERROR: Failed to extract PDF: {e}")

if __name__ == "__main__":
    # Relative paths for reproducibility
    pdf_path = os.path.join(os.path.dirname(__file__), 'Timing is Everything.pdf')
    txt_path = os.path.join(os.path.dirname(__file__), 'Timing_is_Everything.txt')
    extract_pdf_text(pdf_path, txt_path)
