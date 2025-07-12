# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "calculate_investment_growth",
    "description": "Calculates the future value of an investment with compound interest.",
    "parameters": {
      "type": "object",
      "properties": {
        "principal": {
          "type": "number",
          "description": "The initial principal amount of the investment.",
          "minimum": 1.0
        },
        "rate": {
          "type": "number",
          "description": "The annual interest rate as a percentage, e.g., enter 5 for 5%.",
          "minimum": 0.0
        },
        "years": {
          "type": "number",
          "description": "The number of years the investment will grow.",
          "minimum": 1.0
        }
      },
      "required": [
        "principal",
        "rate",
        "years"
      ]
    }
  },
  {
    "name": "get_timezone_info",
    "description": "Gets the current time and timezone information for a specific city.",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "The name of the city to get timezone information for, e.g., 'Tokyo' or 'San Francisco'."
        }
      },
      "required": [
        "city"
      ]
    }
  },
  {
    "name": "get_movie_recommendation",
    "description": "Provides a movie recommendation based on a specified genre.",
    "parameters": {
      "type": "object",
      "properties": {
        "genre": {
          "type": "string",
          "description": "The genre of the movie to recommend.",
          "enum": [
            "Action",
            "Comedy",
            "Drama",
            "Sci-Fi",
            "Horror",
            "Thriller",
            "Romance"
          ]
        },
        "decade": {
          "type": "string",
          "description": "Optional: The decade the movie was released in, e.g., '1990s' or '2010s'."
        }
      },
      "required": [
        "genre"
      ]
    }
  },
  {
    "name": "log_water_intake",
    "description": "Logs the amount of water consumed to a daily health tracker.",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "number",
          "description": "The amount of water consumed.",
          "minimum": 1.0
        },
        "unit": {
          "type": "string",
          "description": "The unit of measurement for the water amount.",
          "enum": [
            "ml",
            "oz",
            "cup"
          ],
          "default": "ml"
        }
      },
      "required": [
        "amount"
      ]
    }
  },
  {
    "name": "send_quick_note",
    "description": "Sends a short note or reminder to a specified contact.",
    "parameters": {
      "type": "object",
      "properties": {
        "contact_name": {
          "type": "string",
          "description": "The name of the contact to send the note to, e.g., 'Mom' or 'Alex'."
        },
        "message": {
          "type": "string",
          "description": "The short message or note content to send."
        }
      },
      "required": [
        "contact_name",
        "message"
      ]
    }
  }
]
