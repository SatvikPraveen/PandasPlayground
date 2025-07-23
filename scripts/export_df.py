# scripts/export_pdf.py

import subprocess
from pathlib import Path

# Define paths
notebook_path = Path("notebooks/09_reporting_exporting.ipynb")
output_path = Path("exports")
output_filename = "report_final.pdf"

# Ensure output directory exists
output_path.mkdir(parents=True, exist_ok=True)

# Export notebook as PDF using nbconvert
try:
    subprocess.run([
        "jupyter", "nbconvert",
        "--to", "pdf",
        "--output-dir", str(output_path),
        "--output", output_filename,
        str(notebook_path)
    ], check=True)

    print(f"✅ Successfully exported to {output_path / output_filename}")

except subprocess.CalledProcessError as e:
    print("❌ PDF export failed.")
    print("Reason:", e)
    print("Tip: Make sure xelatex or LaTeX is installed on your system.")
