from typing import Any

import requests
from fastapi import FastAPI


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
app = FastAPI()


@app.get("/temperatura-cidade")
def temperatura_cidade(nome_cidade: str) -> float:
    geo_params: dict[str, str | int] = {"name": nome_cidade, "count": 1}
    geo_response = requests.get(GEO_URL, params=geo_params)
    geo_data: dict[str, Any] = geo_response.json()

    lat = float(geo_data["results"][0]["latitude"])
    lon = float(geo_data["results"][0]["longitude"])

    weather_params: dict[str, float | bool] = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }
    weather_response = requests.get(WEATHER_URL, params=weather_params)
    weather_data: dict[str, Any] = weather_response.json()
    return float(weather_data["current_weather"]["temperature"])

