import os
import chromadb
from atlassian import Confluence
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from apscheduler.schedulers.background import BackgroundScheduler
import boto3
import logging
import urllib3
import pdfplumber
import tempfile
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import os

# Configuration
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://yourinstance.atlassian.net")
PARENT_PAGE_ROOT_ID = os.getenv("PARENT_PAGE_ROOT_ID", "your_parent_page_id")  # Replace with root page ID
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "your_username")
CONFLUENCE_PASSWORD = os.getenv("CONFLUENCE_PASSWORD", "your_password")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CHROMA_PERSIST_DIR = "./chroma_db"
UPDATE_INTERVAL_MINUTES = 60  # Update every hour
OUTPUT_DIR = "./confluence_pdfs"  # Temporary directory for PDFs
LAST_SYNC_TIMESTAMP_FILE = "./last_sync_timestamp.txt"  # File to store last sync time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("confluence_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize Confluence client with username and password
confluence = Confluence(
    url=CONFLUENCE_URL,
    username=CONFLUENCE_USERNAME,
    password=CONFLUENCE_PASSWORD
)

# Initialize Bedrock client
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION
)

# Helper function to get child pages
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_child_pages(page_id):
    try:
        children = confluence.get_page_child_by_type(page_id, type="page")["results"]
        logger.info(f"Fetched {len(children)} child pages for page ID {page_id}")
        return children
    except Exception as e:
        logger.error(f"Failed to fetch child pages for page ID {page_id}: {str(e)}")
        raise  # Retry on failure

# Step 1: Fetch Confluence pages and export as PDFs with child pages starting from root ID
def fetch_confluence_pages():
    documents = []
    processed_page_ids = set()  # Avoid duplicate processing
    last_sync_timestamp = get_last_sync_timestamp()

    def process_page(page_id):
        if page_id in processed_page_ids:
            return
        processed_page_ids.add(page_id)

        try:
            page = confluence.get_page_by_id(page_id, expand="version")
            title = page.get("title", "Unknown Title")
            version = page["version"]["number"]
            last_updated = page["version"]["when"]
            if last_sync_timestamp and last_updated <= last_sync_timestamp:
                return  # Skip if not updated since last sync

            # Export page as PDF with retry
            pdf_export = export_page_with_retry(page_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=OUTPUT_DIR) as temp_file:
                temp_file.write(pdf_export)
                temp_file_path = temp_file.name

            # Extract text from PDF
            with pdfplumber.open(temp_file_path) as pdf:
                text = ""
                for page_num in range(len(pdf.pages)):
                    text += pdf.pages[page_num].extract_text() or ""

            # Create Document object
            doc = Document(
                page_content=text,
                metadata={
                    "page_id": page_id,
                    "version": version,
                    "last_updated": last_updated,
                    "title": title,
                    "source": f"{CONFLUENCE_URL}/wiki/spaces/{page.get('space', {}).get('key', 'unknown')}/pages/{page_id}"
                }
            )
            documents.append(doc)
            logger.info(f"Successfully processed page ID {page_id} (Title: {title})")

            # Process child pages recursively
            children = get_child_pages(page_id)
            for child in children:
                child_id = child["id"]
                process_page(child_id)

        except Exception as e:
            logger.error(f"Failed to process page ID {page_id} (Title: {title}): {str(e)}")
            return  # Skip to next page or child

    # Start with the root page
    process_page(PARENT_PAGE_ROOT_ID)
    update_last_sync_timestamp()
    logger.info(f"Fetched {len(documents)} pages from Confluence successfully")
    return documents

# Step 2: Retry logic for page export
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def export_page_with_retry(page_id):
    return confluence.export_page(page_id, "pdf")

# Step 3: Manage last sync timestamp
def get_last_sync_timestamp():
    try:
        if os.path.exists(LAST_SYNC_TIMESTAMP_FILE):
            with open(LAST_SYNC_TIMESTAMP_FILE, "r") as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.error(f"Error reading last sync timestamp: {str(e)}")
        return None

def update_last_sync_timestamp():
    try:
        with open(LAST_SYNC_TIMESTAMP_FILE, "w") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    except Exception as e:
        logger.error(f"Error updating last sync timestamp: {str(e)}")

# Step 4: Process and update ChromaDB
def update_chromadb(documents, vector_store):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(splits)} chunks")

    # Generate unique IDs for chunks
    ids = [f"{doc.metadata['page_id']}_{i}" for i, doc in enumerate(splits)]
    
    # Check existing documents in ChromaDB
    existing_docs = vector_store.get()
    existing_ids = set(existing_docs.get("ids", []))
    
    # Handle updates and deletions
    for doc_id in existing_ids:
        page_id = doc_id.split("_")[0]
        new_doc = next((d for d in documents if d.metadata["page_id"] == page_id), None)
        if not new_doc:
            vector_store.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id} from ChromaDB")
        else:
            existing_version = next(
                (meta["version"] for meta, id_ in zip(existing_docs["metadatas"], existing_docs["ids"]) if id_ == doc_id),
                0
            )
            if new_doc.metadata["version"] > existing_version:
                vector_store.delete(ids=[doc_id])
                logger.info(f"Marked outdated document {doc_id} for update")

    # Add new or updated documents
    vector_store.add_documents(documents=splits, ids=ids)
    logger.info("Updated ChromaDB with new/updated documents")

# Step 5: Initialize ChromaDB
def initialize_and_update_chromadb():
    embeddings = BedrockEmbeddings(
        client=bedrock_client,
        model_id="amazon.titan-embed-text-v2:0"
    )
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    vector_store = Chroma(
        client=client,
        collection_name="confluence_data",
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    documents = fetch_confluence_pages()
    if documents:
        update_chromadb(documents, vector_store)
    return vector_store

# Step 6: Schedule periodic updates
def start_update_scheduler(vector_store):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: update_chromadb(fetch_confluence_pages(), vector_store),
        "interval",
        minutes=UPDATE_INTERVAL_MINUTES
    )
    scheduler.start()
    logger.info(f"Started scheduler for updates every {UPDATE_INTERVAL_MINUTES} minutes")

# Main execution
def main():
    vector_store = initialize_and_update_chromadb()
    start_update_scheduler(vector_store)
    logger.info("Confluence to ChromaDB sync initialized and running")

if __name__ == "__main__":
    main()