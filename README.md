# Agentic Study Aid
NotebookLM-inspired Streamlit app that lets you upload PDFs, embeds them with Google Gemini, and chats with a retrieval-augmented generation (RAG) workflow.

## Features
- Upload one or more PDFs and extract text with `pypdf`.
- Chunk documents with overlap, embed via `text-embedding-004`, and store vectors in a Chroma collection.
- Retrieve top matches per question and generate answers with `gemini-2.5-flash`, citing sources.
- Simple chat UI built with Streamlit.

## Requirements
- Google Gemini API key.

## Setup
1) Install dependencies (consider a virtualenv):
```
pip install -r requirements.txt
```
2) Provide your Gemini key in `src/_private.py`:
```python
# src/_private.py
GEMINI_API_KEY = "your-key-here"
```

## Run
```
streamlit run page.py
```

## Usage
- Upload PDFs in the right-hand panel; they are embedded on first use or when uploads change.
- Ask questions in the chat box; responses cite the file each chunk came from.
- The Chroma collection is cleared when uploads change (see `RAG_Handler.refresh()` in `src/rag.py`).

## Project Structure
- `page.py`: Streamlit UI wiring chat + uploads.
- `src/rag.py`: RAG pipeline (embed, store, retrieve, generate).
- `src/helpers.py`: PDF-to-text, chunking, and prompt construction utilities.

## Notes
- Chroma is used in-memory by default; data resets between runs.
