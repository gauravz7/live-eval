# LiveAPI Automated Testing Framework

## 1. Project Overview

This project provides a robust, automated testing framework for a voice-controlled LiveAPI powered by Google's Gemini models. It is designed to evaluate the accuracy of the API's tool-calling capabilities by simulating real-time audio streams and analyzing the server's responses.

The framework includes a specialized evaluation server for running automated tests, with features for audio recording, detailed logging, and single-turn session management.

A key feature of this framework is the ability to dynamically generate test cases using Gemini 1.5 Pro, ensuring a diverse and comprehensive set of evaluation data.

## 2. Architecture

The project is composed of several key files, each with a specific role:

*   **`tools.py`**: The "source of truth" for the API's capabilities. It defines the available tools, their descriptions, and their parameters.
*   **`config.py`**: The central configuration file for all settings, including GCP project details, TTS parameters, and file paths.
*   **`tts_client.py`**: A dedicated client for interacting with the Google Cloud Text-to-Speech API to generate audio from text.
*   **`common.py`**: Contains the base WebSocket server class and other common components.
*   **`server_eval.py`**: The evaluation server, which includes features for audio recording, detailed logging, and single-turn session management.
*   **`run_test.py`**: The main orchestration script for the testing workflow. It loads test cases, sends them to the evaluation server, and analyzes the results.
*   **`test_cases.json`**: A JSON file containing the test cases to be used by the evaluation script.
*   **`generate_eval_data.py`**: A powerful tool that uses Gemini 1.5 Pro to dynamically generate test cases based on the tool definitions in `tools.py`.

## 3. Flow Diagram

This diagram illustrates the workflow of the automated testing framework:

![Evaluation Framework Flow](Eval.png)

## 4. Running the Evaluation

Follow these steps to run the automated test suite:

### Step 1: Set Up the Environment

1.  **Install Dependencies**:
    ```bash
    pip install -r pythonsdk-eval-live/server/requirements.txt
    pip install pydantic
    ```

2.  **Authenticate with Google Cloud**:
    ```bash
    gcloud auth application-default login
    ```

### Step 2: Generate Evaluation Data

1.  **Run the generation script**:
    ```bash
    python pythonsdk-eval-live/server/generate_eval_data.py
    ```
    This will use Gemini 1.5 Pro to create a fresh set of test cases and save them to `test_cases.json`.

### Step 3: Run the Automated Test

1.  **Start the Evaluation Server**:
    ```bash
    python pythonsdk-eval-live/server/server_eval.py
    ```

2.  **In a separate terminal, execute the test script**:
    ```bash
    python pythonsdk-eval-live/server/run_test.py
    ```

The script will then execute the test cases, and you will see a final accuracy report in the console. All recorded audio and logs will be saved in the `pythonsdk-eval-live/server/results/` directory.
