from pathlib import Path


class Paths:
    """Class to store the paths to the data and output folders."""

    project = Path(__file__).resolve().parent.parent.parent.parent
    raw_data = project / "raw_data"
    app = project
    app_data = app / "src" / "data"
    scripts = app_data / "scripts"
