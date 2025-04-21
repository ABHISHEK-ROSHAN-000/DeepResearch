import time
import ollama
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.markdown import Markdown
from dotenv import load_dotenv
import os

load_dotenv()

console = Console()

SUMMARIZE_MODEL = os.getenv("SUMMARIZE_MODEL")
FINAL_MODEL = os.getenv("FINAL_MODEL")
WIDTH = int(os.getenv("WIDTH")) # no.of webside visit for single query
DEPTH = int(os.getenv("DEPTH")) # no.of loop for self question
# Total website visited is WIDTH x DEPTH

# ----- Research Tool Functions -----
def ollama_chat(prompt, system=None, model="qwen2.5:1.5b"):
    """
    Sends a chat message to the specified Ollama model.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = ollama.chat(model=model, messages=messages)
    return response['message']['content']


def search_web(query, max_results=3):
    """
    Returns a list of URLs from DuckDuckGo search results for the given query.
    """

    skip_domains = ["google.com", "google.co", "google.", "webcache.googleusercontent.com"]

    def is_valid_url(url):
        return all(skip not in url for skip in skip_domains)
    
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, region='wt-wt', safesearch='moderate', max_results=max_results):
            url = r.get('href', '')
            if is_valid_url(url):
                results.append(url)
    return results


def fetch_text_from_url(url):
    """
    Fetches and returns up to 4000 characters of text from the given URL.
    """
    try:
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text[:4000]
    except Exception as e:
        console.print(f"[red][!] Error fetching {url}: {e}[/red]")
        return ""


def query_generator(main_question):
    prompt = f"Generate exactly one Google search query for an in-depth investigation of the following question:\n\n'{main_question}'\n\nReturn them as a numbered list."
    response = ollama_chat(prompt, model=SUMMARIZE_MODEL)
    return [line.strip("0123456789). ") for line in response.strip().split("\n") if line.strip()]


def summarize_article(text, url):
    prompt = (
        f"Summarize the following article for research purposes. Include main points. "
        f"The source URL is: {url}\n\n{text}"
    )
    return ollama_chat(prompt, model=SUMMARIZE_MODEL)

def identify_missing_info(summaries, main_question):
    """
        Given existing summaries and the main question, ask the LLM to list missing subtopics or gaps.
    """
    combined = "\n-----\n".join(summaries)
    prompt = (
        f"You are conducting research on: {main_question}\n"
        f"Here are summaries of relevant articles:\n{combined}\n\n"
        "Identify one key aspects or subtopics of the main question that are NOT covered in these summaries"
        " and would be important to investigate. Return each as a short phrase in a numbered list."
    )

    response = ollama_chat(prompt, model=SUMMARIZE_MODEL)
    
    return [line.strip("0123456789). ") for line in response.strip().split("\n") if line.strip()]


def deep_research(question, depth=3):
    """
    Runs a multi-step deep research pipeline:
      1. Sub-questions
      2. Web search & fetch
      3. Summarize articles
      4. Synthesize final report
    Returns the final synthesized report string.
    """
    console.print(f"\n[cyan]🔍 Main Question:[/] {question}")
    subqs = query_generator(question)
    console.print(f"[magenta]\n📌 Sub-questions:[/] {subqs[0]}\n")

    all_summaries = []
    sq = subqs[0]
    console.print(f"[cyan]🔎 Researching-main:[/] {sq}")
    urls = search_web(sq, max_results=WIDTH)
    for url in urls:
        console.print(f"   ▪ Fetching: {url}")
        text = fetch_text_from_url(url)
        if text:
            summary = summarize_article(text, url)
            all_summaries.append(summary)

    for i in range(depth):
        missing_query = identify_missing_info(all_summaries, question)
        missing_query = missing_query[0]
        console.print(f"[cyan]🔎 Researching:[/] {missing_query}")
        sub_query = query_generator(f"{question}: {missing_query}")
        sub_urls = search_web(sub_query[0], max_results=WIDTH)
        for url in sub_urls:
                console.print(f"   ▪ Fetching: {url}")
                text = fetch_text_from_url(url)
                if text:
                    summary = summarize_article(text, url)
                    all_summaries.append(summary)
        

    console.print("\n[green]🧠 Synthesizing final report...[/]")
    return all_summaries

def stream_synthesized_report_in_panel(question, summaries, system=None, model="qwen2.5:latest"):
    """
    Streams final synthesis from Ollama into a live Rich panel.
    """
    # Build system/user messages
    messages = []
    if system:
        messages.append({"role":"system","content":system})
    # user prompt for synthesis
    synthesis_prompt = (
        f"You are a research assistant. Based on the following article summaries, "
        f"synthesize a complete answer to the main question:\n\n'{question}'\n\n"
        f"Summaries:\n" + "\n\n".join(summaries) +
        "Give Report in this Format:"
        "\n### Title Page"
        "\n- Title"
        "\n- Abstract (Executive Summary)"
        "\n- Table of Contents"
        "\n### Main Body"
        "\n1. Introduction"
        "\n2. Literature Review"
        "\n3. Methodology"
        "\n4. Results"
        "\n5. Discussion"
        "\n6. Conclusion"
        "\n7. References"
        "\n\nEach section should contain comprehensive and detailed paragraphs, thoroughly addressing the topic with in-depth analysis and examples."
        "\nDo not start your answer with thank you for providing the summaries."
    )
    messages.append({"role":"user","content":synthesis_prompt})

    streamed = ""
    with Live(refresh_per_second=20) as live:
        for chunk in ollama.chat(model=model, messages=messages, stream=True):
            # each chunk is a dict with 'message':{'content':...}
            content = chunk.get('message', {}).get('content', '')
            streamed += content
            live.update(Markdown(streamed))
    time.sleep(0.3)


def chat():
    """Main chat loop integrating deep research with Rich UI."""
    console.print(Panel("[bold cyan]          DeepResearch[/bold cyan]\n\nMade with love by [bold]Abhishek Roshan[/bold]\n\n       Type '/bye' to quit.", expand=False))
    while True:
        user_input = Prompt.ask("[bold green]\nYou[/bold green]")
        if user_input.strip().lower() == "/bye":
            console.print("[bold red]Exiting chat...[/bold red]")
            break
        # Run deep research pipeline on user input
        summaries = deep_research(user_input, depth=DEPTH)
        console.print()  # spacing
        console.rule("[bold cyan]DeepResearch Report.[/bold cyan]", align="left")
        console.print()
        stream_synthesized_report_in_panel(user_input, summaries, model=FINAL_MODEL)
        console.print()
        console.rule("[bold cyan]Report Fineshed.[/bold cyan]", align="left")
        console.print()

if __name__ == "__main__":
    chat()
