# Mini RAG System

## Project Description
This project implements a mini Retrieval-Augmented Generation (RAG) system, designed to process and query documents using a combination of Large Language Models (LLMs) and vector-based search. It provides a robust backend API for uploading PDF documents, processing them into a searchable vector store, and enabling real-time conversational queries via WebSockets.

## Features
-   **Document Upload**: API endpoint for uploading PDF documents.
-   **PDF Processing**: Extracts text from PDFs and chunks it for embedding.
-   **Vector Store Management**: Stores document embeddings for efficient similarity search.
-   **LLM Integration**: Utilizes LLMs for generating responses based on retrieved document chunks.
-   **Real-time Chat**: WebSocket interface for interactive querying of uploaded documents.

## Technologies Used
-   **Backend**: Python, Django, Django Rest Framework
-   **Asynchronous Processing**: Django Channels
-   **LLM Integration**: Custom `llm_handler` for interacting with Gemini model
-   **Vector Database**: Custom `vector_store` utility (likely relies on a library like FAISS implementation
-   **PDF Processing**: Custom `pdf_processor` utility (likely uses `PyPDF2` or `pdfminer.six`)
-   **Containerization**: Docker, Docker Compose
-   **WebSockets**: `channels_redis` for channel layer

## Architecture
The system is structured into several key components:

### 1. `api/` Application
-   **`views.py`**: Handles HTTP requests for document uploads and other API interactions using Django Rest Framework.
-   **`serializers.py`**: Defines how data is serialized and deserialized for API requests and responses.
-   **`models.py`**: Defines the database schema for storing information about uploaded documents.
-   **`utils/`**:
    -   **`llm_handler.py`**: Manages communication with external Large Language Models, responsible for sending prompts and receiving generated text.
    -   **`pdf_processor.py`**: Contains logic for extracting text from PDF files and preparing it for further processing (e.g., chunking).
    -   **`vector_store.py`**: Manages the creation, storage, and querying of document embeddings. This is where the RAG system's retrieval mechanism resides.
-   **`ws/`**:
    -   **`consumers.py`**: Handles WebSocket connections, receiving user queries, orchestrating the RAG process (retrieval + generation), and sending responses back to the client.
    -   **`routing.py`**: Defines the URL routing for WebSocket connections, mapping paths to consumers.

### 2. `project/` (Core Django Project)
-   **`settings.py`**: Contains the main configuration for the Django project, including database settings, installed apps, and Django Channels configurations.
-   **`urls.py`**: Defines the primary URL routing for HTTP requests, directing them to appropriate views in the `api` app.
-   **`asgi.py`**: The ASGI entry point for the application, used by uvicorn or daphne to serve the application, especially for WebSockets.
-   **`ws_middlewares.py`**: Custom middleware for WebSocket connections, potentially handling authentication or session management.

### 3. `uploads/`
-   **`documents/`**: Directory for storing uploaded PDF files.
-   **`vector_stores/`**: Directory for persisting vector store indexes or data.

### 4. `utils/` (Project-wide Utilities)
-   **`exception_handler.py`**: Centralized error handling logic for the application.
-   **`helpers.py`**: General utility functions used across the project.

## Setup and Installation

### Prerequisites
-   Docker and Docker Compose (recommended for easy setup)
-   Python 3.8+ (if setting up locally without Docker)

### Using Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/mohamedElbalky/mini_rag_system.git
    cd mini_rag_system
    ```
2.  **Create `.env` file**:
    Copy `.env.examples` to `.env` and fill in any necessary environment variables.
    ```bash
    cp .env.examples .env
    ```
3.  **Build and run containers**:
    ```bash
    docker-compose up --build
    ```
    This will build the Docker images and start the Django application and Redis for Channels.

### Local Setup (Without Docker)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/mohamedElbalky/mini_rag_system.git
    cd mini_rag_system
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv env
    source env/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create `.env` file**:
    Copy `.env.examples` to `.env` and fill in any necessary environment variables (e.g., API keys for LLMs).
    ```bash
    cp .env.examples .env
    ```
5.  **Apply database migrations**:
    ```bash
    python manage.py migrate
    ```
6.  **Run the development server**:
    ```bash
    python manage.py runserver
    ```
## Authentication Endpoints

This API provides endpoints for user registration and authentication using JWT (JSON Web Tokens).

### 1. Register a New User (`/api/v1/auth/register/`)
-   **Method**: `POST`
-   **Permissions**: `AllowAny`
-   **Description**: Creates a new user account.

**Request Body**:
```json
{
    "username": "your_username",
    "email": "your_email@example.com",
    "password": "your_strong_password",
    "password2": "your_strong_password"
}
```

**Successful Response (201 Created)**:
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user": {
            "id": 1,
            "username": "your_username",
            "email": "your_email@example.com"
        },
        "tokens": {
            "refresh": "eyJ...[your_refresh_token]...",
            "access": "eyJ...[your_access_token]..."
        }
    }
}
```

**Error Response (400 Bad Request, 500 Internal Server Error)**:
```json
{
    "success": false,
    "message": "Registration failed",
    "errors": {
        "email": ["Email already exists."],
        "password": ["Password fields didn't match."]
    }
}
```
or
```json
{
    "success": false,
    "message": "An error occurred during registration",
    "errors": "Error message details"
}
```

### 2. Login User (`/api/v1/auth/login/`)
-   **Method**: `POST`
-   **Permissions**: `AllowAny`
-   **Description**: Authenticates a user and provides JWT `access` and `refresh` tokens. The `access` token should be included in the `Authorization: Bearer <token>` header for subsequent authenticated requests.

**Request Body**:
```json
{
    "username": "your_username",
    "password": "your_strong_password"
}
```
*Note: The login endpoint currently authenticates using the `username` field, not `email`.*

**Successful Response (200 OK)**:
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": {
            "id": 1,
            "username": "your_username",
            "email": "your_email@example.com"
        },
        "tokens": {
            "refresh": "eyJ...[your_refresh_token]...",
            "access": "eyJ...[your_access_token]..."
        }
    }
}
```

**Error Response (400 Bad Request, 401 Unauthorized, 500 Internal Server Error)**:
```json
{
    "success": false,
    "message": "Username and password are required"
}
```
or
```json
{
    "success": false,
    "message": "Invalid credentials"
}
```
or
```json
{
    "success": false,
    "message": "An error occurred during login",
    "errors": "Error message details"
}
```

## Usage

### 1. Document Upload (HTTP POST)
-   **Endpoint**: `/api/v1/documents/upload/`
-   **Method**: `POST`
-   **Payload**: `multipart/form-data` with a file named `document` (or similar) containing the PDF.

Example using `curl`:
```bash
curl -X POST -H "Authorization: Token YOUR_AUTH_TOKEN" -F "document=@/path/to/your/document.pdf" http://localhost:8000/api/v1/documents/upload/
```

**Expected JSON Response (Success)**:
```json
{
    "success": true,
    "message": "Document uploaded and processed successfully",
    "data": {
        "id": 1,
        "title": "rag_test_document.pdf",
        "file": "http://127.0.0.1:8000/media/documents/rag_test_document.pdf",
        "uploaded_at": "2025-11-29T10:30:27.592944Z",
        "processed": true
    }
}
```
The `id` field is the `document_id` you will use for WebSocket queries.

### 2. Real-time Chat (WebSocket)
-   **Endpoint**: `ws://localhost:8000/ws/chat/`
-   **Protocol**: WebSocket

