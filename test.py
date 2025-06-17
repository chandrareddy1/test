import boto3
import pdfplumber
import re
import json
import io
import chromadb
from chromadb.config import Settings
from botocore.exceptions import ClientError
from langchain.text_splitter import RecursiveCharacterTextSplitter

# AWS setup
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
bucket_name = 'your-bucket-name'
prefix = 'path/to/pdfs/'  # Optional folder in bucket

# Initialize Chroma in-memory DB
chroma_client = chromadb.Client(Settings(persist_directory=None))  # In-memory
collection = chroma_client.create_collection(name="pdf_embeddings")

# Semantic text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=30000,  # ~4,000 tokens, conservative for Titan's 50,000-char limit
    chunk_overlap=200,  # Small overlap to preserve context
    separators=["\n\n", "\n", ". ", " ", ""],  # Split by paragraphs, sentences, etc.
    length_function=len
)

def generate_titan_embedding(text, model_id="amazon.titan-embed-text-v2:0", dimensions=1024, normalize=True):
    """Generate embeddings using Amazon Titan Text Embeddings V2."""
    try:
        body = json.dumps({
            "inputText": text,
            "dimensions": dimensions,
            "normalize": normalize
        })
        response = bedrock_client.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response['body'].read())
        return response_body['embedding']
    except ClientError as e:
        print(f"Error generating embedding: {e}")
        return None

def extract_urls(text):
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return re.findall(url_pattern, text)

def process_pdf(file_content, file_key):
    """Extract text, tables, and URLs from a PDF with semantic chunking."""
    chunks = []
    metadata = []
    
    # Load PDF from bytes
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text
            text = page.extract_text() or ""
            if text:
                # Apply semantic chunking
                text_chunks = text_splitter.split_text(text)
                for chunk in text_chunks:
                    chunks.append(chunk)
                    metadata.append({"file": file_key, "page": page_num + 1, "type": "text"})

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                table_text = "\n".join([",".join(row) for row in table if row])
                if table_text:
                    # Tables are treated as single chunks (no splitting needed)
                    chunks.append(table_text[:40000])  # Truncate if needed
                    metadata.append({"file": file_key, "page": page_num + 1, "type": "table"})

            # Extract URLs from text
            urls = extract_urls(text)
            for url in urls:
                chunks.append(url)
                metadata.append({"file": file_key, "page": page_num + 1, "type": "url"})

    return chunks, metadata

def main():
    # List PDF files in S3
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    pdf_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]

    for file_key in pdf_files:
        print(f"Processing {file_key}...")
        
        # Download PDF from S3
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = obj['Body'].read()
        except ClientError as e:
            print(f"Error downloading {file_key}: {e}")
            continue

        # Extract content
        try:
            chunks, metadata = process_pdf(file_content, file_key)
        except Exception as e:
            print(f"Error processing {file_key}: {e}")
            continue

        # Generate embeddings
        embeddings = []
        valid_chunks = []
        valid_metadata = []
        for chunk, meta in zip(chunks, metadata):
            embedding = generate_titan_embedding(chunk)
            if embedding:
                embeddings.append(embedding)
                valid_chunks.append(chunk)
                valid_metadata.append(meta)

        # Store in Chroma
        if embeddings:
            collection.add(
                embeddings=embeddings,
                documents=valid_chunks,
                metadatas=valid_metadata,
                ids=[f"{file_key}_chunk_{i}" for i in range(len(valid_chunks))]
            )

    print("All PDFs processed and embeddings stored.")

if __name__ == "__main__":
    main()