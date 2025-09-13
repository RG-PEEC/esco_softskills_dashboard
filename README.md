# Soft-Skills Dashboard

Streamlit application that detects and visualizes soft skills in text using a **local LLM** served by **LM Studio**. Developed on macOS. Intended to be cross-platform (Linux and Windows), but not yet tested on those systems.

---

## Features

* Local inference via LM Studio (no cloud dependency)
* Configurable model (default: `openai/gpt-oss-20b`)
* Interactive UI for text review and soft-skill outputs
* Clear separation of UI, data, and LLM client code
* Reproducible setup via `requirements.txt`

---

## Quick Start

1. **Install prerequisites**

   * Python **3.11+**
   * LM Studio (desktop app)

2. **Start LM Studio**

   * Download or load the model **`openai/gpt-oss-20b`**.
   * Start the local server with the default settings.
   * Verify the base URL: `http://localhost:1234/v1`.

3. **Set up the project**

   ```bash
   git clone <your-repo-url>
   cd <your-repo>
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   # .venv\Scripts\Activate.ps1

   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   streamlit run app.py
   ```

   Open the URL shown in the terminal (default: `http://localhost:8501`).

---

## Requirements

* **Python:** 3.11 or later
* **LM Studio:** running locally with the model loaded
* **Model:** `openai/gpt-oss-20b` (must be available in LM Studio)
* **Python packages:** listed in `requirements.txt`
  Typical stack includes:

  * `streamlit`
  * `pandas`
  * `plotly`
  * `requests`
  * `streamlit-autorefresh`

> Install exactly via `pip install -r requirements.txt`.

---

## Configuration

Change Model in functions.py on top

```python
lm_studio_client = LMStudioClient(model="openai/gpt-oss-20b") # change model here
```


---

## Project Structure

```
.
├─ app.py                     # Streamlit entrypoint
├─ functions.py               # UI helpers, highlighting, rendering
├─ lm_studio_client.py        # HTTP client for LM Studio server
├─ data.py                    # Demo data (e.g., texts, personas)
├─ requirements.txt
└─ README.md
```

* **`app.py`**: orchestrates UI, calls the LLM client, renders outputs.
* **`functions.py`**: formatting, tooltip logic, skill highlighting.
* **`lm_studio_client.py`**: minimal wrapper around the LM Studio REST API.
* **`data.py`**: example `pandas.DataFrame` and configuration objects used by the app.

---

## How It Works

1. The user interface runs in Streamlit.
2. The app sends prompts to the local LM Studio server at `http://127.0.0.1:1234`.
3. The loaded model (`openai/gpt-oss-20b`) returns structured text relevant to soft-skill extraction.
4. The UI formats results into highlights, tooltips, and tables.

---

## Usage Notes

* Keep LM Studio open with the server running while you use the app.
* Load the model **before** starting the Streamlit app for faster first response.
* Large models on CPU can be slow. Expect higher latency without a strong GPU.

---

## Troubleshooting

**The app cannot reach LM Studio**

* Confirm the server is running in LM Studio (“Start Server”).
* Verify the URL matches `LMSTUDIO_BASE_URL` (default `http://localhost:1234/v1`).
* Check firewall or port conflicts on `1234`.

**Model not loaded or wrong name**

* In LM Studio, ensure **`openai/gpt-oss-20b`** is selected and loaded.
* Match the exact model name used by your client code.

**`ModuleNotFoundError` or package errors**

* Activate the virtual environment.
* Re-run `pip install -r requirements.txt`.

**Streamlit does not open a browser tab**

* Manually navigate to the URL shown in the terminal, typically `http://localhost:8501`.

---

## Development

* Use a virtual environment for isolation.
* Keep UI logic in `app.py` thin; push formatting and parsing into `functions.py`.
* For configuration, prefer environment variables over hard-coding.

---

## Platform Support

* Built on **macOS**.
* Expected to run on **Linux** and **Windows** with Python 3.11+ and LM Studio, but not yet verified.

---

## License

Add a license file (e.g., `LICENSE`) and reference it here.

---

## Acknowledgments

* LM Studio for local model serving.
* Open-source model authors for `openai/gpt-oss-20b`.
