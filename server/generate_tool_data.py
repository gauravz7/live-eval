import json
import os
import argparse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import config

class ParameterProperty(BaseModel):
    """Defines a single parameter property."""
    type: str = Field(..., description="The parameter type (e.g., 'string', 'number', 'boolean')")
    description: str = Field(..., description="Description of the parameter")
    enum: Optional[List[str]] = Field(None, description="Enum values for the parameter")
    minimum: Optional[float] = Field(None, description="Minimum value for numeric parameters")
    maximum: Optional[float] = Field(None, description="Maximum value for numeric parameters")
    default: Optional[Any] = Field(None, description="Default value for the parameter")

class ParameterSchema(BaseModel):
    """Defines the parameter schema structure."""
    type: str = Field(default="object", description="Schema type, always 'object'")
    properties: Dict[str, ParameterProperty] = Field(..., description="Parameter properties")
    required: List[str] = Field(..., description="List of required parameter names")

class ToolDefinition(BaseModel):
    """Defines the structure for a single tool definition."""
    name: str = Field(..., description="The name of the tool.")
    description: str = Field(..., description="A description of what the tool does.")
    parameters: ParameterSchema = Field(..., description="A JSON schema for the tool's parameters.")

class ToolDefinitions(BaseModel):
    """A list of tool definitions."""
    tools: List[ToolDefinition]

def generate_prompt(num_tools: int):
    """Creates the prompt for Gemini to generate tool definitions."""
    
    prompt = f"""
You are an expert tool definition generator for a voice-controlled AI system.
Your task is to generate a list of {num_tools} diverse and creative tool definitions that are easy to measure for accuracy.

**CRITICAL RULES FOR PARAMETER GENERATION:**
1.  **NO LONG TEXT:** Parameters must NOT be for long, free-form text (e.g., no 'email_body', 'note_content', 'message'). All parameters must be simple, discrete, and easily measurable.
2.  **USE ENUMS FOR STRINGS:** Every parameter with `type: "string"` MUST have an `enum` field with a list of possible categorical values. For example: `"status": {{ "type": "string", "description": "The status to set", "enum": ["active", "paused", "completed"] }}`.
3.  **PRIORITIZE DISCRETE TYPES:** Strongly prefer parameter types like `integer`, `number`, and `boolean` over strings.
4.  **SIMPLE & CLEAR:** Keep the tools simple with 1-3 parameters each. Descriptions should be clear and actionable.
5.  **SNAKE CASE:** Tool and parameter names must be in `snake_case`.

**EXAMPLE OF A GOOD, MEASURABLE TOOL:**
```json
{{
    "name": "set_light_brightness",
    "description": "Adjusts the brightness of a smart light.",
    "parameters": {{
        "type": "object",
        "properties": {{
            "brightness_level": {{
                "type": "integer",
                "description": "The desired brightness level.",
                "minimum": 0,
                "maximum": 100
            }},
            "room": {{
                "type": "string",
                "description": "The room where the light is located.",
                "enum": ["living_room", "bedroom", "kitchen", "office"]
            }}
        }},
        "required": ["brightness_level", "room"]
    }}
}}
```

Generate {num_tools} diverse tools that follow these strict rules, covering categories like:
- Smart Home (lights, thermostat, locks)
- Media Control (play, pause, volume)
- Timers & Alarms (set, cancel)
- Simple Lookups (stock price, weather)
- Settings (dark_mode, notifications)

Every single tool you generate must adhere to the parameter rules above to ensure they are measurable.
"""
    return prompt

def validate_tool_definitions(tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
    """Validates and converts tool definitions to the expected format."""
    validated_tools = []
    
    for tool in tools:
        try:
            # Convert to dictionary format
            tool_dict = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": tool.parameters.required
                }
            }
            
            # Convert parameters properly
            for param_name, param_def in tool.parameters.properties.items():
                param_dict = {
                    "type": param_def.type,
                    "description": param_def.description
                }
                
                # Add optional fields if they exist
                if param_def.enum:
                    param_dict["enum"] = param_def.enum
                if param_def.minimum is not None:
                    param_dict["minimum"] = param_def.minimum
                if param_def.maximum is not None:
                    param_dict["maximum"] = param_def.maximum
                if param_def.default is not None:
                    param_dict["default"] = param_def.default
                    
                tool_dict["parameters"]["properties"][param_name] = param_dict
            
            validated_tools.append(tool_dict)
            print(f"✅ Validated tool: {tool.name}")
            
        except Exception as e:
            print(f"❌ Error validating tool {tool.name}: {e}")
            continue
    
    return validated_tools

def main(num_tools: int):
    """Main function to generate and save tool definitions."""
    print("🤖 Starting tool definition generation with Controlled Generation...")
    
    # 1. Create the prompt
    prompt = generate_prompt(num_tools)
    
    # 2. Configure and call the Vertex AI API
    print(f"📞 Calling Vertex AI to generate {num_tools} tool definitions...")
    try:
        # Initialize the client for Vertex AI
        client = genai.Client(vertexai=True, project=config.PROJECT_ID, location=config.LOCATION)
        model_id = "gemini-2.5-pro"
        
        # Call the model to generate content
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ToolDefinitions,
                temperature=0.7,  # Add some creativity
                max_output_tokens=8192,  # Ensure enough tokens for all tools
            )
        )
        
        # 3. Get the parsed response
        parsed_response: ToolDefinitions = response.parsed
        print(f"✅ Received and parsed response from Vertex AI. Generated {len(parsed_response.tools)} tools.")
        
        # 4. Validate the tool definitions
        print("🔍 Validating tool definitions...")
        validated_tools = validate_tool_definitions(parsed_response.tools)
        
        if not validated_tools:
            print("❌ No valid tools were generated. Please try again.")
            return
        
        # 5. Save to file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "tools.py")
        
        with open(output_path, 'w') as f:
            f.write("# tools.py - Defines the functions available to the LiveAPI\n\n")
            f.write("TOOLS_DEFINITION = ")
            json.dump(validated_tools, f, indent=2)
            f.write("\n")
            
        print(f"✅ Successfully generated and saved {len(validated_tools)} tool definitions to {output_path}")
        
        # 6. Print summary
        print("\n📋 Generated Tools Summary:")
        for i, tool in enumerate(validated_tools, 1):
            required_params = ", ".join(tool["parameters"]["required"])
            print(f"{i:2d}. {tool['name']} - {tool['description'][:50]}... (requires: {required_params})")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if 'response' in locals():
            print("--- Vertex AI Response ---")
            print(response)
            print("--------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tool definitions for LiveAPI")
    parser.add_argument("--num_tools", type=int, default=24, help="The number of tools to generate (default: 24)")
    parser.add_argument("--validate", action="store_true", help="Run additional validation checks")
    args = parser.parse_args()
    main(args.num_tools)
