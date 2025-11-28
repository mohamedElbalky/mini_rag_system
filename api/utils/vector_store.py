import os
import pickle
import numpy as np
import faiss
from typing import List
from django.conf import settings
from google import genai

class VectorStoreManager:
    """
    Manage vector store creation and similarity search using FAISS and google-genai embeddings
    """
    
    def __init__(self):
        self.vector_store_dir = os.path.join(settings.MEDIA_ROOT, 'vector_stores')
        os.makedirs(self.vector_store_dir, exist_ok=True)
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.embedding_model = "text-embedding-004"

    def create_vector_store(self, text_chunks: List[str], document_id: int) -> str:
        """
        Create a vector store for the given text chunks and document ID.

        :param text_chunks: List of text chunks to embed
        :param document_id: Document ID to associate with the vector store
        :return: Path to the created vector store index file
        """
        if not text_chunks: return ""
        try:
            embeddings = self._create_embeddings(text_chunks, is_query=False)
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)

            doc_dir = os.path.join(self.vector_store_dir, str(document_id))
            os.makedirs(doc_dir, exist_ok=True)
            
            index_path = os.path.join(doc_dir, 'index.faiss')
            with open(os.path.join(doc_dir, 'chunks.pkl'), 'wb') as f:
                pickle.dump(text_chunks, f)
                
            faiss.write_index(index, index_path)
            return index_path
        except Exception as e:
            print(f"Error creating vector store: {e}")
            raise

    def search_similar(self, index_path: str, query: str, k: int = 3) -> List[str]:
        """
        Search for similar text chunks in the vector store.

        :param index_path: Path to the faiss index file
        :param query: Query string
        :param k: Number of nearest neighbors to retrieve (default=3)
        :return: List of similar text chunks
        """
        try:
            doc_dir = os.path.dirname(index_path)
            index = faiss.read_index(index_path)
            with open(os.path.join(doc_dir, 'chunks.pkl'), 'rb') as f:
                chunks = pickle.load(f)
            
            query_emb = self._create_embeddings([query], is_query=True)
            distances, indices = index.search(query_emb, k)
            return [chunks[i] for i in indices[0] if i < len(chunks)]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _create_embeddings(self, texts: List[str], is_query: bool) -> np.ndarray:
        """
        Create embeddings for a list of texts using the GemAI text-embedding-004 model
        
        Parameters:
        texts (List[str]): List of texts to embed
        is_query (bool): If True, use the RETRIEVAL_QUERY task type. Otherwise, use RETRIEVAL_DOCUMENT
        
        Returns:
        np.ndarray: A 2D numpy array of shape (len(texts), embedding_dim) containing the embeddings for each text
        """
        try:
            task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=texts,
                config={'task_type': task}
            )
            # Extract .values from the list of embedding objects
            if hasattr(result, 'embeddings'):
                return np.array([e.values for e in result.embeddings]).astype('float32')
            return np.array([])
        except Exception as e:
            print(f"Embedding error: {e}")
            return np.array([])