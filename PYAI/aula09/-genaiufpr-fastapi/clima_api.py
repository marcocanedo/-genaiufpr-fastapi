import requests
from functools import lru_cache
from typing import Any, cast

from fastapi import FastAPI, HTTPException

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
app = FastAPI()

REQUEST_TIMEOUT = 3.0


@lru_cache(maxsize=128)
def get_coordinates(city_name: str) -> tuple[float, float]:
    geo_params: dict[str, str | int] = {"name": city_name, "count": 1}
    geo_response = requests.get(GEO_URL, params=geo_params, timeout=REQUEST_TIMEOUT)
    geo_response.raise_for_status()
    geo_data: dict[str, Any] = geo_response.json()

    results = cast(list[dict[str, Any]] | None, geo_data.get("results"))
    if not results:
        raise HTTPException(status_code=404, detail=f"Cidade '{city_name}' não encontrada")

    first_result = results[0]
    if "latitude" not in first_result or "longitude" not in first_result:
        raise HTTPException(
            status_code=502,
            detail="Resposta inválida da API de geolocalização",
        )

    return float(first_result["latitude"]), float(first_result["longitude"])


@app.get("/temperatura-cidade")
def temperatura_cidade(nome_cidade: str) -> float:
    cidade = nome_cidade.strip()
    lat, lon = get_coordinates(cidade)
    weather_params: dict[str, float | bool] = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }
    weather_response = requests.get(WEATHER_URL, params=weather_params, timeout=REQUEST_TIMEOUT)
    weather_response.raise_for_status()
    weather_data: dict[str, Any] = weather_response.json()

    current_weather = cast(dict[str, Any] | None, weather_data.get("current_weather"))
    if not current_weather or "temperature" not in current_weather:
        raise HTTPException(
            status_code=502,
            detail="Resposta inválida da API de previsão",
        )

    return float(current_weather["temperature"])
