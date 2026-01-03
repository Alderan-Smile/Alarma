# Alarma Laboral

Proyecto para programar alarmas en días laborales, saltando fines de semana y feriados.

Cómo ejecutar en escritorio (Windows/Linux/macOS)

1. Crear un entorno virtual e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # PowerShell
pip install -r requirements.txt
```

2. Ejecutar la vista Toga:

```powershell
python Vista/toga_view.py
```

Comportamiento en escritorio: los eventos se almacenan en `Resources/calendar_events.json`.

Empaquetado para Android (Briefcase)

1. Instalar Briefcase e inicializar el proyecto (revisar docs de Briefcase/Toga):

```powershell
pip install briefcase
briefcase create android
briefcase build android
briefcase run android
```

2. Android specifics:
- Debes implementar permisos runtime `WRITE_CALENDAR` y `READ_CALENDAR`.
- `Controlador/calendar_adapters/android_adapter.py` contiene un ejemplo con `pyjnius`. Ajusta `calendar_id` y manejo de permisos.

Recomendación para producción
- Para alarmas recurrentes completas en Android, usa el `AlarmManager` o crea eventos recurrentes en el calendario.
- Para excluir feriados, esta implementación crea eventos individuales para cada fecha laboral futura.

Si quieres, implemento la gestión de permisos y la selección automática de `calendar_id` en Android.
