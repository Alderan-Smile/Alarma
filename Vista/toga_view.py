import sys
from datetime import datetime, date, time, timedelta
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from Controlador import apicon, dbcon
from Controlador.calendar_adapters import adapter as calendar_adapter


def build(app):
    conn = dbcon.get_db_connection()
    dbcon.create_tables(conn)

    # UI widgets
    country_box = toga.Selection(items=[], style=Pack(flex=1))
    year_input = toga.NumberInput(value=datetime.now().year, style=Pack(width=120))
    sync_button = toga.Button('Sincronizar feriados', on_press=lambda w: on_sync(conn, country_box, year_input, app))
    alarm_button = toga.Button('Programar alarma (días laborales)', on_press=lambda w: on_schedule(conn, country_box, app))
    status_label = toga.Label('Listo', style=Pack(padding_top=10))

    # Layout
    box = toga.Box(style=Pack(direction=COLUMN, padding=10))
    row1 = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
    row1.add(toga.Label('País: ', style=Pack(padding_right=6)))
    row1.add(country_box)
    row1.add(toga.Label('Año: ', style=Pack(padding_left=6, padding_right=6)))
    row1.add(year_input)
    box.add(row1)

    row2 = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
    row2.add(sync_button)
    row2.add(alarm_button)
    box.add(row2)
    box.add(status_label)

    # populate countries
    countries = apicon.fetch_countries()
    if countries:
        # map display -> code
        country_map = {f"{c.name} ({c.countryCode})": c.countryCode for c in countries}
        country_box.items = list(country_map.keys())
        country_box._country_map = country_map

    main_window = toga.MainWindow(title='Alarma laboral')
    main_window.content = box
    main_window.show()


def on_sync(conn, country_box, year_input, app):
    sel = country_box.value
    if not sel:
        app.main_window.info_dialog('Error', 'Seleccione un país primero')
        return
    country_code = country_box._country_map[sel]
    year = int(year_input.value)
    app.main_window.info_dialog('Sincronizando', f'Obteniendo feriados para {country_code} {year}...')
    holidays = apicon.fetch_holidays(country_code, year, api_key=None)
    app.main_window.info_dialog('Listo', f'Sincronizados {len(holidays)} feriados')


def load_holidays_set(conn, country_code, year):
    rows = dbcon.fetch_holidays_by_country(conn, country_code, year)
    return set(r.date for r in rows)


def next_workday(start_date: date, holidays_set):
    d = start_date
    while True:
        if d.weekday() >= 5:  # 5=sab,6=dom
            d = d + timedelta(days=1)
            continue
        if d.isoformat() in holidays_set:
            d = d + timedelta(days=1)
            continue
        return d


def on_schedule(conn, country_box, app):
    sel = country_box.value
    if not sel:
        app.main_window.info_dialog('Error', 'Seleccione un país primero')
        return
    country_code = country_box._country_map[sel]
    year = datetime.now().year
    holidays = dbcon.fetch_holidays_by_country(conn, country_code, year)
    holidays_set = set(h.date for h in holidays)

    # Ask time for alarm
    time_dialog = app.main_window.question_dialog('Hora', 'Ingrese la hora de la alarma en formato HH:MM (24h)')
    if not time_dialog:
        return
    try:
        hh, mm = [int(x) for x in time_dialog.split(':')]
    except Exception:
        app.main_window.info_dialog('Error', 'Formato de hora inválido')
        return

    # Compute next workday and create event via adapter
    today = date.today()
    nd = next_workday(today, holidays_set)
    alarm_datetime = datetime.combine(nd, time(hh, mm))

    title = 'Alarma laboral'
    description = 'Alarma programada para día laboral, omitiendo feriados y fines de semana.'

    try:
        calendar_adapter.create_event(alarm_datetime, title, description)
        app.main_window.info_dialog('Programado', f'Alarma programada para {alarm_datetime}')
    except NotImplementedError as e:
        app.main_window.info_dialog('No implementado', str(e))
    except Exception as e:
        app.main_window.info_dialog('Error', f'No se pudo crear la alarma: {e}')


def main():
    return toga.App('Alarma Laboral', 'org.example.alarma', startup=build)


if __name__ == '__main__':
    main().main_loop()
