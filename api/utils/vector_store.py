import os
import pickle
import numpy as np
import faiss
from typing import List
from django.conf import settings


class VectorStoreManager:
    """
    Manage FAISS vector store for document embeddings
    """
    
    def __init__(self):
        self.vector_store_dir = os.path.join(settings.MEDIA_ROOT, 'vector_stores')
        os.makedirs(self.vector_store_dir, exist_ok=True)

    def create_vector_store(self, text_chunks: List[str], document_id: int) -> str:
        """
        Create a FAISS vector store from text chunks
        """
        try:
            # Create embeddings (using simple TF-IDF-like approach for demo)
            # In production, use proper embeddings (OpenAI, SentenceTransformers, etc.)
            embeddings = self._create_embeddings(text_chunks)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)

            # Save vector store
            doc_vector_dir = os.path.join(self.vector_store_dir, str(document_id))
            os.makedirs(doc_vector_dir, exist_ok=True)

            index_path = os.path.join(doc_vector_dir, 'index.faiss')
            chunks_path = os.path.join(doc_vector_dir, 'chunks.pkl')

            faiss.write_index(index, index_path)
            
            with open(chunks_path, 'wb') as f:
                pickle.dump(text_chunks, f)

            return index_path

        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise

    def search_similar(self, index_path: str, query: str, k: int = 3) -> List[str]:
        """
        Search for similar chunks in the vector store
        """
        try:
            # Load index and chunks
            index = faiss.read_index(index_path)
            
            chunks_path = index_path.replace('index.faiss', 'chunks.pkl')
            with open(chunks_path, 'rb') as f:
                chunks = pickle.load(f)

            # Create query embedding
            query_embedding = self._create

            # Search
            distances, indices = index.search(query_embedding, k)

            # Return top k chunks
            similar_chunks = [chunks[idx] for idx in indices[0] if idx < len(chunks)]
            
            return similar_chunks

        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []

    def _create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create simple embeddings (TF-IDF-like)
        For production, use OpenAI embeddings or SentenceTransformers
        """
        # This is a simplified version for demo purposes
        # In production, use proper embeddings like:
        # - OpenAI: openai.Embedding.create()
        # - SentenceTransformers: model.encode()
        
        from collections import Counter
        
        # Create vocabulary
        all_words = []
        for text in texts:
            words = text.lower().split()
            all_words.extend(words)
        
        vocab = list(set(all_words))
        vocab_size = min(len(vocab), 384)  # Limit vocabulary size
        vocab = vocab[:vocab_size]
        word_to_idx = {word: idx for idx, word in enumerate(vocab)}
        
        # Create embeddings
        embeddings = np.zeros((len(texts), vocab_size))
        
        for i, text in enumerate(texts):
            words = text.lower().split()
            word_counts = Counter(words)
            
            for word, count in word_counts.items():
                if word in word_to_idx:
                    embeddings[i, word_to_idx[word]] = count
        
        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        return embeddings.astype('float32')