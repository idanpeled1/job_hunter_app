"""
job_hunter.py
~~~~~~~~~~~~~~~~

Core logic for the Job Hunter application.  This module provides a simple
interface for querying the Google Programmable Search Engine (CSE) and
ranking results based on the user’s configuration.  It supports both
command‑line usage and programmatic import from the Flask web UI.

The search algorithm was inspired by a bespoke system built for Hebrew
job‑seekers focusing on the social and public sectors.  It can be adapted
to other use‑cases by tweaking the configuration.

The module exposes the following functions:

* `load_config(path)` – read a YAML configuration file
* `search_jobs(config, query=None)` – perform a search and return a list
  of job dictionaries with scores
* `compute_score(job, config)` – compute the relevance of a result
* `save_results(jobs, output_path)` – write results to a Markdown file

Running the script directly will execute a search and write the results to
`daily_jobs.md`.
"""

import os
import re
import json
import yaml
import requests
from urllib.parse import urlencode
from typing import List, Dict, Any, Optional


def load_config(path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration.

    Returns:
        A dictionary containing the configuration.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def search_jobs(config: Dict[str, Any], query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for jobs using Google Programmable Search.

    This function iterates over the configured sites and executes a search
    query for each.  Results are deduplicated on their link.  If a custom
    query string is provided, it overrides the default keyword
    concatenation from the configuration.

    Args:
        config: Configuration dictionary as returned from `load_config`.
        query: Optional search string.  If ``None``, a query will be
            constructed from the keywords in the configuration.

    Returns:
        A list of job dictionaries sorted by descending score.
    """
    api_key = os.getenv('GOOGLE_CSE_KEY') or config.get('google_cse_key')
    cx = os.getenv('GOOGLE_CSE_CX') or config.get('google_cse_cx')
    if not api_key or not cx:
        raise RuntimeError(
            "Google CSE credentials are missing.  Set GOOGLE_CSE_KEY and GOOGLE_CSE_CX "
            "environment variables or define them in config.yaml."
        )

    sites = config.get('sites', [])
    keywords_all = config.get('keywords_all', [])
    keywords_any = config.get('keywords_any', [])
    locations = config.get('locations', [])

    # Base query: either supplied by the caller or built from keywords
    if query:
        base_query = query
    else:
        base_query_parts = []
        # Join all mandatory keywords with AND for Google search
        if keywords_all:
            base_query_parts.append(' '.join(keywords_all))
        # Join optional keywords with OR
        if keywords_any:
            base_query_parts.append(' '.join(keywords_any))
        base_query = ' '.join(base_query_parts).strip()
    if locations:
        # Append locations to the query to boost local results
        base_query += ' ' + ' '.join(locations)

    results: Dict[str, Dict[str, Any]] = {}

    for site in sites:
        if not site:
            continue
        # Compose site‑specific search: restrict to domain
        query_str = f"{base_query} site:{site}"
        params = {
            'key': api_key,
            'cx': cx,
            'q': query_str,
            'num': 10,
        }
        url = 'https://www.googleapis.com/customsearch/v1?' + urlencode(params)
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # Skip site on errors
            continue
        for item in data.get('items', []):
            link = item.get('link')
            if not link:
                continue
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            source = site
            job = {'title': title, 'link': link, 'snippet': snippet, 'source': source}
            # Compute a relevance score
            job['score'] = compute_score(job, config)
            # Deduplicate – keep the highest scoring item per link
            prev = results.get(link)
            if prev is None or job['score'] > prev['score']:
                results[link] = job

    # Filter out jobs from commercial sites that do not mention ESG or partnerships
    filtered_results = []
    for job in results.values():
        text = (job['title'] + ' ' + job['snippet']).lower()
        # Identify public/non‑profit domains by patterns
        public_patterns = re.compile(r"(\.gov\.il|\.muni\.il|\.org\.il)")
        if not public_patterns.search(job['link']):
            # Corporate site – require ESG/partnership keywords
            corporate_terms = ['esg', 'קיימות', 'אחריות תאגידית', 'partnership', 'partnerships', 'שותפויות']
            if not any(term in text for term in corporate_terms):
                continue
        filtered_results.append(job)

    # Sort by score descending
    return sorted(filtered_results, key=lambda x: x['score'], reverse=True)


def compute_score(job: Dict[str, Any], config: Dict[str, Any]) -> float:
    """Compute a relevance score for a job item.

    The score is based on keyword presence, location hints and avoidance
    terms.  Positive keywords increase the score while avoidance words
    decrease it.  Additional weighting can be customised here.

    Args:
        job: A dictionary with `title`, `snippet` and other fields.
        config: Configuration dictionary.

    Returns:
        A floating‑point score.  Higher is more relevant.
    """
    score = 0.0
    text = (job.get('title', '') + ' ' + job.get('snippet', '')).lower()
    keywords_all = config.get('keywords_all', [])
    keywords_any = config.get('keywords_any', [])
    locations = config.get('locations', [])
    avoid = config.get('avoid', [])

    # Mandatory keywords must all appear – if not, no score boost
    if keywords_all:
        if all(kw.lower() in text for kw in keywords_all):
            score += 2.0
    # Add one point for each optional keyword present
    for kw in keywords_any:
        if kw.lower() in text:
            score += 1.0
    # Location hints
    for loc in locations:
        if loc.lower() in text:
            score += 0.5
    # Penalise avoidance terms
    for bad in avoid:
        if bad.lower() in text:
            score -= 1.0
    return score


def save_results(jobs: List[Dict[str, Any]], output_path: str) -> None:
    """Write jobs to a Markdown file.

    Args:
        jobs: A list of job dictionaries.
        output_path: The output file path.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Daily Jobs Digest\n\n')
        for job in jobs:
            title = job.get('title', 'Untitled')
            link = job.get('link', '#')
            source = job.get('source', '')
            snippet = job.get('snippet', '')
            score = job.get('score', 0)
            f.write(f"* [{title}]({link}) — {source} (score {score:.2f})\n")
            if snippet:
                f.write(f"  \n  {snippet}\n\n")


def main() -> None:
    """CLI entry point for the job hunter.

    Parses arguments, loads configuration, executes the search and writes
    the results to the specified output file.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Run job search and output results.')
    parser.add_argument('--config', default='config.yaml', help='Path to YAML configuration file')
    parser.add_argument('--output', default='daily_jobs.md', help='Output Markdown file')
    parser.add_argument('--query', help='Override query string')
    args = parser.parse_args()

    config = load_config(args.config)
    try:
        jobs = search_jobs(config, query=args.query)
    except Exception as exc:
        print(f"Error executing search: {exc}")
        return
    save_results(jobs, args.output)
    print(f"Saved {len(jobs)} jobs to {args.output}")


if __name__ == '__main__':
    main()
