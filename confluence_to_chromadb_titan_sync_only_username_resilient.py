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

# Configuration
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://yourinstance.atlassian.net")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "YOUR_SPACE_KEY")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "your_username")
CONFLUENCE_PASSWORD = os.getenv("CONFLUENCE_PASSWORD", "your_password")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CHROMA_PERSIST_DIR = "./chroma_db"
UPDATE_INTERVAL_MINUTES = 60  # Update every hour

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

# Step 1: Fetch Confluence pages
def fetch_confluence_pages():
    documents = []
    start = 0
    limit = 100
    while True:
        try:
            # Fetch a batch of pages
            pages = confluence.get_all_pages_from_space(
                CONFLUENCE_SPACE_KEY,
                start=start,
                limit=limit,
                expand="version,body.storage",
                status="current"
            )
            if not pages:
                break  # No more pages to fetch

            # Process each page individually
            for page in pages:
                try:
                    page_id = page["id"]
                    content = page["body"]["storage"]["value"]
                    version = page["version"]["number"]
                    last_updated = page["version"]["when"]
                    title = page.get("title", "Unknown Title")
                    doc = Document(
                        page_content=content,
                        metadata={
                            "page_id": page_id,
                            "version": version,
                            "last_updated": last_updated,
                            "source": f"{CONFLUENCE_URL}/wiki/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}",
                            "title": title
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Failed to process page ID {page.get('id', 'unknown')} (Title: {page.get('title', 'unknown')}): {str(e)}")
                    continue  # Skip to the next page

            start += limit  # Move to the next batch
        except Exception as e:
            logger.error(f"Error fetching page batch (start={start}, limit={limit}): {str(e)}")
            break  # Stop if batch fetch fails

    logger.info(f"Fetched {len(documents)} pages from Confluence successfully")
    return documents

# Step 2: Process and update ChromaDB
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

# Step 3: Initialize ChromaDB
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

# Step 4: Schedule periodic updates
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