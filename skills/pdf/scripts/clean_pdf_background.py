#!/usr/bin/env python3
"""Clean background noise from scanned PDF documents."""
import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import numpy as np


def analyze_image(image_path):
    """Analyze if image needs processing."""
    img = Image.open(image_path)
    arr = np.array(img)
    
    if len(arr.shape) == 3:
        brightness = np.mean(arr, axis=2)
    else:
        brightness = arr
    
    bg_percentile_95 = np.percentile(brightness, 95)
    bg_percentile_98 = np.percentile(brightness, 98)
    
    bg_is_white = bg_percentile_95 > 250
    bg_is_clean = bg_percentile_98 > 253
    needs_processing = not (bg_is_white and bg_is_clean)
    
    return needs_processing


def clean_image(input_path, output_path):
    """Clean background noise while preserving color content."""
    needs_processing = analyze_image(input_path)
    
    if not needs_processing:
        shutil.copy(input_path, output_path)
        return False
    
    cmd = ["convert", input_path,
           "-level", "0%,92%,1.0",
           "-white-threshold", "92%",
           output_path]
    
    subprocess.run(cmd, check=True)
    return True


def clean_pdf(input_pdf, output_pdf, dpi=300):
    """Clean background noise from all pages of a PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        print(f"Converting PDF to images (DPI: {dpi})...")
        subprocess.run([
            "pdftoppm", "-png", "-r", str(dpi), input_pdf,
            str(tmpdir / "page")
        ], check=True)
        
        image_files = sorted(tmpdir.glob("page-*.png"))
        print(f"Processing {len(image_files)} pages...")
        
        processed_count = 0
        for i, img_file in enumerate(image_files, 1):
            cleaned_file = tmpdir / f"cleaned-{i:04d}.png"
            was_processed = clean_image(str(img_file), str(cleaned_file))
            if was_processed:
                processed_count += 1
            print(f"  Page {i}/{len(image_files)}: {'processed' if was_processed else 'skipped (good quality)'}")
        
        print(f"\nConverting images back to PDF...")
        cleaned_images = sorted(tmpdir.glob("cleaned-*.png"))
        
        subprocess.run([
            "convert",
            *[str(f) for f in cleaned_images],
            output_pdf
        ], check=True)
        
        print(f"Done! Processed {processed_count}/{len(image_files)} pages")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clean_pdf_background.py <input.pdf> <output.pdf> [dpi]")
        print("  dpi: Resolution for processing (default: 300)")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    
    clean_pdf(input_pdf, output_pdf, dpi)
