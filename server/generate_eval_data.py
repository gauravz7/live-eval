import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from tools import TOOLS_DEFINITION
import config

from google.genai.types import (
    FunctionDeclaration,
    GenerateContentConfig,
    GoogleSearch,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting,
    ThinkingConfig,
    Tool,
    ToolCodeExecution,
)
     
# --- Pydantic Schemas for Controlled Generation ---
class TestCase(BaseModel):
    """Defines the structure for a single test case."""
    test_id: str = Field(..., description="A unique identifier for the test case.")
    spoken_text: str = Field(..., description="A natural language phrase a user would speak to invoke the tool.")
    expected_tool: str = Field(..., description="The exact name of the tool that should be called.")
    expected_args: Optional[Dict[str, Any]] = Field(None, description="A JSON object of arguments. Should be null if no arguments.")

class TestCases(BaseModel):
    """A list of test cases."""
    test_cases: List[TestCase]

def generate_prompt(tools_definition):
    """Creates the prompt for Gemini to generate test cases."""
    
    prompt = f"""
You are an expert test case generator for a voice-controlled AI system.
Your task is to generate a list of test cases based on the provided tool definitions, which only use discrete and categorical parameters.

**CRITICAL RULES FOR TEST CASE GENERATION:**
1.  **CREATE 2 UNIQUE TEST CASES:** For each tool definition provided, generate exactly two unique test cases.
2.  **NATURAL & AMBIGUOUS SPOKEN TEXT:** The `spoken_text` should be natural-sounding and conversational. It should be slightly ambiguous to make the model work, but not so unclear that the correct tool and parameters are impossible to determine. For example, instead of "Set brightness to 80," use "It's a bit too bright in here, can you turn it down to about 80%."
3.  **EXACT ARGUMENT MATCHING:** The `expected_args` you generate MUST use the exact values defined in the tool's `enum` or fall within the specified `minimum` and `maximum` for numbers.
4.  **VARY THE TESTS:** For each tool, create test cases that cover different parameters or scenarios. For instance, one test might use a required parameter, and the second could use both required and optional ones.

**Tool Definitions:**
```json
{json.dumps(tools_definition, indent=2)}
```

Generate the list of test cases following these rules precisely.
"""
    return prompt

def main():
    """Main function to generate and save test cases."""
    print("🤖 Starting test case generation with Controlled Generation...")
    
    # 1. Create the prompt
    prompt = generate_prompt(TOOLS_DEFINITION)
    
    # 2. Configure and call the Vertex AI API
    print(f"📞 Calling Vertex AI to generate test cases...")
    try:
        # Correctly initialize the client for Vertex AI
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        model_id = "gemini-2.5-pro"
        
        # Correctly call the model to generate content using the 'config' parameter
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TestCases,
            )
        )
        
        # 3. Get the parsed response
        parsed_response: TestCases = response.parsed
        print("✅ Received and parsed response from Vertex AI.")
        
        # 4. Save to file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "test_cases.json")
        
        # Convert Pydantic models to a list of dicts for JSON serialization
        test_cases_list = []
        for i, test_case in enumerate(parsed_response.test_cases):
            test_case_dict = test_case.dict()
            test_case_dict['test_id'] = f"{test_case.expected_tool}_{i+1}"
            test_cases_list.append(test_case_dict)
        
        with open(output_path, 'w') as f:
            json.dump(test_cases_list, f, indent=4)
            
        print(f"✅ Successfully generated and saved {len(test_cases_list)} test cases to {output_path}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if 'response' in locals():
            print("--- Vertex AI Response ---")
            print(response)
            print("--------------------------")

if __name__ == "__main__":
    main()
