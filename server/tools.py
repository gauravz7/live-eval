# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "get_world_time",
    "description": "Fetches the current local time for any major city in the world.",
    "parameters": {
      "type": "object",
      "properties": {
        "city_name": {
          "type": "string",
          "description": "The name of the city for which to find the time, for example, 'Tokyo' or 'San Francisco'."
        }
      },
      "required": [
        "city_name"
      ]
    }
  },
  {
    "name": "generate_story_prompt",
    "description": "Creates a unique story prompt based on a specified genre and an optional keyword.",
    "parameters": {
      "type": "object",
      "properties": {
        "genre": {
          "type": "string",
          "description": "The genre for the story prompt.",
          "enum": [
            "fantasy",
            "sci-fi",
            "mystery",
            "horror",
            "adventure"
          ]
        },
        "keyword": {
          "type": "string",
          "description": "An optional specific keyword or character to include in the story prompt, like 'dragon' or 'cyborg'."
        }
      },
      "required": [
        "genre"
      ]
    }
  }
]
