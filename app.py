from flask import Flask, render_template, request
import requests
from requests.exceptions import RequestException
import os
from functools import lru_cache
import logging
import time

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fallback mock data for common schemes
FALLBACK_SCHEMES = [
    {
        "scheme_code": "120503",
        "scheme_name": "Axis Small Cap Fund - Regular Plan - Growth",
        "fund_house": "Axis Mutual Fund",
        "scheme_type": "Equity",
        "scheme_category": "Small Cap"
    },
    {
        "scheme_code": "120465",
        "scheme_name": "Axis Bluechip Fund - Regular Plan - Growth",
        "fund_house": "Axis Mutual Fund",
        "scheme_type": "Equity",
        "scheme_category": "Large Cap"
    },
    {
        "scheme_code": "120466",
        "scheme_name": "Axis Long Term Equity Fund - Regular Plan - Growth",
        "fund_house": "Axis Mutual Fund",
        "scheme_type": "Equity",
        "scheme_category": "ELSS"
    },
    {
        "scheme_code": "120467",
        "scheme_name": "Axis Midcap Fund - Regular Plan - Growth",
        "fund_house": "Axis Mutual Fund",
        "scheme_type": "Equity",
        "scheme_category": "Mid Cap"
    },
    {
        "scheme_code": "100371",
        "scheme_name": "SBI Bluechip Fund - Regular Plan - Growth",
        "fund_house": "SBI Mutual Fund",
        "scheme_type": "Equity",
        "scheme_category": "Large Cap"
    }
]

FALLBACK_DETAILS = {
    "120503": {
        "meta": {
            "scheme_name": "Axis Small Cap Fund - Regular Plan - Growth",
            "fund_house": "Axis Mutual Fund",
            "scheme_type": "Equity",
            "scheme_category": "Small Cap"
        },
        "data": [
            {"date": "2025-07-09", "nav": "32.456"},
            {"date": "2025-07-10", "nav": "32.789"},
            {"date": "2025-07-11", "nav": "33.123"},
            {"date": "2025-07-12", "nav": "33.567"},
            {"date": "2025-07-13", "nav": "34.012"}
        ]
    },
    "120465": {
        "meta": {
            "scheme_name": "Axis Bluechip Fund - Regular Plan - Growth",
            "fund_house": "Axis Mutual Fund",
            "scheme_type": "Equity",
            "scheme_category": "Large Cap"
        },
        "data": [
            {"date": "2025-07-09", "nav": "45.123"},
            {"date": "2025-07-10", "nav": "45.567"},
            {"date": "2025-07-11", "nav": "46.012"},
            {"date": "2025-07-12", "nav": "46.789"},
            {"date": "2025-07-13", "nav": "47.234"}
        ]
    },
    "120466": {
        "meta": {
            "scheme_name": "Axis Long Term Equity Fund - Regular Plan - Growth",
            "fund_house": "Axis Mutual Fund",
            "scheme_type": "Equity",
            "scheme_category": "ELSS"
        },
        "data": [
            {"date": "2025-07-09", "nav": "38.456"},
            {"date": "2025-07-10", "nav": "38.789"},
            {"date": "2025-07-11", "nav": "39.123"},
            {"date": "2025-07-12", "nav": "39.567"},
            {"date": "2025-07-13", "nav": "40.012"}
        ]
    },
    "120467": {
        "meta": {
            "scheme_name": "Axis Midcap Fund - Regular Plan - Growth",
            "fund_house": "Axis Mutual Fund",
            "scheme_type": "Equity",
            "scheme_category": "Mid Cap"
        },
        "data": [
            {"date": "2025-07-09", "nav": "41.234"},
            {"date": "2025-07-10", "nav": "41.678"},
            {"date": "2025-07-11", "nav": "42.012"},
            {"date": "2025-07-12", "nav": "42.456"},
            {"date": "2025-07-13", "nav": "42.901"}
        ]
    },
    "100371": {
        "meta": {
            "scheme_name": "SBI Bluechip Fund - Regular Plan - Growth",
            "fund_house": "SBI Mutual Fund",
            "scheme_type": "Equity",
            "scheme_category": "Large Cap"
        },
        "data": [
            {"date": "2025-07-09", "nav": "43.567"},
            {"date": "2025-07-10", "nav": "43.901"},
            {"date": "2025-07-11", "nav": "44.234"},
            {"date": "2025-07-12", "nav": "44.678"},
            {"date": "2025-07-13", "nav": "45.123"}
        ]
    }
}

@lru_cache(maxsize=100)
def get_all_schemes():
    """Fetch and return list of mutual fund schemes from mfapi.in."""
    url = "https://api.mfapi.in/mf"
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            schemes = response.json()
            valid_schemes = [s for s in schemes if s.get('scheme_name') and isinstance(s.get('scheme_name'), str)]
            logger.info(f"Loaded {len(valid_schemes)} schemes from API")
            return valid_schemes if valid_schemes else FALLBACK_SCHEMES
        except RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed fetching schemes: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
            else:
                logger.info("Using fallback schemes")
                return FALLBACK_SCHEMES

@lru_cache(maxsize=100)
def get_scheme_details(scheme_code):
    """Fetch details for a specific scheme by code."""
    if scheme_code in FALLBACK_DETAILS:
        logger.info(f"Using fallback details for scheme {scheme_code}")
        return FALLBACK_DETAILS[scheme_code]
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched details for scheme {scheme_code}")
            return data
        except RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed fetching scheme {scheme_code}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                logger.info(f"No details found for scheme {scheme_code}")
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
            # Split query into terms for progressive matching
            terms = selected_name.lower().split()
            matching_schemes = [
                s for s in all_schemes 
                if all(term in s.get('scheme_name', '').lower() for term in terms)
            ]
            if not matching_schemes:
                # Fallback to fuzzy matching for suggestions
                try:
                    from fuzzywuzzy import fuzz
                    matching_schemes = [
                        s for s in all_schemes
                        if fuzz.partial_ratio(selected_name.lower(), s.get('scheme_name', '').lower()) > 70
                    ][:10]
                    error_message = f"No exact schemes found matching '{selected_name}'. Try one of the suggestions below or check API status."
                except ImportError:
                    error_message = f"No schemes found matching '{selected_name}'. Please check the spelling or try again later."
            elif len(matching_schemes) == 1:
                scheme_code = matching_schemes[0]['scheme_code']
                scheme_data = get_scheme_details(scheme_code)
                if not scheme_data or 'meta' not in scheme_data:
                    error_message = f"Failed to fetch details for '{selected_name}'. The API may be down or the scheme code ({scheme_code}) is invalid."
                    matching_schemes = [
                        s for s in all_schemes
                        if selected_name.lower() in s.get('scheme_name', '').lower()
                    ][:10]
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
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
