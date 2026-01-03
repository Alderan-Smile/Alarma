import http.client
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from Modelo import contryDTO, holidayDTO
from Controlador import dbcon

def fetch_holidays(country_code: str, year: int, api_key: str):
    conn = http.client.HTTPSConnection("date.nager.at")
    endpoint = f"/api/v3/PublicHolidays/{year}/{country_code}"
    dbase = dbcon.get_db_connection()
    try:
        conn.request("GET", endpoint)
        res = conn.getresponse()
        if res.status != 200:
            print(f"Error fetching holidays: {res.status} {res.reason}")
            return []
        data = res.read()
        holidays_json = json.loads(data)

        holidays = []
        for item in holidays_json:
            holiday = holidayDTO.holidayDTO(
                date=item.get('date'),
                localName=item.get('localName'),
                name=item.get('name'),
                countryCode=country_code,
                year=year
            )
            holidays.append(holiday)
            dbcon.insert_holiday(dbase, holiday)
        return holidays
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fetch_countries():
    conn = http.client.HTTPSConnection("date.nager.at")
    endpoint = "/api/v3/AvailableCountries"
    dbase = dbcon.get_db_connection()
    try:
        conn.request("GET", endpoint)
        res = conn.getresponse()
        if res.status != 200:
            print(f"Error fetching countries: {res.status} {res.reason}")
            return []
        data = res.read()
        countries_json = json.loads(data)

        countries = []
        for item in countries_json:
            country = contryDTO.countryDTO(
                countryCode=item.get('countryCode'),
                name=item.get('name')
            )
            countries.append(country)
            dbcon.insert_country(dbase, country)
        return countries
    except Exception as e:
        print(f"An error occurred: {e}")
        return []