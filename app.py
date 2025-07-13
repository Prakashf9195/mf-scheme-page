from flask import Flask, render_template, request
import requests
from requests.exceptions import RequestException
import os
from functools import lru_cache
import logging
import time
import csv
from io import StringIO

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
            {"date": "2025-07-13", "nav": "34.012
