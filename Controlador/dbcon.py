import sqlite3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from Modelo import contryDTO, holidayDTO


def get_db_connection(db_path: str = None):
    # default path relative to project root: <repo>/Resources/database.db
    if db_path is None:
        base = Path(__file__).parent.parent
        resources = base / 'Resources'
        resources.mkdir(parents=True, exist_ok=True)
        db_path = str(resources / 'database.db')
    else:
        # ensure parent exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    if conn:
        conn.close()

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            countryCode TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            localName TEXT NOT NULL,
            name TEXT NOT NULL,
            countryCode TEXT NOT NULL,
            year INTEGER NOT NULL,
            FOREIGN KEY (countryCode) REFERENCES countries (countryCode)
        )
    ''')
    conn.commit()

def insert_country(conn, country: contryDTO.countryDTO):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO countries (countryCode, name)
        VALUES (?, ?)
    ''', (country.countryCode, country.name))
    conn.commit()

def insert_holiday(conn, holiday: holidayDTO.holidayDTO):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO holidays (date, localName, name, countryCode, year)
        VALUES (?, ?, ?, ?, ?)
    ''', (holiday.date, holiday.localName, holiday.name, holiday.countryCode, holiday.year))
    conn.commit()

def insert_weekend_holiday(conn, holiday: holidayDTO.holidayDTO):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO holidays (date, localName, name, countryCode)
        VALUES (?, ?, ?, ?)
    ''', (holiday.date, holiday.localName + ' (Weekend)', holiday.name, holiday.countryCode))
    conn.commit()

def fetch_countries(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM countries')
    rows = cursor.fetchall()
    countries = [contryDTO.countryDTO(row['countryCode'], row['name']) for row in rows]
    return countries

def fetch_holidays_by_country(conn, country_code, year):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM holidays WHERE countryCode = ? and year = ?', (country_code, year))
    rows = cursor.fetchall()
    holidays = [holidayDTO.holidayDTO(row['date'], row['localName'], row['name'], row['countryCode'], row['year']) for row in rows]
    return holidays