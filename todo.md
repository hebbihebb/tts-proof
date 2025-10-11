# TTS-Proof Implementation Plan & Todo List

This document outlines a plan for implementing the features listed in the `readme.md` TODO list. The focus is on making non-destructive, incremental enhancements to the application.

## 🎯 UI/UX Improvements (High Priority)

These features are aimed at improving the user experience and workflow of the application.

### 1. Separate Model Picker for Prepass

*   **Summary**: Allow users to select a different language model for the TTS prepass detection than for the main grammar correction pass. This is useful if a smaller, faster model is sufficient for detection.
*   **Implementation Plan**:
    *   **Frontend (`frontend/src/App.tsx`)**:
        1.  Introduce a new state variable, e.g., `prepassModelId`.
        2.  Add a second `<ModelPicker />` component within the "TTS Prepass" section of the UI.
        3.  This new picker will be bound to `prepassModelId`. The existing picker will remain for the grammar model (`selectedModelId`).
        4.  Pass `prepassModelId` as a prop to the `<PrepassControl />` component.
    *   **Frontend (`frontend/src/components/PrepassControl.tsx`)**:
        1.  Modify the component to accept `prepassModelId` as a prop.
        2.  When triggering the prepass run, use this new model ID in the API call to the backend.
    *   **Backend (`backend/app.py`)**:
        1.  No changes are required. The `/api/prepass` endpoint already accepts a `model_name` parameter.
*   **Impact Analysis**:
    *   **Dependencies**: None.
    *   **Code Changes**: `frontend/src/App.tsx`, `frontend/src/components/PrepassControl.tsx`.
    *   **Risk**: Low. This is an additive UI change.

### 2. Expose Prepass Prompt in Web UI

*   **Summary**: Allow users to view and edit the prompt used for the TTS prepass, similar to how the grammar prompt is editable.
*   **Implementation Plan**:
    1.  **Backend (`prepass.py`)**:
        *   Externalize the hardcoded prepass prompt. Create a new file `prepass_prompt.txt` in the root directory.
        *   Modify `prepass.py` to load the prompt from this file. Include a fallback to the original hardcoded prompt if the file doesn't exist.
    2.  **Backend (`backend/app.py`)**:
        *   Add two new API endpoints:
            *   `GET /api/prepass-prompt`: Reads and returns the content of `prepass_prompt.txt`.
            *   `POST /api/prepass-prompt`: Saves a new prompt to `prepass_prompt.txt`.
        *   These endpoints will mirror the existing `/api/grammar-prompt` endpoints.
    3.  **Frontend (`frontend/src/services/api.ts`)**:
        *   Add functions to call the new prepass prompt endpoints.
    4.  **Frontend (`frontend/src/App.tsx`)**:
        *   Add a new state for the prepass prompt, e.g., `prepassPrompt`.
        *   Load this prompt from the backend on startup.
        *   Add an "Edit" button to the "TTS Prepass" section. This button will open a modal.
    5.  **Frontend (`frontend/src/components/`)**:
        *   Reuse the existing `PromptEditor` component for editing the prepass prompt. It can be passed the prepass prompt state and the corresponding save function.
*   **Impact Analysis**:
    *   **Dependencies**: None.
    *   **Code Changes**: `prepass.py`, `backend/app.py`, `frontend/src/services/api.ts`, `frontend/src/App.tsx`. A new file `prepass_prompt.txt` will be created.
    *   **Risk**: Low. The core logic remains the same, we are just externalizing a string.

### 3. Reorganize Web UI Layout

*   **Summary**: Refactor the UI from a 2x3 grid to a more intuitive, linear workflow, potentially a multi-column layout.
*   **Proposed Layout**: A three-column layout for the main controls, flowing from left to right:
    1.  **Column 1: Input & Setup**:
        *   File Selector
        *   File Analysis
        *   Chunk Size Control
    2.  **Column 2: Pre-Processing (Optional Step)**:
        *   TTS Prepass section, including its own model picker and prompt editor button.
    3.  **Column 3: Main Processing**:
        *   Main Model Selector (for grammar)
        *   Prompt Template section (for grammar)
        *   Process Document section (Run/Cancel buttons, progress bar)