Once a WebSocket connection is established, you can send JSON messages containing your queries. The `document_id` in the message should correspond to the `id` received after a successful document upload. The system will retrieve relevant document chunks, use the LLM to generate a response, and send it back over the WebSocket.

Example message format (client to server):
```json
{
    "query": "What is this document about?",
    "document_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

**Expected WebSocket Message Formats (Server to Client):**

1.  **Connection Confirmation:**
    ```json
    {
        "type": "connection",
        "message": "Connected successfully. You can now send queries."
    }
    ```

2.  **Error Message:**
    ```json
    {
        "type": "error",
        "message": "Authentication failed. Please provide a valid token."
    }
    ```
    (Other error messages may also be sent with `type: "error"`.)

    No document found
    ```json
    {
        "type": "error",
        "message": "No document found. Please upload a PDF first."
    }
    ```

3.  **Status Updates:**
    ```json
    {
        "type": "status",
        "message": "Retrieving relevant context..."
    }
    ```
    ```json
    {
        "type": "status",
        "message": "Generating response..."
    }
    ```

4.  **Streaming Content (partial response):**
    ```json
    {
        "type": "stream",
        "content": "This document is about various concepts within Artificial Intelligence, including Machine Learning, Neural Networks, Large Language Models (LLMs), and Retrieval-Augmented Generation (RAG)."
    }
    ```
    (The `content` field will contain chunks of the LLM-generated response.)

5.  **End of Response:**
    ```json
    {
        "type": "end",
        "message": "Response complete"
    }
    ```
