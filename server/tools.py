# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "set_focus_timer",
    "description": "Sets a timer for a focused work session, optionally followed by a short break.",
    "parameters": {
      "type": "object",
      "properties": {
        "duration_minutes": {
          "type": "number",
          "description": "The duration of the focus session in minutes. For example, 25 minutes.",
          "minimum": 1.0,
          "maximum": 180.0
        },
        "break_minutes": {
          "type": "number",
          "description": "The duration of the optional break after the session, in minutes. For example, 5 minutes.",
          "minimum": 1.0,
          "maximum": 60.0
        }
      },
      "required": [
        "duration_minutes"
      ]
    }
  },
  {
    "name": "get_world_time",
    "description": "Retrieves the current local time for any major city in the world.",
    "parameters": {
      "type": "object",
      "properties": {
        "city_name": {
          "type": "string",
          "description": "The name of the city to get the current time for, such as 'Tokyo', 'New York', or 'Paris'."
        }
      },
      "required": [
        "city_name"
      ]
    }
  }
]
