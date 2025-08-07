import os
import requests
import base64
import re
import argparse

# FOFA API credentials
FOFA_EMAIL = os.getenv("FOFA_EMAIL")
FOFA_KEY = os.getenv("FOFA_KEY")

# FOFA API endpoint
FOFA_API_URL = "https://fofa.info/api/v1/search/all"

# Gemini API Key validation endpoint
GEMINI_VALIDATION_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"


def validate_gemini_key(key, silent=False):
    """
    Validates a potential Gemini API key by making a request to the Gemini API.
    """
    try:
        response = requests.get(GEMINI_VALIDATION_URL.format(key=key))
        if response.status_code == 200:
            return True
        if response.status_code == 400 and "API key not valid" in response.text:
            return False
        return False
    except requests.exceptions.RequestException as e:
        if not silent:
            print(f"Error validating key {key}: {e}")
        return False


def find_gemini_keys(text):
    """
    Finds all potential Gemini API keys in a given text.
    Keys start with "AIzaSy" and are 39 characters long.
    """
    return re.findall(r"AIzaSy[a-zA-Z0-9_-]{33}", text)


def search_fofa(query, silent=False):
    """
    Searches the FOFA API for the given query and validates potential Gemini keys.
    """
    if not FOFA_EMAIL or not FOFA_KEY:
        print("Error: Please set the FOFA_EMAIL and FOFA_KEY environment variables.")
        return []

    try:
        query_b64 = base64.b64encode(query.encode()).decode()
        params = {
            "email": FOFA_EMAIL,
            "key": FOFA_KEY,
            "qbase64": query_b64,
            "size": 1000,
            "full": "true",
        }

        response = requests.get(FOFA_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            print(f"FOFA API Error: {data.get('errmsg')}")
            return []

        valid_keys = []
        if "results" in data:
            for result in data["results"]:
                text_to_search = str(result)
                potential_keys = find_gemini_keys(text_to_search)
                for key in potential_keys:
                    if not silent:
                        print(f"Found potential key: {key}. Validating...")
                    if validate_gemini_key(key, silent):
                        if not silent:
                            print(f"VALID key found: {key}")
                        valid_keys.append(key)
        return valid_keys

    except requests.exceptions.RequestException as e:
        print(f"Error making request to FOFA API: {e}")
        return []
    except ValueError:
        print("Error: Could not decode JSON response from FOFA API.")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find Gemini API keys using FOFA.")
    parser.add_argument(
        "-s", "--silent", action="store_true", help="Suppress verbose output."
    )
    args = parser.parse_args()

    search_query = 'body="AIzaSy"'
    found_keys = search_fofa(search_query, args.silent)

    if found_keys:
        print("\n--- Found Valid Gemini Keys ---")
        for key in found_keys:
            print(key)
    else:
        if not args.silent:
            print("\nNo valid Gemini keys found.")
