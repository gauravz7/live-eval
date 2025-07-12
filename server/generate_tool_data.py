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
Your task is to generate a list of {num_tools} diverse and creative tool definitions.
The tools should cover a wide range of domains, such as productivity, finance, travel, entertainment, utilities, and more.
Each tool definition must include a name, a description, and a properly structured JSON schema for its parameters.
Keep the tools simple with 1-3 parameters each, and ensure they are easy to understand and use.

CRITICAL: You must follow this EXACT structure for each tool:

{{
    "name": "tool_name_in_snake_case",
    "description": "Clear description of what the tool does.",
    "parameters": {{
        "type": "object",
        "properties": {{
            "parameter_name": {{
                "type": "string",
                "description": "Description of the parameter with examples if helpful"
            }},
            "optional_parameter": {{
                "type": "number",
                "description": "Description of optional parameter",
                "minimum": 0,
                "maximum": 100
            }}
        }},
        "required": ["parameter_name"]
    }}
}}

IMPORTANT RULES:
1. Each parameter in "properties" must be an object with "type" and "description" fields
2. Use appropriate types: "string", "number", "integer", "boolean", "array"
3. Include validation like "minimum", "maximum", "enum" where appropriate
4. The "required" array should list only the mandatory parameter names
5. Tool names should be descriptive and use snake_case
6. Descriptions should be clear and actionable

Generate {num_tools} diverse tools covering different categories like:
- Productivity tools (calendar, notes, reminders)
- Finance tools (calculations, conversions)
- Travel tools (weather, currency, time zones)
- Entertainment tools (jokes, trivia, music)
- Utility tools (calculations, conversions, lookups)
- Health tools (fitness, nutrition)
- Communication tools (messaging, social)

Make sure each tool is unique and useful for voice interaction.
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