from flask import Flask, render_template, request
import requests
from requests.exceptions import RequestException
import os
from functools import lru_cache
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for API responses
@lru_cache(maxsize=100)
def get_all_schemes():
    """Fetch and return list of mutual fund schemes from mfapi.in."""
    url = "https://api.mfapi.in/mf"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        schemes = response.json()
        return [s for s in schemes if s.get('scheme_name') and isinstance(s.get('scheme_name'), str)]
    except RequestException as e:
        logger.error(f"Error fetching schemes: {e}")
        return []

@lru_cache(maxsize=100)
def get_scheme_details(scheme_code):
    """Fetch details for a specific scheme by code."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"Error fetching scheme {scheme_code}: {e}")
        return None

# Load schemes at startup
all_schemes = get_all_schemes()

@app.route('/', methods=['GET', 'POST'])
def index():
    scheme_data = None
    selected_name = request.form.get('scheme_name', '').strip()
    error_message = None
    matching_schemes = []

    if request.method == 'POST' and selected_name:
        if not selected_name:
            error_message = "Please enter a scheme name."
        elif len(selected_name) > 200:
            error_message = "Scheme name is too long (max 200 characters)."
        else:
            # Partial, case-insensitive matching
            matching_schemes = [
                s for s in all_schemes 
                if selected_name.lower() in s.get('scheme_name', '').strip().lower()
            ]
            if not matching_schemes:
                error_message = f"No schemes found matching '{selected_name}'. Please check the spelling."
            elif len(matching_schemes) == 1:
                scheme_code = matching_schemes[0]['scheme_code']
                scheme_data = get_scheme_details(scheme_code)
                if not scheme_data or 'meta' not in scheme_data:
                    error_message = "Failed to fetch scheme details or invalid data received."
            else:
                error_message = f"Multiple schemes found matching '{selected_name}'. Please select one below."

    return render_template(
        'index.html',
        all_schemes=all_schemes,
        scheme_data=scheme_data,
        selected_name=selected_name,
        error_message=error_message,
        matching_schemes=matching_schemes
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
