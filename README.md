Once the server is running, you can access the interactive API documentation at `http://127.0.0.1:8000# EdAgent

EdAgent is an AI-powered educational tool designed to transform static study materials into interactive learning resources. By leveraging Large Language Models, the application processes uploaded notes and documents to automatically generate comprehensive summaries and challenging multiple-choice questions (MCQs).

## Features

*   **Document Processing:** Upload PDF or text-based notes for instant analysis.
*   **AI Summarization:** Get concise, structured summaries of complex topics.
*   **MCQ Generation:** Automatically create quizzes based on your study material to test your knowledge.
*   **Cloud Integration:** Secure file handling and storage via Cloudinary.
*   **Multi-Model Support:** Integration with Google Gemini and Groq AI for high-performance processing.

## Tech Stack

*   **Backend:** FastAPI
*   **Task Orchestration:** Python
*   **Storage:** Cloudinary
*   **AI Engines:** Google Gemini API, Groq AI

---

## Getting Started

### Prerequisites

*   Python 3.9+
*   A Cloudinary account
*   API keys for Google Gemini and Groq AI

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/jrjagdish/Ed_agent.git](https://github.com/jrjagdish/Ed_agent.git)
    cd Ed_agent
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Create a `.env` file in the root directory and add your credentials:
```env
# AI API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
Running the Application
The server is built with FastAPI and should be started using Uvicorn. Run the following command:

Bash
uvicorn main:app --reload
Once the server is running, you can access the interactive API documentation at http://127.0.0.1:8000/docs.

Usage
Upload: Send your notes (PDF/Text) to the upload endpoint.

Process: The agent parses the file and sends the content to the AI models.

Learn: Receive a structured summary and a set of MCQs instantly.
