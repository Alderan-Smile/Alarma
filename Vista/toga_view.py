import sys
from datetime import datetime, date, time, timedelta
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from Controlador import apicon, dbcon, scheduler
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

    # Weekday selection (Mon-Sun)
    weekdays_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
    weekdays_box.add(toga.Label('Días: ', style=Pack(padding_right=6)))
    weekday_names = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']
    weekday_checks = []
    for i, name in enumerate(weekday_names):
        cb = toga.Checkbox(label=name, style=Pack(padding_right=6))
        # default Mon-Fri checked
        if i < 5:
            cb.value = True
        weekday_checks.append(cb)
        weekdays_box.add(cb)
    box.add(weekdays_box)

    # Recurrence options
    recur_box = toga.Box(style=Pack(direction=ROW, padding_bottom=10))
    recur_box.add(toga.Label('Recurrencia: ', style=Pack(padding_right=6)))
    recur_choice = toga.Selection(items=['None', 'Weekly', 'Monthly', 'RRULE'], style=Pack(width=140))
    recur_choice.value = 'None'
    recur_box.add(recur_choice)
    recur_interval = toga.NumberInput(value=1, style=Pack(width=80))
    recur_box.add(toga.Label('Intervalo:', style=Pack(padding_left=6, padding_right=6)))
    recur_box.add(recur_interval)
    recur_monthday = toga.NumberInput(value=datetime.now().day, style=Pack(width=80))
    recur_box.add(toga.Label('Día mes:', style=Pack(padding_left=6, padding_right=6)))
    recur_box.add(recur_monthday)
    recur_rrule = toga.TextInput(placeholder='Ej: RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10', style=Pack(flex=1))
    recur_box.add(recur_rrule)
    box.add(recur_box)

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

    # Ask time for alarm
    time_dialog = app.main_window.question_dialog('Hora', 'Ingrese la hora de la alarma en formato HH:MM (24h)')
    if not time_dialog:
        return
    try:
        hh, mm = [int(x) for x in time_dialog.split(':')]
    except Exception:
        app.main_window.info_dialog('Error', 'Formato de hora inválido')
        return

    # Ask number of occurrences to schedule
    occ_dialog = app.main_window.question_dialog('Ocurrencias', '¿Cuántas próximas alarmas desea programar? (ej: 10)')
    if not occ_dialog:
        return
    try:
        occurrences = int(occ_dialog)
        if occurrences <= 0:
            raise ValueError()
    except Exception:
        app.main_window.info_dialog('Error', 'Número de ocurrencias inválido')
        return

    # Schedule recurring workday alarms (skipping weekends and feriados)
    try:
        # gather selected weekdays
        selected_weekdays = set(i for i, cb in enumerate(weekday_checks) if cb.value)
        if not selected_weekdays:
            app.main_window.info_dialog('Error', 'Seleccione al menos un día de la semana')
            return

        # Build recurrence rule
        recur_type = recur_choice.value
        rule = None
        if recur_type == 'Weekly':
            rule = {'type': 'weekly', 'interval': int(recur_interval.value), 'weekdays': selected_weekdays}
        elif recur_type == 'Monthly':
            rule = {'type': 'monthly', 'bymonthday': int(recur_monthday.value)}
        elif recur_type == 'RRULE':
            rule = {'type': 'rrule', 'rrule': recur_rrule.value}

        if rule:
            scheduled = scheduler.schedule_with_rule(conn, country_code, hour=hh, minute=mm, occurrences=occurrences, rule=rule)
        else:
            scheduled = scheduler.schedule_recurring_workday_alarms(conn, country_code, hour=hh, minute=mm, occurrences=occurrences, weekdays=selected_weekdays)
        app.main_window.info_dialog('Programado', f'Se programaron {scheduled} alarmas laborales')
    except Exception as e:
        app.main_window.info_dialog('Error', f'No se pudo programar: {e}')


def main():
    return toga.App('Alarma Laboral', 'org.example.alarma', startup=build)


if __name__ == '__main__':
    main().main_loop()
