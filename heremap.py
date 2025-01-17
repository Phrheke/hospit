import requests
import logging

logger = logging.getLogger(__name__)

HERE_API_KEY = 'AnNqHPQq1CjIAlhwXf7m0OiN54e8hOD43y7u0v1dYuY'

def search_hospitals(latitude, longitude):
    url = "https://discover.search.hereapi.com/v1/discover"
    params = {
        'apikey': AnNqHPQq1CjIAlhwXf7m0OiN54e8hOD43y7u0v1dYuY,
        'q': 'hospital',
        'at': f'{latitude},{longitude}',
        'limit': 4
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling HERE Maps API: {e}")
        return []
