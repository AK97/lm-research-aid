from pypdf import PdfReader

def doc2text(pdf) -> str:
    '''document will be of type streamlit.UploadedFile'''
    reader = PdfReader(pdf)
    pages = [page.extract_text() or "" for page in reader.pages]
    content = "\n".join(pages)
    return content

def text2chunks(text: str) -> list:
    """
    Splits text into chunks, attempting to maintain semantic boundaries
    (paragraphs, sentences) and then combines them with overlap.
    """
    MAX_CHARS = 1000
    OVERLAP = 200
    
    # 1. Define common separators, ordered by preference
    # Prioritize paragraphs, then sentences, then words, then characters
    separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    # This helper will recursively split text based on separators
    def _split_by_separators(text_content, current_separators, max_len):
        if not text_content:
            return []
        if len(text_content) <= max_len:
            return [text_content]

        if not current_separators:
            # If no separators left, just split by max_len
            return [text_content[i:i + max_len] for i in range(0, len(text_content), max_len)]

        separator = current_separators[0]
        remaining_separators = current_separators[1:]

        # If the separator is empty string, we are at character level split
        if not separator:
            return [text_content[i:i + max_len] for i in range(0, len(text_content), max_len)]

        parts = text_content.split(separator)
        
        chunks = []
        current_chunk_buffer = ""

        for part in parts:
            # Check if adding the next part (and separator) exceeds max_len
            if len(current_chunk_buffer) + len(part) + len(separator) <= max_len:
                current_chunk_buffer += (separator if current_chunk_buffer else "") + part
            else:
                # current_chunk_buffer is too large or adding part would make it too large
                if current_chunk_buffer:
                    # Recursively split the current_chunk_buffer with the next separator
                    chunks.extend(_split_by_separators(current_chunk_buffer, remaining_separators, max_len))
                
                # Start a new buffer with the current part
                current_chunk_buffer = part

        # Add any remaining content in the buffer
        if current_chunk_buffer:
            chunks.extend(_split_by_separators(current_chunk_buffer, remaining_separators, max_len))
        
        return chunks

    # First pass: get chunks respecting semantic boundaries, trying to keep them under MAX_CHARS
    # These chunks might still be larger than MAX_CHARS if a single "part" (e.g., a very long sentence)
    # is itself longer than MAX_CHARS and no smaller separator exists.
    semantic_chunks = _split_by_separators(text, separators, MAX_CHARS)

    # Second pass: Combine semantic chunks with overlap to form final chunks
    final_chunks = []
    current_chunk = ""

    for chunk in semantic_chunks:
        if not current_chunk:
            current_chunk = chunk
        elif len(current_chunk) + len(chunk) + 1 <= MAX_CHARS: # +1 for a potential space/newline
            current_chunk += "\n" + chunk # Add a newline to separate combined semantic chunks
        else:
            final_chunks.append(current_chunk)
            # Create overlap: start new chunk with the end of the previous one
            overlap_content = current_chunk[-OVERLAP:] if len(current_chunk) > OVERLAP else current_chunk
            current_chunk = overlap_content + "\n" + chunk # Ensure overlap and add new chunk
    
    if current_chunk:
        final_chunks.append(current_chunk)

    # One final check to ensure no chunk exceeds MAX_CHARS due to overlap
    # If an overlapped chunk is too big, it will be split here without semantic consideration
    # This is a fallback to guarantee MAX_CHARS constraint
    result_with_max_len_guarantee = []
    for f_chunk in final_chunks:
        if len(f_chunk) > MAX_CHARS:
            start_idx = 0
            while start_idx < len(f_chunk):
                end_idx = min(start_idx + MAX_CHARS, len(f_chunk))
                result_with_max_len_guarantee.append(f_chunk[start_idx:end_idx])
                start_idx += MAX_CHARS - OVERLAP # This overlap is simple character-based
        else:
            result_with_max_len_guarantee.append(f_chunk)

    return result_with_max_len_guarantee

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