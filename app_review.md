# Application Workflow Analysis

This document provides a detailed, step-by-by-step analysis of the application's text processing pipeline, from file upload to the final, corrected output.

## 1. Application Startup

The application is launched using the `launch.py` script, which concurrently starts the frontend and backend services.

-   **Backend:** A FastAPI server, initiated from `backend/app.py`, that listens on `http://localhost:8000`.
-   **Frontend:** A React/TypeScript application, started with Vite, that is accessible at `http://localhost:5173`.

## 2. File Upload and Initial Processing

The user begins by uploading a Markdown file through the web interface.

1.  **File Selection:** The frontend's `FileSelector` component allows the user to select a `.md` file.
2.  **Upload to Backend:** The selected file is sent to the `/api/upload` endpoint on the backend.
3.  **Temporary Storage:** The backend saves the uploaded file to a temporary location and sends back the file's content to the frontend for display in the "Original Text" preview window.

## 3. The Prepass Pipeline (Optional)

The user has the option to run a "prepass" step to identify and correct text that may be problematic for text-to-speech (TTS) engines.

1.  **Initiation:** The user clicks the "Run Prepass" button in the frontend, which triggers a request to the `/api/prepass` endpoint.
2.  **Chunking:** The backend chunks the input text into smaller, manageable pieces, separating text from code blocks.
3.  **LLM-Powered Detection:** For each text chunk, the backend calls a local LLM with a specialized prompt (`prepass_prompt.txt`) to detect and suggest replacements for TTS-unfriendly text (e.g., stylized Unicode, excessive capitalization).
4.  **Report Generation:** The results are compiled into a JSON report that is sent back to the frontend and displayed to the user.
5.  **User Approval:** The user can review the suggested changes and choose to incorporate them into the main grammar correction pass.

## 4. Main Grammar Correction

This is the core of the application's functionality, where the text is proofread and corrected by an LLM.

1.  **Initiation:** The user clicks the "Process Text" button, which sends a request to the `/api/process/{client_id}` endpoint.
2.  **WebSocket Connection:** The frontend establishes a WebSocket connection to the backend to receive real-time progress updates.
3.  **Prompt Injection:** If the prepass step was used, the backend injects the suggested replacements into the main grammar correction prompt (`grammar_promt.txt`) to ensure the LLM applies them.
4.  **Chunk Processing:** The backend processes the text chunk by chunk, sending each text segment to the LLM for correction.
5.  **Real-Time Preview:** As each chunk is processed, the corrected text is streamed back to the frontend via WebSockets and displayed in the "Processed Text" preview window.
6.  **Checkpointing:** The backend saves its progress after each chunk, allowing the process to be resumed if it's interrupted.

## 5. Final Output

Once all chunks have been processed, the user can save the corrected text.

1.  **Completion Message:** The backend sends a "completed" message to the frontend via WebSockets.
2.  **Save to File:** The user can click the "Save Result" button to download the fully corrected text as a new `.md` file.

## Key Technologies and Components

-   **Frontend:** React, TypeScript, Vite, Tailwind CSS
-   **Backend:** Python, FastAPI
-   **Core Logic:** `md_proof.py` (main processing), `prepass.py` (TTS problem detection)
-   **LLM Interface:** The application is designed to communicate with a local LLM, such as one running in LM Studio, via an OpenAI-compatible API.
-   **Communication:** REST APIs for primary actions (e.g., file upload) and WebSockets for real-time progress updates.
