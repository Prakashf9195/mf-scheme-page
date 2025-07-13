from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# Fetch full list of schemes (only once and store)
def get_all_schemes():
    url = "https://api.mfapi.in/mf"
    response = requests.get(url)
    return response.json()

# Fetch single scheme details
def get_scheme_details(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url)
    return response.json()

# Cache schemes with valid names only
all_schemes = [s for s in get_all_schemes() if 'scheme_name' in s]

@app.route('/', methods=['GET', 'POST'])
def index():
    scheme_data = None
    selected_name = request.form.get('scheme_name', '').strip()

    if request.method == 'POST' and selected_name:
        normalized_selected = selected_name.lower()

        # Try exact match
        matching = [s for s in all_schemes if s.get('scheme_name', '').strip().lower() == normalized_selected]

        # If no exact match, fallback to partial match
        if not matching:
            matching = [s for s in all_schemes if normalized_selected in s.get('scheme_name', '').strip().lower()]

        if matching:
            scheme_code = matching[0]['scheme_code']
            scheme_data = get_scheme_details(scheme_code)
            if not scheme_data or 'meta' not in scheme_data:
                scheme_data = None

    return render_template('index.html', all_schemes=all_schemes, scheme_data=scheme_data, selected_name=selected_name)

# For Render: bind to 0.0.0.0 and dynamic port
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
