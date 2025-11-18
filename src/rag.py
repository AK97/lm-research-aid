from chromadb import Client
from google import genai
from src._private import GEMINI_API_KEY
from src.helpers import doc2text, text2chunks, build_prompt

class RAG_Handler:
    def __init__(self):
        # Init Gemini client
        self.llm = genai.Client(api_key = GEMINI_API_KEY)

        # Init Database (ChromaDB)
        self.db = Client()
        self.refresh()

        self.document_list = []

    def refresh(self) -> None:
        '''
        Clear db
        '''
        try:
            self.db.delete_collection("pdf_docs")
            self.collection = self.db.create_collection(name="pdf_docs")
        except:
            self.collection = self.db.create_collection(name="pdf_docs")

    def embed_docs(self, documents:list) -> None:
        for doc in documents:
            file_name = doc.name
            text = doc2text(doc)
            chunks = text2chunks(text)

            ids = [f"{file_name}_{num}" for num in range(len(chunks))]

            # Embed (note: 100 max batch)
            embedded_content = []
            MAX_BATCH_SIZE = 100
            for c in range(0, len(chunks), MAX_BATCH_SIZE):
                embedded_content_batch = self.llm.models.embed_content(
                    model="text-embedding-004",
                    contents=[{"parts": [{"text": chunk}]} for chunk in chunks[c:c+MAX_BATCH_SIZE]],
                )
                embedded_content += [ecbe.values for ecbe in embedded_content_batch.embeddings]

            # Update DB
            self.collection.add(
                ids = ids,
                documents = chunks,
                embeddings = embedded_content,
                metadatas = [{"source": file_name}] * len(chunks)
            )
    
    def retrieve_top(self, prompt:str) -> list:
        TOP_K = 10

        # Embed user input
        embedded_input = self.llm.models.embed_content(
            model="text-embedding-004",
            contents=[{"parts": [{"text": prompt}]}],
        )

        # Get closest matches
        top_results = self.collection.query(
            query_embeddings = embedded_input.embeddings[0].values,
            n_results = TOP_K,
        )

        # top_results["documents"] == [[]]
        chunks = top_results["documents"][0]
        sources = top_results["metadatas"][0]
        return list(zip(chunks, sources))
    
    def get_ai_response(self, prompt:str, documents:list) -> str:
        # Check if any documents have been uploaded
        if documents == []:
            return "No source material has been uploaded. Please upload some documents to discuss them."
        
        # Check if documents have been changed since last query
        elif documents != self.document_list:
            self.refresh()
            self.embed_docs(documents)
        
        context_chunks = self.retrieve_top(prompt)
        system_msg, user_msg = build_prompt(prompt, context_chunks)

        response = self.llm.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {"role": "model", "parts": [{"text": system_msg}]},
                {"role": "user", "parts": [{"text": user_msg}]},
            ]
        )
        
        return response.text