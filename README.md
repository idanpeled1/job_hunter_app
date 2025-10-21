# Job Hunter App

This repository contains a simple job‑search tool and web interface that can be
run locally or deployed to a server.  It uses the Google Programmable Search
Engine (CSE) API to find positions across a list of preconfigured websites
and ranks them according to supplied keywords.  The system was originally
designed to help job seekers in Israel discover public‑sector and
social‑impact roles, but it can be adapted to other domains by adjusting
the configuration.

## Features

* **Customisable queries** – configure your search terms, locations and
  preferred websites in `config.yaml`.
* **Google CSE integration** – queries are executed against the Google
  Programmable Search API (you provide your own API key and CX ID).
* **Duplicate removal and scoring** – results are deduplicated and scored
  based on how many of your keywords appear in the title and snippet.
* **Command‑line tool** – run `python job_hunter.py` to produce a Markdown
  digest of the day’s jobs.
* **Web interface** – a small Flask app exposes a search form and displays
  the results directly in a browser, making it easier for others to use
  without touching the command line.

## Prerequisites

1. Python 3.8 or newer.
2. A Google Programmable Search Engine (CSE) with the sites you want to
   search indexed.  Note the **API key** (`GOOGLE_CSE_KEY`) and the **CX**
   identifier (`GOOGLE_CSE_CX`).  You can create a CSE at
   <https://programmablesearchengine.google.com/>.

## Installation

Clone or download this repository and install the dependencies:

```sh
git clone https://example.com/job_hunter_app.git
cd job_hunter_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `config.yaml.example` to `config.yaml` and adjust it to reflect
your search preferences:

```sh
cp config.yaml.example config.yaml
${EDITOR:-nano} config.yaml
```

Set your Google CSE API key and CX in your shell, or hard‑code them in
`config.yaml`:

```sh
export GOOGLE_CSE_KEY=your_api_key
export GOOGLE_CSE_CX=your_cx_id
```

## Command‑line usage

Run the crawler on demand:

```sh
python job_hunter.py --config config.yaml --output daily_jobs.md --query "ESG partnerships"
```

The program will fetch results from the configured sites and save them to
`daily_jobs.md`.  Each entry includes a title, link and short summary.

## Web interface

To launch the Flask app locally, run:

```sh
python app.py
```

By default, the server listens on `http://0.0.0.0:5000`.  Open that URL in a
browser and you will see a simple search form.  Enter keywords and click
“Search” to display the top results.  You can deploy this Flask app to a
platform such as Heroku, AWS, or your own server to share it with others.

## Configuration

The `config.yaml` file controls what the crawler looks for.  An example
configuration (`config.yaml.example`) is included.  The most important
sections are:

* `sites` – a list of domains to search.  Keep this list small and relevant
  for best results.  Wildcards are not supported by Google CSE.
* `keywords_all` – every word in this list must appear in the job title or
  snippet for the item to receive a high score.
* `keywords_any` – items receive additional points for each of these terms
  found in the title or snippet.
* `locations` – optional list of location terms to boost relevant results.
* `avoid` – optional list of words to penalise or exclude (e.g. “סטודנט”).

You can also set `google_cse_key` and `google_cse_cx` in the YAML file if
you prefer not to use environment variables.  Environment variables take
precedence if both are present.

## Caveats

* The Google CSE API imposes daily usage quotas.  Please monitor your
  usage and adjust queries accordingly.
* Deep crawling rules (scraping individual job boards) are not included in
  this minimal public version.  You can extend the code in
  `job_hunter.py` to add site‑specific parsers if required.
* This project is provided as a starting point.  Feel free to modify it
  according to your needs and contributions are welcome.
