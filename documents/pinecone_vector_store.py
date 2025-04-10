from pinecone import Pinecone, ServerlessSpec
from django.conf import settings
import logging
import time
import backoff
from decouple import config

logger = logging.getLogger(__name__)


class PineconeVectorStore:
    def __init__(self):
        """Initialize Pinecone vector store"""
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=config('PINECONE_API_KEY'))
        self.index_name = config('PINECONE_INDEX_NAME')
        self.embedding_dimension = 1024  # Dimension for e5-base (update based on your model)
        self.embedding_model = "multilingual-e5-large"  # Default model

        # Ensure index exists
        self._ensure_index_exists()

        # Get index reference
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            # Check if index exists
            indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in indexes:
                logger.info(f"Creating index {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )

                # Wait for index to be ready
                while True:
                    index_info = self.pc.describe_index(self.index_name)
                    if index_info.status.get('ready'):
                        break
                    logger.info("Waiting for index to be ready...")
                    time.sleep(5)

                logger.info(f"Index {self.index_name} is ready")
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise

    def _get_user_namespace(self, user_id=None):
        """Get namespace for user-specific vectors"""
        if user_id:
            return f"user_{user_id}"
        return "global"

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def generate_embedding(self, text):
        """Generate embedding using Pinecone's inference service"""
        try:
            embedding_response = self.pc.inference.embed(
                model=self.embedding_model,
                inputs=[text],
                parameters={"input_type": "passage", "truncate": "END"}
            )
            return embedding_response[0]['values']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def add_document(self, chunk_id, text, user_id=None, metadata=None):
        """Add a single document to the index with generated embedding"""
        namespace = self._get_user_namespace(user_id)

        if metadata is None:
            metadata = {}

        # Add document ID to metadata
        metadata["chunk_id"] = str(chunk_id)

        # Generate embedding
        embedding = self.generate_embedding(text)

        # Upsert to Pinecone
        self.index.upsert(
            vectors=[(str(chunk_id), embedding, metadata)],
            namespace=namespace
        )

        return embedding

    def add_documents(self, chunk_ids, texts, user_id=None, metadatas=None):
        """Add multiple documents to the index with generated embeddings"""
        namespace = self._get_user_namespace(user_id)

        if metadatas is None:
            metadatas = [{} for _ in chunk_ids]

        # Generate embeddings in batch
        try:
            embeddings = []
            # Process in batches of 5 to avoid overloading the API
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.pc.inference.embed(
                    model=self.embedding_model,
                    inputs=batch_texts,
                    parameters={"input_type": "passage", "truncate": "END"}
                )
                embeddings.extend([emb['values'] for emb in batch_embeddings])

            # Prepare vector tuples (id, vector, metadata)
            vectors = []
            for i, (chunk_id, embedding) in enumerate(zip(chunk_ids, embeddings)):
                metadata = metadatas[i].copy()
                metadata["chunk_id"] = str(chunk_id)
                metadata["text"] = texts[i]  # Add the text content to metadata
                vectors.append((str(chunk_id), embedding, metadata))

            # Upsert in batches to avoid payload size limits
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)

            return embeddings
        except Exception as e:
            logger.error(f"Error batch processing documents: {e}")
            raise

    def search(self, query_text=None, query_embedding=None, top_k=5, user_id=None, filter_dict=None):
        """Search for similar documents using text or embedding"""
        namespace = self._get_user_namespace(user_id)

        # Generate embedding if text is provided
        if query_text and not query_embedding:
            query_embedding = self.generate_embedding(query_text)

        if not query_embedding:
            raise ValueError("Either query_text or query_embedding must be provided")

        # First try user-specific namespace if user_id
        if user_id:
            results = self.index.query(
                namespace=namespace,
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

            # If no results, fall back to global namespace
            if len(results['matches']) == 0:
                results = self.index.query(
                    namespace="global",
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict
                )
        else:
            # Search in global namespace
            results = self.index.query(
                namespace="global",
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

        # Format results as [(chunk_id, similarity, metadata)]
        formatted_results = []
        for match in results['matches']:
            chunk_id = match['metadata'].get("chunk_id")
            if chunk_id:
                formatted_results.append((
                    int(chunk_id),
                    float(match['score']),
                    match['metadata']
                ))

        return formatted_results

    def delete_document(self, chunk_id, user_id=None):
        """Delete a document from the index"""
        namespace = self._get_user_namespace(user_id)
        self.index.delete(ids=[str(chunk_id)], namespace=namespace)

    def delete_user_documents(self, user_id):
        """Delete all documents for a user"""
        namespace = self._get_user_namespace(user_id)

        # Get all vectors in the namespace (may need pagination for large collections)
        fetch_response = self.index.fetch(
            ids=[],
            namespace=namespace
        )

        if fetch_response and 'vectors' in fetch_response and fetch_response['vectors']:
            self.index.delete(
                ids=list(fetch_response['vectors'].keys()),
                namespace=namespace
            )