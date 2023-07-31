import json
from flask import jsonify
from .app import app, cache
from .apis.aqi import AQI
from .apis.forecast import Forecast
from .apis.current import Current
from .apis import manager
from .services.forecastdatafetcher import DataFetcher

weather_fetcher = DataFetcher()


@app.route("/", methods=["GET"])
def index():
    """
    Handler for the root endpoint.

    Returns:
        A JSON response containing a greeting message.

    """
    data = {"message": "Hello from the backend!", "status": 200}
    return jsonify(data)


@app.route('/api/forecast', methods=['GET'])
@cache.cached(timeout=3600)
def get_forecast():
    """
    Handler for the '/api/forecast' endpoint.

    Returns:
        Forecast for the POI's.
    """
    forecast = Forecast(weather_fetcher)
    forecast.update_data()

    aqi = AQI()
    aqi.download_netcdf_and_store()
    aqi_data = aqi.to_json()
    aqi_coords = aqi.get_coordinates()

    pois = manager.get_pois()
    poi_forecast = forecast.get_closest_poi_coordinates_data(pois, aqi_data, aqi_coords)

    result = json.dumps(poi_forecast)

    return result


@app.route("/api/poi/", methods=["GET"])
def get_poi_data():
    """
    Handler for the '/api/poi' endpoint.

    Returns:
        Poi data if errors have not occurred.
    """
    return manager.get_pois_as_json()


@app.route("/api/poi/<accessibility>", methods=["GET"])
def get_poi_acessible_poi_data(accessibility):
    """
    Handler for the '/api/poi' endpoint.

    Returns:
        Poi data if errors have not occurred.
    """
    return manager.get_pois_as_json(accessibility)


@app.route('/api/weather', methods=['GET'])
@cache.cached(timeout=3600)
def get_weather_helsinki_kaisaniemi():
    current = Current(weather_fetcher)
    current.get_current_weather()
    helsinki_kaisaniemi = current.weather.get("Helsinki Kaisaniemi")
    return jsonify(helsinki_kaisaniemi)


@app.errorhandler(404)
def not_found_error(error):
    """
    Error handler for the 404 (Not Found) error.
    """
    error_data = {"message": "Resource not found", "status": error.code}
    return jsonify(error_data), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Error handler for the 500 (Internal Server Error) error.
    """
    error_data = {"message": "Internal server error", "status": error.code}
    return jsonify(error_data), 500
