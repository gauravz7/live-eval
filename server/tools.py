# tools.py - Defines the functions available to the LiveAPI

TOOLS_DEFINITION = [
  {
    "name": "set_thermostat_temperature",
    "description": "Sets the temperature for a specific zone in the house.",
    "parameters": {
      "type": "object",
      "properties": {
        "temperature": {
          "type": "number",
          "description": "The target temperature."
        },
        "unit": {
          "type": "string",
          "description": "The temperature unit.",
          "enum": [
            "celsius",
            "fahrenheit"
          ]
        },
        "zone": {
          "type": "string",
          "description": "The zone to adjust.",
          "enum": [
            "upstairs",
            "downstairs",
            "main_floor",
            "all"
          ]
        }
      },
      "required": [
        "temperature",
        "unit",
        "zone"
      ]
    }
  },
  {
    "name": "set_light_color",
    "description": "Changes the color of a smart light in a specific room.",
    "parameters": {
      "type": "object",
      "properties": {
        "room": {
          "type": "string",
          "description": "The room where the light is located.",
          "enum": [
            "living_room",
            "bedroom",
            "kitchen",
            "office",
            "hallway"
          ]
        },
        "color": {
          "type": "string",
          "description": "The desired color for the light.",
          "enum": [
            "red",
            "blue",
            "green",
            "white",
            "purple",
            "orange"
          ]
        }
      },
      "required": [
        "room",
        "color"
      ]
    }
  },
  {
    "name": "lock_door",
    "description": "Locks or unlocks a specific door.",
    "parameters": {
      "type": "object",
      "properties": {
        "door_name": {
          "type": "string",
          "description": "The door to control.",
          "enum": [
            "front_door",
            "back_door",
            "garage_door",
            "patio_door"
          ]
        },
        "lock_state": {
          "type": "string",
          "description": "Whether to lock or unlock the door.",
          "enum": [
            "locked",
            "unlocked"
          ]
        }
      },
      "required": [
        "door_name",
        "lock_state"
      ]
    }
  },
  {
    "name": "set_window_blinds_position",
    "description": "Adjusts the position of the window blinds.",
    "parameters": {
      "type": "object",
      "properties": {
        "position_percent": {
          "type": "integer",
          "description": "The desired position of the blinds, from 0 (closed) to 100 (open).",
          "minimum": 0.0,
          "maximum": 100.0
        },
        "window_location": {
          "type": "string",
          "description": "The location of the window.",
          "enum": [
            "living_room_main",
            "bedroom_east",
            "office_south"
          ]
        }
      },
      "required": [
        "position_percent",
        "window_location"
      ]
    }
  },
  {
    "name": "activate_sprinkler_system",
    "description": "Turns on the sprinkler system for a specific zone for a set duration.",
    "parameters": {
      "type": "object",
      "properties": {
        "zone": {
          "type": "string",
          "description": "The sprinkler zone to activate.",
          "enum": [
            "front_lawn",
            "back_lawn",
            "garden_beds",
            "flower_pots"
          ]
        },
        "duration_minutes": {
          "type": "integer",
          "description": "How long to run the sprinklers in minutes.",
          "minimum": 1.0,
          "maximum": 60.0
        }
      },
      "required": [
        "zone",
        "duration_minutes"
      ]
    }
  },
  {
    "name": "toggle_smart_plug",
    "description": "Turns a smart plug on or off.",
    "parameters": {
      "type": "object",
      "properties": {
        "plug_id": {
          "type": "string",
          "description": "The identifier for the smart plug.",
          "enum": [
            "desk_lamp",
            "coffee_maker",
            "fan",
            "holiday_lights"
          ]
        },
        "state": {
          "type": "string",
          "description": "The desired state for the plug.",
          "enum": [
            "on",
            "off"
          ]
        }
      },
      "required": [
        "plug_id",
        "state"
      ]
    }
  },
  {
    "name": "set_volume",
    "description": "Sets the volume level for a media device.",
    "parameters": {
      "type": "object",
      "properties": {
        "volume_level": {
          "type": "integer",
          "description": "The desired volume level from 0 to 100.",
          "minimum": 0.0,
          "maximum": 100.0
        },
        "device": {
          "type": "string",
          "description": "The device to adjust the volume on.",
          "enum": [
            "tv",
            "soundbar",
            "kitchen_speaker",
            "headphones"
          ]
        }
      },
      "required": [
        "volume_level",
        "device"
      ]
    }
  },
  {
    "name": "play_media_by_genre",
    "description": "Plays a specific type of media from a chosen genre.",
    "parameters": {
      "type": "object",
      "properties": {
        "media_type": {
          "type": "string",
          "description": "The type of media to play.",
          "enum": [
            "music",
            "podcast",
            "audiobook"
          ]
        },
        "genre": {
          "type": "string",
          "description": "The genre of the media.",
          "enum": [
            "rock",
            "jazz",
            "classical",
            "news",
            "comedy",
            "sci_fi"
          ]
        }
      },
      "required": [
        "media_type",
        "genre"
      ]
    }
  },
  {
    "name": "skip_track",
    "description": "Skips forward or backward a number of tracks.",
    "parameters": {
      "type": "object",
      "properties": {
        "direction": {
          "type": "string",
          "description": "The direction to skip.",
          "enum": [
            "forward",
            "backward"
          ]
        },
        "count": {
          "type": "integer",
          "description": "The number of tracks to skip.",
          "minimum": 1.0,
          "default": 1
        }
      },
      "required": [
        "direction"
      ]
    }
  },
  {
    "name": "seek_to_timestamp",
    "description": "Jumps to a specific timestamp in the current media.",
    "parameters": {
      "type": "object",
      "properties": {
        "minutes": {
          "type": "integer",
          "description": "The minutes part of the timestamp.",
          "minimum": 0.0
        },
        "seconds": {
          "type": "integer",
          "description": "The seconds part of the timestamp.",
          "minimum": 0.0,
          "maximum": 59.0
        }
      },
      "required": [
        "minutes",
        "seconds"
      ]
    }
  },
  {
    "name": "set_timer",
    "description": "Sets a timer for a specific duration with a label.",
    "parameters": {
      "type": "object",
      "properties": {
        "duration_minutes": {
          "type": "integer",
          "description": "The duration of the timer in minutes.",
          "minimum": 1.0
        },
        "timer_label": {
          "type": "string",
          "description": "A label to identify the timer.",
          "enum": [
            "pasta",
            "laundry",
            "workout",
            "reading",
            "pizza"
          ]
        }
      },
      "required": [
        "duration_minutes",
        "timer_label"
      ]
    }
  },
  {
    "name": "set_alarm",
    "description": "Sets an alarm for a specific time with a specific sound.",
    "parameters": {
      "type": "object",
      "properties": {
        "hour": {
          "type": "integer",
          "description": "The hour for the alarm (24-hour format).",
          "minimum": 0.0,
          "maximum": 23.0
        },
        "minute": {
          "type": "integer",
          "description": "The minute for the alarm.",
          "minimum": 0.0,
          "maximum": 59.0
        },
        "alarm_sound": {
          "type": "string",
          "description": "The sound to play for the alarm.",
          "enum": [
            "chime",
            "radar",
            "bells",
            "harp",
            "digital"
          ]
        }
      },
      "required": [
        "hour",
        "minute",
        "alarm_sound"
      ]
    }
  },
  {
    "name": "cancel_timer",
    "description": "Cancels a previously set timer by its label.",
    "parameters": {
      "type": "object",
      "properties": {
        "timer_label": {
          "type": "string",
          "description": "The label of the timer to cancel.",
          "enum": [
            "pasta",
            "laundry",
            "workout",
            "reading",
            "pizza"
          ]
        }
      },
      "required": [
        "timer_label"
      ]
    }
  },
  {
    "name": "snooze_alarm",
    "description": "Snoozes the currently ringing alarm for a set number of minutes.",
    "parameters": {
      "type": "object",
      "properties": {
        "duration_minutes": {
          "type": "integer",
          "description": "The number of minutes to snooze the alarm.",
          "minimum": 1.0,
          "maximum": 20.0,
          "default": 9
        }
      },
      "required": [
        "duration_minutes"
      ]
    }
  },
  {
    "name": "get_weather_forecast",
    "description": "Retrieves the weather forecast for a specific city and day.",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "The city for the weather forecast.",
          "enum": [
            "new_york",
            "london",
            "tokyo",
            "sydney",
            "paris",
            "dubai"
          ]
        },
        "day": {
          "type": "string",
          "description": "The day for the forecast.",
          "enum": [
            "today",
            "tomorrow"
          ]
        }
      },
      "required": [
        "city",
        "day"
      ]
    }
  },
  {
    "name": "get_stock_price",
    "description": "Looks up the current price of a stock ticker.",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker_symbol": {
          "type": "string",
          "description": "The stock ticker symbol.",
          "enum": [
            "GOOG",
            "AAPL",
            "MSFT",
            "AMZN",
            "TSLA",
            "NVDA"
          ]
        }
      },
      "required": [
        "ticker_symbol"
      ]
    }
  },
  {
    "name": "get_currency_exchange_rate",
    "description": "Gets the exchange rate between two currencies.",
    "parameters": {
      "type": "object",
      "properties": {
        "from_currency": {
          "type": "string",
          "description": "The currency to convert from.",
          "enum": [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD"
          ]
        },
        "to_currency": {
          "type": "string",
          "description": "The currency to convert to.",
          "enum": [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD"
          ]
        }
      },
      "required": [
        "from_currency",
        "to_currency"
      ]
    }
  },
  {
    "name": "toggle_dark_mode",
    "description": "Enables or disables the system-wide dark mode.",
    "parameters": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Set to true to enable dark mode, false to disable."
        }
      },
      "required": [
        "enabled"
      ]
    }
  },
  {
    "name": "set_notification_level",
    "description": "Sets the notification level for a specific application.",
    "parameters": {
      "type": "object",
      "properties": {
        "app_name": {
          "type": "string",
          "description": "The application to configure.",
          "enum": [
            "email",
            "calendar",
            "messages",
            "social_media"
          ]
        },
        "level": {
          "type": "string",
          "description": "The desired notification level.",
          "enum": [
            "all",
            "priority",
            "none"
          ]
        }
      },
      "required": [
        "app_name",
        "level"
      ]
    }
  },
  {
    "name": "change_system_language",
    "description": "Changes the primary language of the system interface.",
    "parameters": {
      "type": "object",
      "properties": {
        "language_code": {
          "type": "string",
          "description": "The language code to switch to.",
          "enum": [
            "en_US",
            "en_GB",
            "es_ES",
            "fr_FR",
            "de_DE",
            "ja_JP"
          ]
        }
      },
      "required": [
        "language_code"
      ]
    }
  }
]
