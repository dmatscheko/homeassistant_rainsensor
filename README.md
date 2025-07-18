# Tipping Bucket Rain Gauge Sensor for Home Assistant

This is a custom integration for Home Assistant that creates sensor entities to calculate rainfall based on a binary sensor from a tipping bucket rain gauge (e.g., connected via ESPHome or similar). It is specifically designed for tipping bucket rain gauges where the binary sensor toggles on each bucket tip.

## Features
- Two rainfall sensors: one for daily rainfall (resets at midnight), one for cumulative total rainfall (steadily increasing, no reset).
- Two tilt count sensors: one for daily tilt count (resets at midnight), one for cumulative total tilt count (steadily increasing, no reset).
- Rainfall rate sensor (mm/h, based on last hour, full time only).
- Separate on and off count sensors for daily and total (persisted via database states).
- Configurable volume per tilt for "on" and "off" states (for dual-bucket gauges).
- Funnel diameter for accurate rainfall depth calculation.
- Daily reset at midnight for the daily sensors.
- Persistence across restarts using database last entries for count sensors.
- Options flow for adjusting parameters without re-adding the integration.
- Optional missed flip recovery for unreliable binary sensors (may lead to overcounting in some cases).
- Rainfall rate persistence across restarts by reconstructing tip history from recorder.

## Installation

### Via HACS (Recommended)
1. Open HACS in Home Assistant (if not installed, add it first via Settings > Devices & Services).
2. Go to Integrations > Click the three dots (top right) > Custom repositories.
3. Add `https://github.com/dmatscheko/homeassistant_rainsensor` as the repository URL, select "Integration" as the category, and click Add.
4. Search for "Rain Sensor" in HACS and install it.
5. Restart Home Assistant.
6. Go to Settings > Devices & Services > Add Integration > Rain Sensor.

### Manual Installation
1. Copy the `custom_components/rainsensor` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to Settings > Devices & Services > Add Integration > Rain Sensor.

## Configuration
- **Rain Sensor Entity**: Select a binary_sensor that toggles on each tip of the tipping bucket rain gauge.
- **Volume per On/Off Switch (ml)**: The volume of water per tip in each state.
- **Funnel Diameter (mm)**: The diameter of the rain gauge funnel.
- **Sensor Name**: Base name for the sensor entities (will append " Daily" and " Total" for rainfall, and " Daily Tilt Count" and " Total Tilt Count" for tilts).
- **Enable Missed Flip Recovery**: Optional (default: false). Enables recovery for missed flips on unreliable sensors, but can have side effects like counting too many flips if the sensor fires unnecessary same-state events.

The rainfall sensors will output in mm. The tilt count sensors will output in "tips". The daily sensors reset daily; the total sensors accumulate indefinitely.

## Troubleshooting
- Ensure the monitored binary_sensor is correctly toggling on each tip event from the tipping bucket.
- Check HA logs for errors (search for "rainsensor").
- If counts are inaccurate, verify the binary_sensor doesn't fire unnecessary events (e.g., attribute updates without state change).
- If using missed flip recovery, be aware it assumes missed even-numbered flips on same-state events, which could lead to overcounting. Disable if your sensor is reliable but noisy.
- Ensure recorder is enabled for persistence and rate history reconstruction.

For issues, open an issue on GitHub.

## Development
This assumes you have `uv` installed globally (e.g., via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`. Check the [official docs](https://docs.astral.sh/uv/) for details).

### Prerequisites with `uv`
- Python 3.13+.
- Install dependencies (including dev extras) and create a virtual environment:
  ```
  uv sync --extra dev
  ```

### Run Tests
Run the test command:
```
uv run pytest
```

- **Coverage**: `uv run pytest --cov=custom_components/rainsensor --cov-report=html` (view in `htmlcov/index.html`).
- **Verbose**: `uv run pytest -v`.
- **Specific Test**: `uv run pytest tests/test_config_flow.py` or `uv run pytest tests/test_config_flow.py::test_user_flow_success`.
- **Markers**: `uv run pytest -m nohomeassistant`.

### Linting
After installing dev dependencies, you can run:

- `uv run ruff format .` to format code.
- `uv run pre-commit run --all-files` to run all pre-commit hooks (you can set them up to run before every commit with `uv run pre-commit install`).
