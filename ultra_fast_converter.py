#!/usr/bin/env python3
"""
ULTRA-FAST PDF to Markdown Converter
Minimal processing for maximum speed (<5 minutes)
"""

import os
import subprocess
import re
from pathlib import Path
import time

def clean_filename(filename: str) -> str:
    """Convert PDF filename to clean markdown filename"""
    name = filename.replace('.pdf', '')
    name = re.sub(r'^[^-]+-\s*', '', name)  # Remove "Author - " prefix
    name = re.sub(r'\([^)]*\)', '', name)    # Remove parentheses content
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'[^\w\s-]', '', name)     # Remove special chars
    name = re.sub(r'[-\s]+', '-', name).lower()
    return f"{name}.md"

def ultra_fast_convert(input_dir: str, output_dir: str) -> dict:
    """Ultra-fast conversion with minimal processing"""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        return {"success": False, "error": f"Input directory not found: {input_dir}"}
    
    # Get PDF files
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        return {"success": False, "error": f"No PDF files found in {input_dir}"}
    
    print(f"📚 Found {len(pdf_files)} PDF files")
    for pdf in pdf_files:
        size = os.path.getsize(pdf) / (1024 * 1024)
        print(f"  • {pdf.name} ({size:.1f}MB)")
    
    # ULTRA-FAST marker command with minimal processing
    cmd = [
        "poetry", "run", "marker",
        str(input_path),
        "--output_dir", str(output_path),
        "--extract_images", "False",        # Skip image extraction
        "--force_ocr", "False",             # No OCR
        "--pdftext_workers", "1",           # Single worker
        "--disable_links", "True",          # Skip link processing
        "--DocumentProvider_disable_ocr", "True",  # Disable OCR completely
        "--TableProcessor_disable_tqdm", "True",   # Disable progress bars
        "--LayoutBuilder_disable_tqdm", "True",    # Disable progress bars
        "--LineBuilder_disable_tqdm", "True",      # Disable progress bars
        "--OcrBuilder_disable_tqdm", "True",       # Disable progress bars
        "--StructureBuilder_gap_threshold", "0.1",  # Faster structure detection
        "--DocumentProvider_pdftext_workers", "1",  # Single worker
        "--PdfProvider_pdftext_workers", "1"       # Single worker
    ]
    
    print(f"\n⚡ ULTRA-FAST conversion starting...")
    print(f"Command: {' '.join(cmd[:5])}...")  # Show first 5 args
    start_time = time.time()
    
    try:
        # Run marker with minimal processing
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Conversion completed in {processing_time:.1f}s")
            
            # Check outputs and rename
            converted_files = []
            for pdf_file in pdf_files:
                expected_output = output_path / f"{pdf_file.stem}.md"
                clean_name = clean_filename(pdf_file.name)
                final_output = output_path / clean_name
                
                if expected_output.exists():
                    if expected_output != final_output:
                        expected_output.rename(final_output)
                        print(f"📝 {pdf_file.name} → {clean_name}")
                    
                    output_size = final_output.stat().st_size
                    converted_files.append({
                        "input": pdf_file.name,
                        "output": clean_name,
                        "size": output_size
                    })
                else:
                    print(f"❌ Missing: {pdf_file.name}")
            
            return {
                "success": True,
                "processing_time": processing_time,
                "converted_files": converted_files,
                "total_files": len(pdf_files),
                "successful_files": len(converted_files)
            }
        else:
            print(f"❌ Failed: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Conversion took longer than 5 minutes")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Main ultra-fast conversion"""
    
    input_dir = Path("book pdf to md")
    output_dir = Path("book_markdown")
    
    print("⚡ ULTRA-FAST PDF to Markdown Converter")
    print("=" * 50)
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    output_dir.mkdir(exist_ok=True)
    
    # Convert with ultra-fast settings
    result = ultra_fast_convert(str(input_dir), str(output_dir))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 CONVERSION SUMMARY")
    print(f"{'='*60}")
    
    if result["success"]:
        print(f"✅ Success: {result['successful_files']}/{result['total_files']}")
        print(f"⏱️  Time: {result['processing_time']:.1f}s")
        
        for file_info in result["converted_files"]:
            print(f"  ✅ {file_info['input']} → {file_info['output']}")
        
        print(f"\n📁 Output: {output_dir.absolute()}")
    else:
        print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    main() 