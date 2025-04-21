## DeepResearch

**DeepResearch** is a command‑line research assistant built with Python that automates multi‑step web investigation, article summarization, and final report synthesis—all powered by Ollama LLMs and rich terminal output. It helps you dive deep into any question by iteratively generating subqueries, retrieving and summarizing content, identifying gaps, and stitching together a structured, publication‑ready report.

---

### Key Features

- **Automated Query Generation**  
  Uses an LLM (your `SUMMARIZE_MODEL`) to turn a broad question into targeted Google/DuckDuckGo search queries.

- **Iterative Deep Dives**  
  Conducts a configurable number of research loops (`WIDTH` × `DEPTH`), fetching multiple sources per subquestion and uncovering missing subtopics in each cycle.

- **Summarization Pipeline**  
  Retrieves web page text with BeautifulSoup, then summarizes articles via Ollama, keeping summaries concise and source‑attributed.

- **Gap Analysis**  
  Identifies unaddressed subtopics from existing summaries, automatically spawning new searches to fill in missing pieces.

- **Structured Synthesis**  
  Streams a final, richly formatted report into your terminal—complete with Title Page, Abstract, Table of Contents, and a six‑section body plus references—using Rich’s live Markdown panels.

- **Rich Terminal UI**  
  Powered by [Rich](https://github.com/Textualize/rich) for colored prompts, panels, progress updates, and live Markdown rendering.

---

### Architecture & Workflow

1. **Main Loop**  
   - Prompt user for a question  
   - Call `deep_research(question, depth)`  

2. **Subquestion Generation**  
   - `query_generator` asks the LLM to propose one focused search query  
   - Executes DuckDuckGo searches (via `duckduckgo_search`)  

3. **Fetch & Summarize**  
   - `fetch_text_from_url` scrapes paragraphs (up to 4,000 chars)  
   - `summarize_article` passes raw text to the LLM for summary  

4. **Gap Identification**  
   - `identify_missing_info` compares summaries against the main question  
   - Generates new subtopics to explore in subsequent loops  

5. **Synthesis**  
   - Compiles all summaries and streams a final, structured report with `stream_synthesized_report_in_panel`  

---

### Installation & Requirements

- **Python 3.9+**  
- **PIP Packages**:  
  ```bash
  pip install ollama duckduckgo_search requests beautifulsoup4 rich python-dotenv
  ```
- **Ollama Models**:  
  Define `SUMMARIZE_MODEL` and `FINAL_MODEL` in a `.env` file, e.g.:  
  ```
  SUMMARIZE_MODEL=qwen2.5:1.5b
  FINAL_MODEL=qwen2.5:latest
  WIDTH=3
  DEPTH=2
  ```

---

### Usage

Run the tool from your terminal:
```bash
python deep_research.py
```
- You’ll be greeted by the DeepResearch banner.  
- Type your research question and watch it automatically gather, summarize, and synthesize into a polished report.  
- Exit anytime by typing `/bye`.

---

DeepResearch streamlines what normally takes hours of manual searching and reading into just minutes—perfect for academics, journalists, or anyone who needs an AI‑powered research assistant.
