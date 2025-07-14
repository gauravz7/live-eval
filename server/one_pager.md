# A Framework for Automated End-to-End Evaluation of Live, Voice-Driven, Tool-Using AI Models

## 1. Problem Statement

Evaluating the performance of large language models (LLMs) that interact with live APIs via real-time voice is a complex challenge. The primary difficulties include:

*   **Real-time Latency:** The system must process streaming audio, understand intent, and execute actions with minimal delay.
*   **Tool-Use Accuracy:** The model must accurately select the correct tool and extract the right parameters from a spoken request.
*   **Parameter Ambiguity:** Measuring parameter extraction accuracy is difficult when dealing with open-ended, free-form text fields (e.g., the body of an email), making it hard to distinguish between a correct and incorrect model response.
*   **Reproducibility & Scalability:** The evaluation must be automated, reproducible, and scalable to consistently measure performance across different model versions and with a varying number of available tools.
*   **Environmental Flakiness:** Test failures can occur due to temporary network issues or server unavailability, which can pollute the true signal of the model's performance.

## 2. Our Solution

We have developed a comprehensive, Python-based framework that automates the entire evaluation pipeline for voice-driven, tool-using AI models. It provides a **robust, precise, and reproducible** method for benchmarking model performance in a real-world, streaming context, while intelligently handling environmental failures and providing deep analytical insights.

## 3. Key Components & Workflow

The framework is composed of several key scripts that work in concert to generate data, simulate user interaction, execute tests, and analyze the results.

**Workflow Diagram:**
`generate_tool_data.py` -> `generate_eval_data.py` -> `tts_client.py` -> `run_test.py` <-> `server_eval.py` -> `analyze_results`

**Component Breakdown:**

1.  **Automated & Measurable Test Data Generation:**
    *   `generate_tool_data.py`: Uses a powerful generative model (e.g., Gemini 2.5 Pro) with a **strict prompt** to create a diverse set of tool definitions. The prompt enforces that all tool parameters are simple, discrete, and easily measurable (e.g., integers, booleans, or strings with a fixed set of `enum` values), explicitly forbidding ambiguous, long-form text fields.
    *   `generate_eval_data.py`: Ingests these measurable tool definitions and uses the same model to generate corresponding test cases. Each test case includes a natural language voice command (`spoken_text`) and the ground truth (`expected_tool`, `expected_args`), ensuring the arguments align perfectly with the discrete parameter definitions.

2.  **Realistic Voice Simulation:**
    *   `tts_client.py`: Converts the text-based commands from the test cases into high-quality audio streams using Google's Text-to-Speech API, simulating real user voice input.

3.  **Real-time Evaluation Server (`server_eval.py`):**
    *   A WebSocket server that acts as the intermediary between the test client and the live AI model (e.g., `gemini-live-2.5-flash`).
    *   It streams the simulated audio to the model, captures all outputs (transcriptions, audio, and tool calls), and logs every tool call with its corresponding test ID and arguments to `tool_call_log.jsonl`.

4.  **Robust Test Execution and Analysis (`run_test.py`):**
    *   **Resilient Test Runner:** The client attempts to connect to the server up to **3 times** for each test case, making the system resilient to temporary server unavailability. Tests that cannot be run after all retries are skipped and **excluded from the final accuracy calculation**, preventing environmental issues from skewing the results.
    *   **Two-Tiered Accuracy Analysis:** After the test run, the script automatically analyzes the logs and provides a more insightful, two-layered report:
        1.  **Tool Call Accuracy:** Measures how often the model selected the correct tool, regardless of the parameters.
        2.  **Tool & Parameter Accuracy:** A stricter metric that measures how often the model selected the correct tool *and* extracted all the correct parameters.
    *   **Detailed Error Reporting:** For failed tests, the report explicitly details the mismatch, showing the expected vs. actual tool names and parameters, which greatly simplifies debugging.

5.  **Scalable Benchmarking (`run_benchmark.py`):**
    *   This high-level script automates the entire workflow, allowing for comprehensive benchmarks. It can systematically test and record both accuracy metrics across a varying number of tools and against different model versions.

## 4. Core Technology

The system is built on a modern Python stack, leveraging:
*   **`asyncio` and `websockets`:** For efficient, non-blocking, real-time communication.
*   **Google Cloud Vertex AI:** Integrates directly with the `live.connect` API for streaming interaction with Gemini models.
*   **Google Cloud Text-to-Speech:** For generating high-fidelity, realistic voice inputs.
*   **Pydantic:** For robust data validation and structured configuration.

## 5. Outcome

This framework provides a highly automated, precise, and scalable solution to accurately benchmark the performance of live, tool-using AI models. It enables rapid iteration, data-driven decision-making, and a clear understanding of a model's strengths and weaknesses by separating tool selection accuracy from parameter extraction accuracy.
