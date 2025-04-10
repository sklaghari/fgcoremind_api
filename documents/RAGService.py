import logging
from typing import List, Dict, Any
from groq import Groq
from .pinecone_vector_store import PineconeVectorStore
from decouple import config

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        """Initialize the RAG service with vector store and LLM client"""
        self.vector_store = PineconeVectorStore()
        self.groq_client = Groq(api_key=config('GROQ_API_KEY'))
        self.model = config('GROQ_MODEL', default="llama3-70b-8192")  # Default model
        self.max_tokens = 4096
        self.temperature = 0.3
        self.top_k = 5  # Number of chunks to retrieve
        self.similarity_threshold = 0.7

    def retrieve_relevant_chunks(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from the vector store."""
        try:
            # Generate query embedding
            query_embedding = self.vector_store.generate_embedding(query)
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=self.top_k
            )

            filtered_results = [
                {
                    "chunk_id": chunk_id,
                    "similarity": similarity,
                    "metadata": metadata,
                    "content": metadata.get("text", "")  # Extract text content
                }
                for chunk_id, similarity, metadata in results
                if similarity >= self.similarity_threshold
            ]

            # Sort by similarity score (highest first)
            filtered_results.sort(key=lambda x: x["similarity"], reverse=True)

            return filtered_results
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {e}")
            return []

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a readable context for the model."""
        if not chunks:
            return ""  # No relevant information found

        context = ""
        for i, chunk in enumerate(chunks):
            doc_id = chunk["metadata"].get("document_id", "Unknown")
            title = chunk["metadata"].get("title", "Untitled")

            context += f"--- DOCUMENT {i + 1}: {title} (ID: {doc_id}) ---\n"
            context += chunk["content"] + "\n\n"

        return context

    def generate_response(self, query: str) -> str:
        """Generate a response using RAG when context is available, else use open-ended generation."""
        try:
            # Step 1: Retrieve relevant document chunks
            chunks = self.retrieve_relevant_chunks(query)

            # Step 2: Format chunks into context
            context = self.format_context(chunks)

            # Step 3: Construct messages dynamically
            messages = []
            system_message = "You are an AI assistant capable of answering general and document-based queries."
            messages.append({"role": "system", "content": system_message})

            if chunks:
                # If relevant information is found, use it
                user_message = f"""Use the following retrieved information to answer the question:\n\n
                {context}\n
                Question: {query}
                """
            else:
                # If no context is found, allow open-ended generation
                user_message = f"Answer the following question based on your general knowledge: {query}"

            messages.append({"role": "user", "content": user_message})

            # Step 4: Generate response using Groq API
            response = self.groq_client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I'm sorry, I encountered an error while processing your request. Technical details: {str(e)}"