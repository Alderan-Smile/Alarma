import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from Controlador import dbcon, apicon, scheduler

def main():
    conn = dbcon.get_db_connection()
    dbcon.create_tables(conn)

    # Ensure we have countries in DB
    countries = dbcon.fetch_countries(conn)
    if not countries:
        print('No hay países en la BD. Trayendo desde la API...')
        apicon.fetch_countries()
        countries = dbcon.fetch_countries(conn)

    if not countries:
        print('No se pudo obtener países. Abortando.')
        return

    country_code = countries[0].countryCode
    print(f'Usando país: {countries[0].name} ({country_code})')

    # Run scheduler for 5 occurrences at 09:00 Monday-Friday
    scheduled = scheduler.schedule_recurring_workday_alarms(conn, country_code, hour=9, minute=0, occurrences=5, weekdays=set(range(0,5)))
    print(f'Se programaron {scheduled} eventos (simulación desktop).')

    # Print events store path
    events_file = Path(__file__).parent.parent / 'Resources' / 'calendar_events.json'
    print('Events stored at:', events_file)
    if events_file.exists():
        print(events_file.read_text(encoding='utf-8'))

if __name__ == '__main__':
    main()
