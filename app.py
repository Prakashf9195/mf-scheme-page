from flask import Flask, render_template, request
import requests

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

# Cache scheme list on server start
all_schemes = get_all_schemes()

@app.route('/', methods=['GET', 'POST'])
def index():
    scheme_data = None
    scheme_code = ""
    selected_name = ""

    if request.method == 'POST':
        selected_name = request.form.get('scheme_name')
        # Find scheme code based on exact match
        matching = [s for s in all_schemes if s['scheme_name'].lower() == selected_name.lower()]
        if matching:
            scheme_code = matching[0]['scheme_code']
            scheme_data = get_scheme_details(scheme_code)

    return render_template('index.html', all_schemes=all_schemes, scheme_data=scheme_data, selected_name=selected_name)

if __name__ == '__main__':
    app.run(debug=True)
