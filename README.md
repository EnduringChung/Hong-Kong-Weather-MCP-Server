The weather MCP Server that enables connection to Hong Kong Observatory API for obtaining weather information.

Key Capabilities:
1. Obtain local weather forecast
2. 9-day weather forecast
3. Current weather report
4. Weather warning information
5. Special Weather Tips

By prompting the model to return in English, Traditional Chinese or Simplified Chinese, can enable the response to return in their respective language.


## Installation

pip install weather

## Configuration

Add to your MCP client configuration:

**Claude Desktop (`claude_desktop_config.json`):**
{
  "mcpServers": {
    "hko-weather": {
        "command": "hko-weather-mcp"
    }
  }
}


**LM Studio:**
{
    "hko-weather": {
        "command": "hko-weather-mcp"
    }
}


## Features

- Current weather conditions
- 9-day weather forecast
- Weather warnings
- Special weather tips
- Rainfall, temperature, humidity data

## Usage

The server provides weather data from Hong Kong Observatory through the `get_weather` tool.