# Solar AI Backend

FastAPI backend providing:

1. Chatbot with live weather context (LangGraph + Google Gemini model)
2. Solar PV hourly power prediction using a pre-trained scikit-learn model (`solar_power_prediction.pkl`)
3. Real‑time IoT sensor data ingestion via MQTT (ESP32 publishing to `emqx/esp32`)

Main entrypoint: `main.py`

---

## Features

- `/chat` enriches user prompts with current weather (Open‑Meteo) before invoking the LLM.
- `/predict` fetches 24h forecast (temperature + shortwave radiation) and predicts hourly PV power plus daily total.
- `/sensor` exposes the most recent MQTT payload (JSON if ESP32 publishes JSON, else raw string).
- Dockerized (Python 3.12 slim) with health check hitting `/predict`.

## Tech Stack

- FastAPI + Uvicorn
- LangChain / LangGraph + Google Generative AI (Gemini 2.5 Flash)
- scikit-learn model (`solar_power_prediction.pkl`) loaded with `joblib`
- Open‑Meteo public API (no key required)
- Paho MQTT client (background subscriber)

## Directory (backend-relevant)

```
main.py              # FastAPI app & routes
chatbotengine.py     # LangGraph pipeline + weather context injection
esp32mqtt.py         # MQTT subscriber storing latest_data
mqtt.py              # (Alternative simple subscriber - currently unused by main.py)
solar_power_prediction.pkl  # Trained regression/model artifact
dockerfile           # Container build instructions
requirements.txt     # Python dependencies
```

## Environment Variables

Create a `.env` (loaded in `chatbotengine.py`):

```
GOOGLE_API_KEY=your_google_genai_key
# (Optional) Other provider keys if you extend models
```

Variable `GOOGLE_API_KEY` is required for the Gemini model. (The code also looks for `api_key` but currently only `GOOGLE_API_KEY` is used.)

## Installation (Local)

Pre-req: Python 3.12, pip, MQTT broker reachable (default uses public test.mosquitto.org)

```
pip install --upgrade pip
pip install -r requirements.txt
```

Run (dev):

```
uvicorn main:app --reload --port 8000
```

Access automatic docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker

Build & run:

```
docker build -t solar-backend .
docker run -p 8000:8000 --env-file .env solar-backend
```

## API Endpoints

### 1. Chat
POST `/chat`

Request JSON:
```
{ "message": "Berapa potensi listrik hari ini?", "thread_id": "user123" }
```
Response:
```
{ "thread_id": "user123", "response": "...model reply with weather context..." }
```

### 2. Prediction
GET `/predict`

Response:
```
{
	"data": [
		{"time": "2025-08-23T00:00", "ambient_temperature": 22.1, "module_temperature": 25.5, "irradiance": 110.2, "predicted_power": 45.7},
		... 24 hourly rows ...
	],
	"total_energy": 1234.56
}
```

Model Input Shape (per hour): `[ambient_temperature, module_temperature, irradiance]`

Module temperature is heuristically estimated: `T_module = T_ambient + irradiance * 0.03` (simple NOCT approximation).

### 3. Sensor Data
GET `/sensor`

Response examples:
```
{"temperature": 28.5, "voltage": 12.4}
```
or
```
{"value": "raw-string-payload"}
```

If nothing received yet:
```
{"error": "No data received yet"}
```

## Sample curl Commands

```
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"Halo\"}"
curl http://localhost:8000/predict
curl http://localhost:8000/sensor
```

## MQTT Integration

- Broker: `test.mosquitto.org`
- Topic: `emqx/esp32`
- Subscriber starts automatically when `esp32mqtt.py` is imported by `main.py`.
- Publish example (JSON):
```
mosquitto_pub -h test.mosquitto.org -t emqx/esp32 -m '{"temperature":28.7,"voltage":12.6}'
```

## Chatbot Flow (LangGraph)

1. Fetch weather JSON (Open‑Meteo)
2. Format summary into a `SystemMessage`
3. Prepend to conversation state
4. Invoke Gemini model via LangChain `init_chat_model`
5. Persist conversation thread in `MemorySaver` using `thread_id`

## Model Artifact (`solar_power_prediction.pkl`)

Assumed scikit-learn regressor. If you retrain, ensure you keep the same input ordering and replace the file.

## Minimal Dependency Subset (if optimizing)

Core runtime needs roughly: `fastapi`, `uvicorn`, `joblib`, `scikit-learn`, `requests`, `paho-mqtt`, `langchain-core`, `langgraph`, `langchain-google-genai`, `python-dotenv`.

The current `requirements.txt` is broad (RAG / DB / extras). Prune for production to reduce image size and attack surface.

## Production Notes

- Pin only required packages; consider a slimmer base (e.g. `python:3.12-alpine` with necessary build deps) after verifying wheels.
- Add request timeouts & exception handlers (e.g., for external API failures) for resilience.
- Replace public MQTT broker with a secured one (TLS, auth) before deployment.
- Rate limit `/chat` and cache `/predict` for a forecast period to reduce external calls / model invocations.
- Add logging & monitoring (structured logs, OpenTelemetry already partially included via deps).

## Extending

- Add database persistence (e.g., timeseries of predictions / sensor values)
- Incorporate real irradiance sensor & compare predicted vs actual
- Enhance weather context with derived KPIs (capacity factor estimate)
- Internationalize responses

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 / model error | Missing `GOOGLE_API_KEY` | Set in `.env` |
| `/sensor` empty | No MQTT publish yet | Publish a test JSON message |
| Slow startup | Large dependency set | Prune `requirements.txt` |
| Docker healthcheck failing | Forecast API unreachable | Allow retries / widen health logic |