*   **Implementation Plan**:
    *   **Frontend (`frontend/src/App.tsx`)**:
        1.  Modify the main JSX structure. Replace the `grid-cols-3 grid-rows-2` with a new structure, likely using Flexbox or a different CSS Grid setup to achieve the three-column layout.
        2.  Move the existing components into the new layout structure.
*   **Impact Analysis**:
    *   **Dependencies**: None.
    *   **Code Changes**: `frontend/src/App.tsx`.
    *   **Risk**: Medium. This is a significant visual change. While it shouldn't break functionality if done carefully, it will alter the user experience completely. Thorough testing on different screen sizes is required.

### 4. Real-time Chunk Preview

*   **Summary**: Display the processed text in the preview window as each chunk is completed, rather than waiting for the entire document to finish.
*   **Implementation Plan**:
    1.  **Backend (`backend/app.py`)**:
        *   In the `run_processing_job` function, modify the `chunk_complete` WebSocket message. Instead of sending a truncated `processed_content`, send the *full* corrected text for the chunk.
        *   Ensure that messages are also sent for non-text chunks (like code blocks), containing the original content, so the live preview can be reconstructed accurately.
    2.  **Frontend (`frontend/src/App.tsx`)**:
        *   In the WebSocket message handler (`handleWebSocketMessage`):
            *   On connection start, clear the `processedText` state.
            *   For the `chunk_complete` message type, append the received chunk content (`message.chunk.processed_content`) to the `processedText` state.
            *   Remove the logic that sets `processedText` in the `completed` message handler, as the text will already be fully assembled.
*   **Impact Analysis**:
    *   **Dependencies**: None.
    *   **Code Changes**: `backend/app.py`, `frontend/src/App.tsx`.
    *   **Risk**: Medium. This changes the data flow for results. Need to ensure correct concatenation and handling of all chunk types to avoid a garbled preview.

### 5. Open Temp Files Location Button

*   **Summary**: Add a button that helps the user find the temporary files created during processing.
*   **Implementation Plan**:
    1.  **Backend (`backend/app.py`)**:
        *   Create a new, simple endpoint: `GET /api/temp-directory`.
        *   This endpoint will return the path of the temporary directory used by the application (e.g., from `tempfile.gettempdir()`).
    2.  **Frontend**:
        *   Add a new button, perhaps in the logs section or a settings menu.
        *   When clicked, the button's event handler will:
            *   Call the `/api/temp-directory` endpoint.
            *   Display the returned path to the user in a modal or a dismissible notification.
            *   Include a "Copy to Clipboard" button within the notification to make it easy for the user to copy the path. Use `navigator.clipboard.writeText()`.
*   **Impact Analysis**:
    *   **Dependencies**: None.
    *   **Code Changes**: `backend/app.py`, and a new component or part of an existing component on the frontend.
    *   **Risk**: Low. This is a simple, non-intrusive feature.

### 6. Batch File Processing (Marked as Optional in README)

*   **Summary**: Allow users to upload and process multiple files in a queue.
*   **Implementation Plan (High-Level)**:
    *   This is a significant feature that should be implemented after the higher-priority items.
    *   **Frontend**:
        1.  Modify `FileSelector` to accept multiple files.
        2.  Create a new "File Queue" component to display the list of uploaded files and their status (Queued, Processing, Complete, Error).
        3.  Refactor the processing logic in `App.tsx` to manage this queue. It would iterate through the file list, processing one at a time and updating the UI accordingly.
    *   **Backend**: No changes are likely needed, as the backend is stateless and processes whatever content it receives. The queue management can be handled entirely on the frontend.
*   **Impact Analysis**:
    *   **Risk**: High. Requires major changes to frontend state management and application workflow.

---

## Further Enhancements (Optional)

The `readme.md` also lists "Core Features", "Advanced Features", and "Quality & Testing" as optional enhancements. These can be planned in more detail after the primary UI/UX improvements are completed. A brief summary:

*   **Diff View**: Would require a library like `diff-match-patch` or a React diff component. The backend would need to provide both original and corrected text.
*   **Processing Profiles / Custom Prompts**: Would involve more complex state management on the frontend to store and manage presets, likely using `localStorage`.
*   **Automated Testing**: Would involve setting up a test runner like Jest/Vitest for the frontend and `pytest` for the backend, and writing unit and integration tests. This is a high-value task for ensuring long-term stability.