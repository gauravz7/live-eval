# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "set_reminder",
    "description": "Sets a reminder for a specific task at a given time.",
    "parameters": {
      "type": "object",
      "properties": {
        "task": {
          "type": "string",
          "description": "The description of the task to be reminded about. For example, 'call mom'."
        },
        "time": {
          "type": "string",
          "description": "When to set the reminder. For example, 'in 10 minutes' or 'at 3pm'."
        }
      },
      "required": [
        "task",
        "time"
      ]
    }
  },
  {
    "name": "get_weather_forecast",
    "description": "Retrieves the current weather forecast for a specified location.",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "The city for which to get the weather forecast, e.g., 'London' or 'Tokyo'."
        },
        "units": {
          "type": "string",
          "description": "The temperature unit.",
          "enum": [
            "celsius",
            "fahrenheit"
          ],
          "default": "celsius"
        }
      },
      "required": [
        "location"
      ]
    }
  },
  {
    "name": "currency_converter",
    "description": "Converts an amount from one currency to another.",
    "parameters": {
      "type": "object",
      "properties": {
        "amount": {
          "type": "number",
          "description": "The amount of money to convert."
        },
        "from_currency": {
          "type": "string",
          "description": "The three-letter currency code to convert from, e.g., 'USD'."
        },
        "to_currency": {
          "type": "string",
          "description": "The three-letter currency code to convert to, e.g., 'EUR'."
        }
      },
      "required": [
        "amount",
        "from_currency",
        "to_currency"
      ]
    }
  },
  {
    "name": "calculate_tip",
    "description": "Calculates the tip for a given bill amount and percentage.",
    "parameters": {
      "type": "object",
      "properties": {
        "bill_amount": {
          "type": "number",
          "description": "The total amount of the bill.",
          "minimum": 0.0
        },
        "tip_percentage": {
          "type": "number",
          "description": "The percentage of the bill to leave as a tip.",
          "default": 15.0
        }
      },
      "required": [
        "bill_amount"
      ]
    }
  },
  {
    "name": "get_movie_recommendation",
    "description": "Recommends a movie based on a specified genre.",
    "parameters": {
      "type": "object",
      "properties": {
        "genre": {
          "type": "string",
          "description": "The genre of the movie to recommend.",
          "enum": [
            "Comedy",
            "Action",
            "Drama",
            "Sci-Fi",
            "Horror",
            "Romance"
          ]
        }
      },
      "required": [
        "genre"
      ]
    }
  },
  {
    "name": "start_timer",
    "description": "Starts a timer for a specified duration.",
    "parameters": {
      "type": "object",
      "properties": {
        "duration_minutes": {
          "type": "number",
          "description": "The duration of the timer in minutes.",
          "minimum": 1.0,
          "maximum": 180.0
        },
        "timer_name": {
          "type": "string",
          "description": "An optional name for the timer, e.g., 'pizza oven'."
        }
      },
      "required": [
        "duration_minutes"
      ]
    }
  },
  {
    "name": "log_water_intake",
    "description": "Logs the amount of water consumed.",
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
            "cups"
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
    "name": "find_recipe",
    "description": "Finds a recipe based on a primary ingredient.",
    "parameters": {
      "type": "object",
      "properties": {
        "ingredient": {
          "type": "string",
          "description": "The main ingredient to search for in a recipe, e.g., 'chicken'."
        },
        "cuisine_type": {
          "type": "string",
          "description": "Optional: The type of cuisine, e.g., 'Italian' or 'Mexican'."
        }
      },
      "required": [
        "ingredient"
      ]
    }
  },
  {
    "name": "get_world_time",
    "description": "Gets the current time in a specified city.",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "The city for which to find the current time, e.g., 'New York'."
        }
      },
      "required": [
        "city"
      ]
    }
  },
  {
    "name": "tell_a_joke",
    "description": "Tells a joke, optionally from a specific category.",
    "parameters": {
      "type": "object",
      "properties": {
        "category": {
          "type": "string",
          "description": "The category of the joke.",
          "enum": [
            "any",
            "programming",
            "puns",
            "dad"
          ],
          "default": "any"
        }
      },
      "required": []
    }
  }
]
