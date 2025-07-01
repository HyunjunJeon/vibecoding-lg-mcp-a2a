You're implementing a REST API for a RAG system.
You are to use FastAPI and LangChain.

Below are instructions on all of the different endpoints you need to implement.

# API Endpoint Definitions

## Collections

Manage vector store collections.

- POST /collections
  - Creates a new collection.
  - Request Body: JSON containing collection details (e.g., {'name': 'my_collection'}).
  - Response: Details of the created collection or confirmation.

- GET /collections
  - Lists all available collections.
  - Response: List of collection identifiers or objects.

- GET /collections/{collection_id}
  - Retrieves details of a specific collection.
  - Path Parameter: collection_id - The ID of the collection to retrieve.
  - Response: Details of the specified collection.

- PUT /collections/{collection_id}
  - Updates/replaces an existing collection (e.g., rename).
  - Path Parameter: collection_id - The ID of the collection to update.
  - Request Body: JSON containing the full updated collection details.
  - Response: Details of the updated collection.

- PATCH /collections/{collection_id}
  - Partially updates an existing collection.
  - Path Parameter: collection_id - The ID of the collection to update.
  - Request Body: JSON containing the specific fields to update.
  - Response: Details of the updated collection.

- DELETE /collections/{collection_id}
  - Deletes a specific collection.
  - Path Parameter: collection_id - The ID of the collection to delete.
  - Response: Confirmation of deletion.

## Documents (within Collections)

Manage documents within a specific collection (RAG functionality).

- POST /collections/{collection_id}/documents
  - Indexes (adds) a new document to the specified collection.
  - Path Parameter: collection_id - The ID of the collection to add the document to.
  - Request Body: The document data to be indexed.
  - Response: Identifier or details of the indexed document.

- GET /collections/{collection_id}/documents
  - Lists all documents within a specific collection.
  - Path Parameter: collection_id - The ID of the collection.
  - Query Parameters (Optional):
    - query={search_terms}: Filter documents based on search terms.
    - limit={N}: Limit the number of results.
    - offset={M}: Skip the first M results (for pagination).
  - Response: List of document identifiers or objects within the collection.

- GET /collections/{collection_id}/documents/{document_id}
  - Retrieves a specific document from a collection.
  - Path Parameters:
    - collection_id: The ID of the collection.
    - document_id: The ID of the document to retrieve.
  - Response: The content or details of the specified document.

- PUT /collections/{collection_id}/documents/{document_id}
  - Updates/replaces an existing document in a collection.
  - Path Parameters:
    - collection_id: The ID of the collection.
    - document_id: The ID of the document to update.
  - Request Body: The full updated document data.
  - Response: Details of the updated document.

- PATCH /collections/{collection_id}/documents/{document_id}
  - Partially updates an existing document in a collection.
  - Path Parameters:
    - collection_id: The ID of the collection.
    - document_id: The ID of the document to update.
  - Request Body: JSON containing the specific fields/parts of the document to update.
  - Response: Details of the updated document.

- DELETE /collections/{collection_id}/documents/{document_id}
  - Deletes a specific document from a collection.
  - Path Parameters:
    - collection_id: The ID of the collection.
    - document_id: The ID of the document to delete.
  - Response: Confirmation of deletion.

- POST /collections/{collection_id}/documents/search (Alternative Search)
  - Performs a search within a specific collection using potentially complex criteria.
  - Use this if GET with query parameters is insufficient (e.g., requires a request body).
  - Path Parameter: collection_id - The ID of the collection to search within.
  - Request Body: JSON containing search criteria.
  - Response: List of matching documents.

## LangChain Integration

Please setup this application with LangChain document loaders, text splitters and vector stores.

### Document Loaders

You should use the `UploadFile` type from FastAPI for the inputs to the API for uploading documents. Then, use the `Blob` class from `langchain_core.documents` to load the uploaded file as a blob.
Finally, use the `MimeTypeBasedParser` from `langchain_community.document_loaders.parsers.generic` to parse the blob into a document. Here is some example code, and the types of documents you should support:

```python
from langchain_community.document_loaders.parsers import BS4HTMLParser, PDFMinerParser
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.txt import TextParser

HANDLERS = {
    "application/pdf": PDFMinerParser(),
    "text/plain": TextParser(),
    "text/html": BS4HTMLParser(),
    "application/msword": MsWordParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        MsWordParser()
    ),
}

SUPPORTED_MIMETYPES = sorted(HANDLERS.keys())

MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
    handlers=HANDLERS,
    fallback_parser=None,
)
```

### Text Splitters

For text splitting, you should use the `RecursiveCharacterTextSplitter` from `langchain_text_splitters`. Set the following parameters:
`chunk_size=1000, chunk_overlap=200`.

### Vector Stores

For the vector store, use the PGVector LangChain integration. For connection details, use environment variables. Import from the `langchain_postgres` package.

You should also use postgres to create collections, and fetch/search/delete/create collections.
