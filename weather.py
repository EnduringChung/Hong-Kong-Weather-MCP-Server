from typing import Any
import httpx
import json
from mcp.server.fastmcp import FastMCP


# Initialize FastMCP server
mcp = FastMCP("weather", log_level = "ERROR")

# Constants
HKO_API_BASE = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
USER_AGENT = "weather-app/1.0"

async def make_hko_weather_request(url: str) -> dict[str, Any] | None:
    """Make a request to HKO API with proper error handling"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try: 
            response = await client.get(url, headers=headers, timeout= 30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e}")
            return None
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

def format_warnings(data):
    if not data.get('details'):
        return "No active warnings"
    
    warnings = []
    warning_code_dict = {
        "WFIRE": "Fire Danger Warning",
        "WFROST" : "Frost Warning",
        "WHOT": "Hot Weather Warning",
        "WCOLD": "Cold Weather Warning",
        "WMSGNL": "Strong Monsoon Signal",
        "WTCPRE8": "Pre-no.8 Special Announcement",
        "WRAIN": "Rainstorm Warning Signal",
        "WFNTSA": "Special Announcement on Flooding in the northern New Territories",
        "WL": "Landslip Warning",
        "WTCSGNL": "Tropical Cyclone Warning Signal",
        "WTMW": "Tsunami Warning",
        "WTS": "Thunderstorm Warning"
    }
    for warning in data['details']:
        code = warning_code_dict[warning['warningStatementCode']]
        subtype = f" ({warning['subtype']})" if warning.get('subtype') else ''
        time = warning['updateTime']
        content = ' '.join(warning['contents'])
        
        warnings.append(f"{code}{subtype} - {time}: {content}")
    
    return '\n\n'.join(warnings)

def format_warnings_summary(warnings_data:dict) -> str:
  final_warning_list = []
  if len(warnings_data.items()) == 0:
    return "No warning issued."
  else:
    for warning_code, warning_info in warnings_data.items():
      warning_name = warning_info.get('name', 'Unknown')
      action = warning_info.get('actionCode', 'Unknown')
      issue_time = warning_info.get('issueTime', 'Unknown')
      final_warning_list.append((f"{warning_name} ({warning_code}) - Action: {action}, Issued at: {issue_time}"))
  return "\n".join(final_warning_list)

def extract_temperature_data(data):
    if 'temperature' in data:
        temperatures = data['temperature']['data']
        record_time = data['temperature']['recordTime']
        location_temp = []
        for temp in temperatures:
            location_temp.append(f"{temp['place']}: {temp['value']}°{temp['unit']}")
        temp = f"Temperature readings (recorded at {record_time}):" + '\n'.join(location_temp)
    return temp

def extract_rainfall_data(data):
    if 'rainfall' in data:
        rainfall_info = data['rainfall']
        rainfall_data = rainfall_info['data']
        rain_location = []
        for rain in rainfall_data:
            maintenance = " Under maintenance" if rain.get('main') == 'TRUE' else "False"
            rain_location.append(f"{rain['place']}: {rain['max']}{rain['unit']} maintenance:{maintenance}")
    return f"Rainfall data:\n {''.join(rain_location)}"

def extract_humidity_data(data):
    if 'humidity' not in data or not data.get('humidity', {}).get('data'):
        return "Humidty data not available"

    humidity_info = data['humidity']['data'][0]
    record_time = data['humidity']['recordTime']
    return f"""Humidity: {humidity_info['value']} {humidity_info['unit']} at {humidity_info['place']} Recorded at: {record_time}"""

def extract_uv_index(data):
    uvinfo = data.get('uvindex', "No uv index")
    if len(uvinfo) < 1:
      return "No UV index"
    else: 
      uv_data = uvinfo['data'][0]
      record_desc = uvinfo['recordDesc']
      return f"""UV Index: {uv_data['value']} ({uv_data['desc']}) at {uv_data['place']} 
        Record description: {record_desc}"""


def current_weather_process(data):
    """Process and Extrate all weather info"""
    weather_info = [extract_temperature_data(data), extract_rainfall_data(data), extract_humidity_data(data), extract_uv_index(data)]
    return "\n".join(weather_info)


def formatting_weather(weather_data: dict, dataType:str) -> str:
    """Format weather into a readable string."""
    
    if dataType == "flw":
        return f"""
        General Situation: {weather_data.get("generalSituation", "Unknown")}
        tcInfo: {weather_data.get("tcInfo", "Unkown")}
        fireDangerWarning: {weather_data.get("fireDangerWarning", "No fire Danger")}
        forecastPeriod: {weather_data.get("forecastPeriod", "Forecast Period not provided")}
        forecastDesc: {weather_data.get("forecastDesc", "No forecast description available")}
        outlook: {weather_data.get("outlook", "No outlook available")}
        updateTime: {weather_data.get("updateTime", "No update time available")}
        """
    elif dataType == "fnd":
        weekly_weather_list = weather_data["weatherForecast"]
        weekly_weather = "\n".join(
            f"{day['week']} ({day['forecastDate']}): {day['forecastWeather']}, {day['forecastMintemp']['value']}-{day['forecastMaxtemp']['value']}\
            {day['forecastMaxtemp']['unit']}"
            for day in weekly_weather_list
        )
        return weekly_weather
    elif dataType == "rhrread":
        return current_weather_process(weather_data)
    elif dataType == "warnsum":
        return format_warnings_summary(weather_data)
    elif dataType == "warningInfo":
        return format_warnings(weather_data)
    elif dataType == "swt":
        special_weather_tips_list = weather_data["swt"]
        special_weather_tips = "\n".join(
        f"{tips.get('updateTime', 'time unknown')}: {tips.get('desc', 'no description')}" 
        for tips in special_weather_tips_list
        )
        return special_weather_tips
   



@mcp.tool()
async def get_weather(dataType: str, lang:str) -> str:
    """Get Weather from Hong Kong Obvervatory. 

    Args:
        dataType: {
        "flw": "local weather forecast which includes 
                general situation, 
                tropical cyclone info, 
                fire danger, 
                forecast period, 
                forecast description, 
                outlook",
        "fnd": "9-day weather forecast which includes
                weather forecast,
                forecast date
                forecast weather
                forecast max temp
                forecast min temp
                week
                forecast wind
                forecast max relative humidity
                forecast min relative humidity
                Probability of significant Rain
                soil temperature
                sea surface temperature",
        "rhrread": "Current Weather Report which includes
                lightling,
                rainfall,
                place or location,
                uvindex",
        "warnsum": "Weather Warning Summary which includes
                warning name,
                issue time",
        "warningInfo": "Weather Warning Information,
                warning statement code,
                subtype of warning
                update time",
        "swt": "Special Weather Tips"
        }
        lang: {
        "en": "English", 
        "tc": "traditional Chinese", 
        "sc": "simplified Chinese"
        }
    """
    dataType_set = {"flw", "fnd", "rhrread", "warnsum", "warningInfo", "swt"}
    lang_set = {"en", "tc", "sc"}

    if dataType not in dataType_set or lang not in lang_set:
        return f"Invalid dataType or lang. Use dataType in {dataType_set} and {lang_set}"
    else:
        url = f"{HKO_API_BASE}?dataType={dataType}&lang={lang}"
        print(f"Requesting URL: {url}")
        data = await make_hko_weather_request(url)
        
        if data is None:
            return "Data is None"
        else:
            return formatting_weather(data, dataType) # if data else "Request failed"

def main():
    """Main entry point for the server."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # Initialize and run the server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
