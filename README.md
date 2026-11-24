# AI Trust Calibration Assistant

README prose word count: 616 (whitespace count; headings, code blocks and this line excluded).

## Project status

This local educational prototype supports low-risk English information seeking. A user asks a free question or selects one of five fixed claims, reads an AI response, records an initial judgment, optionally searches for evidence, and makes a final judgment. A session dashboard shows judgments and search activity.

The five SI claims have manually checked NIST reference answers, revealed after the final judgment. The system compares the user's judgments with the claim key; “Unsure” is reported separately. Free questions are not automatically graded. These summaries do not establish trust calibration or prove that the interface improves reliance.

## Technology and files

- **Python and Flask:** local server, session state and API calls (`app.py`).
- **HTML, CSS and JavaScript:** interface and interaction (`templates/`, `static/`).
- **DeepSeek API:** default response generation; OpenAI is an alternative. A personal API key and model access are required.
- **English Wikipedia API:** independent search results and links; it is not an automatic fact-checker.
- **MathJax:** browser-side formula rendering loaded from a CDN, with a basic text fallback if unavailable.
- **Tests:** `tests/` uses pytest and mocked external services. Dependencies are listed in `requirements.txt`.

## Setup and running

Requires Python 3.10 or later, internet access and an API key for the chosen provider. API use may incur charges. In a terminal opened in this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
open -e .env
```

Run the `cp` command only when creating `.env` for the first time: it replaces an existing file. In `.env`, set `AI_PROVIDER=deepseek` and replace `DEEPSEEK_API_KEY` with your own key. For OpenAI, select `AI_PROVIDER=openai` and set `OPENAI_API_KEY`. Existing environment variables take precedence over `.env`.

```bash
python app.py
```

Open http://127.0.0.1:5000. Stop the server with Control+C. Run tests with `python -m pytest -q`. Never commit `.env`, API keys or `.venv` to a repository; `.env.example` contains placeholders only.

## Boundaries

Generated explanations and Wikipedia results are displayed separately. Search results may be irrelevant or incomplete; a link click does not prove a source was read or supports a claim. Search failure is shown without fabricated evidence. Model-stated uncertainty is qualitative and uncalibrated, not a probability of correctness. The NIST key evaluates the fixed claim, not every sentence of an AI answer. Its source is [NIST SI Brochure, section 2](https://www.nist.gov/pml/special-publication-330/sp-330-section-2), checked 22 November 2026.

Session data is stored in server memory and disappears on restart. Refreshing retains dashboard history but does not restore unfinished controls. There is no database, export, automatic source-quality assessment, calibrated model confidence or formal user study. The provider receives the question or claim; Wikipedia receives search terms. Do not enter sensitive information.

## Development record and AI assistance

- **Design:** I chose a real AI API, low-risk questions and an interaction with initial and final judgments. Feedback, user control, cognitive load and provenance informed the design.
- **11 November 2026:** I asked OpenAI Codex to generate the Flask application, interface and tests. Considering the cost of token usage, I chose to replace the original OpenAI API configuration with DeepSeek, with implementation assistance from Codex.
- **19 November 2026:** I added fixed-claim comparisons, session summaries and clearer English search guidance. Formatting support was also added for bold text and mathematical expressions.
- **Checks:** I configured DeepSeek, ran the application, observed an AI response and inspected Wikipedia results after editing search terms. Four automated tests passed using mocked providers and retrieval, most recently when the README was reviewed; they do not verify live API reliability. No formal user study was conducted.
- **Report:** Codex assisted with the report and references. I remain responsible for checking the sources, design choices and claims. Add any further checks or adaptations actually performed, and link relevant commits when available.
