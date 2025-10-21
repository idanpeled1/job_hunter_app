"""
A minimal Flask application exposing the job search functionality via a web
interface.  Users can enter free‑text queries and see the results ranked
by relevance.  This app loads its configuration once at startup and
reuses it for all requests.  To update the configuration, edit
`config.yaml` and restart the server.

Running this module directly with `python app.py` will launch a local
development server listening on port 5000.  To deploy in production,
consider using a WSGI server such as Gunicorn.
"""

from flask import Flask, render_template, request
import os
from pathlib import Path
from job_hunter import load_config, search_jobs


app = Flask(__name__)

# Load configuration at startup.  If config.yaml does not exist, use
# the example configuration.  You can point to a different file via
# the JOB_HUNTER_CONFIG environment variable.
CONFIG_PATH = os.getenv('JOB_HUNTER_CONFIG', 'config.yaml')
if not Path(CONFIG_PATH).is_file():
    # Fallback to example config
    CONFIG_PATH = 'config.yaml.example'
    if not Path(CONFIG_PATH).is_file():
        raise FileNotFoundError('No configuration file found.')

CONFIG = load_config(CONFIG_PATH)


@app.route('/', methods=['GET', 'POST'])
def index() -> str:
    """Render the search form and process submissions."""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if not query:
            return render_template('index.html', error='Please enter search terms.')
        try:
            jobs = search_jobs(CONFIG, query=query)
        except Exception as exc:
            return render_template('index.html', error=f'Error executing search: {exc}')
        return render_template('results.html', jobs=jobs, query=query)
    return render_template('index.html')


if __name__ == '__main__':
    # Run the development server
    app.run(host='0.0.0.0', port=5000, debug=True)
