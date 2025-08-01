import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from pinecone import Pinecone, ServerlessSpec
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Configuration from environment variables with defaults
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "offer-letter-index")
CLOUD_PROVIDER = os.getenv("PINECONE_CLOUD", "aws")
REGION = os.getenv("PINECONE_REGION", "us-west-2")

def get_vectorstore(docs=None):
    """
    Initialize and return a Pinecone vector store with HuggingFace embeddings.
    
    Args:
        docs (list, optional): List of documents to embed and store if creating a new index.
    
    Returns:
        LangchainPinecone: The initialized vector store.
    
    Raises:
        ValueError: If required environment variables are missing or docs are not provided for new index.
        ConnectionError: If Pinecone connection fails.
        RuntimeError: For other initialization errors.
    """
    try:
        # Initialize embeddings for vector storage
        embed = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        logger.info("HuggingFaceEmbeddings initialized successfully for vector storage with model: all-MiniLM-L6-v2")
        
        # Get embedding dimension dynamically
        sample_embedding = embed.embed_query("sample text")
        dimension = len(sample_embedding)
        logger.info(f"Embedding dimension detected: {dimension}")

        # Initialize Pinecone client
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        pc = Pinecone(api_key=api_key)
        logger.info("Pinecone client initialized successfully")

        # Check if index exists
        existing_indexes = [index.name for index in pc.list_indexes()]
        if INDEX_NAME not in existing_indexes:
            if docs is None:
                raise ValueError(f"Docs required to initialize a new index: {INDEX_NAME}")
            logger.info(f"Creating new Pinecone index: {INDEX_NAME} with dimension {dimension}")
            pc.create_index(
                name=INDEX_NAME,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=CLOUD_PROVIDER, region=REGION)
            )
            logger.info(f"Index {INDEX_NAME} created successfully")
            return LangchainPinecone.from_texts(docs, embed, index_name=INDEX_NAME)
        else:
            logger.info(f"Loading existing Pinecone index: {INDEX_NAME}")
            return LangchainPinecone.from_existing_index(INDEX_NAME, embed)

    except ValueError as ve:
        logger.error(f"Validation error in get_vectorstore: {str(ve)}")
        raise
    except ConnectionError as ce:
        logger.error(f"Connection error with Pinecone: {str(ce)}")
        raise
    except Exception as e:
        logger.error(f"Failed to get vectorstore: {str(e)}")
        raise RuntimeError(f"Vectorstore initialization failed: {str(e)}")
