Tesseract OCR support

This backend includes an /ocr endpoint that accepts an image and returns extracted text using Tesseract OCR (pytesseract + Pillow).

Requirements
- Install system Tesseract binary (macOS):

  brew install tesseract

- Install Python dependencies (use a venv):

  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

How it works
- POST /ocr with multipart/form-data containing a file field named `image`.
  - Returns: { "text": "...extracted text..." }
- Alternatively POST JSON { "imageBase64": "data:image/png;base64,..." }

Frontend
- The web UI adds an "Upload image (OCR)" control and an Extract button that uploads the image, inserts the extracted text into the question textarea, and allows users to submit the question as usual.

Notes
- pytesseract is a Python wrapper and requires the Tesseract binary installed on the server. If it's missing the server will return an error message indicating pytesseract is not available.
