from PyPDF2 import PdfReader

def load_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        raise RuntimeError(f"Failed to load PDF {filepath}: {str(e)}")
