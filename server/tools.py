# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "get_animal_info",
    "description": "Get information about a specific animal.",
    "parameters": {
        "type": "object",
        "properties": {
            "animal_name": {
                "type": "string",
                "description": "The name of the animal."
            }
        },
        "required": ["animal_name"]
    }
  },
  {
    "name": "get_planet_info",
    "description": "Get information about a specific planet.",
    "parameters": {
        "type": "object",
        "properties": {
            "planet_name": {
                "type": "string",
                "description": "The name of the planet."
            }
        },
        "required": ["planet_name"]
    }
  },
  {
    "name": "get_ocean_info",
    "description": "Get information about a specific ocean.",
    "parameters": {
        "type": "object",
        "properties": {
            "ocean_name": {
                "type": "string",
                "description": "The name of the ocean."
            }
        },
        "required": ["ocean_name"]
    }
  },
  {
    "name": "get_weather",
    "description": "Get the current weather information for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g., San Francisco, CA"
            }
        },
        "required": ["location"]
    }
  },
  {
    "name": "turn_on_lights",
    "description": "Turn on the smart lights in a specific room or garage room.",
    "parameters": {
        "type": "object",
        "properties": {
            "room": {
                "type": "string",
                "description": "The room where the lights should be turned on."
            }
        },
        "required": ["room"]
    }
  },
  {
    "name": "turn_off_lights",
    "description": "Turn off the smart lights in a specific room or garage room.",
    "parameters": {
        "type": "object",
        "properties": {
            "room": {
                "type": "string",
                "description": "The room where the lights should be turned off."
            }
        },
        "required": ["room"]
    }
  },
  {
    "name": "generate_report",
    "description": "Generate a report on a specific topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic for the report."
            }
        },
        "required": ["topic"]
    }
  },
  {
    "name": "generate_code",
    "description": "Generate code in a specific programming language.",
    "parameters": {
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "The programming language."
            },
            "description": {
                "type": "string",
                "description": "A description of the code to generate."
            }
        },
        "required": ["language", "description"]
    }
  }
]
