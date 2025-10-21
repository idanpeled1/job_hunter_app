"""Job Hunter package

This package bundles the job search logic and the optional Flask web application
for distributing the tool. It allows users to import core functions and run
the web interface.

"""

from .job_hunter import (
    load_config,
    search_jobs,
    compute_score,
    save_results,
)  # noqa: F401
