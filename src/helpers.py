from pypdf import PdfReader

def doc2text(pdf) -> str:
    '''document will be of type streamlit.UploadedFile'''
    reader = PdfReader(pdf)
    pages = [page.extract_text() or "" for page in reader.pages]
    content = "\n".join(pages)
    return content

def text2chunks(text:str) -> list:
    '''
    Returns list of str
    '''
    MAX_CHARS = 1000
    OVERLAP = 200
    chunks = []

    start = 0
    while start < len(text):
        end = start + MAX_CHARS
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - OVERLAP

    return chunks

def build_prompt(prompt:str, context_chunks):
    '''Returns (system message, user_message)'''
    context_text = "\n\n---\n\n".join(
        [f"Source: {m['source']}\n{c}" for c, m in context_chunks]
    )
    system_msg = (
        "You are a helpful assistant that answers questions and engages in productive dialog using the provided context as much as possible."
        "If something is not in the context, answer with other knowledge sources, but be sure to mention that is happening."
        "If it is relevant, you can utilize information from other sources to improve your answer, but be sure to mention where each piece of information is coming from."
    )
    user_msg = (
        f"Context:\n{context_text}\n\n"
        f"User question: {prompt}\n\n"
        "Answer thoroughly and always cite every source with parentheses."
    )
    return system_msg, user_msg