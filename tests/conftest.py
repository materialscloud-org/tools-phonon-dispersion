"""Configuration file for pytest tests."""
import pytest


@pytest.fixture
def chrome_options(chrome_options):
    """By default use these options with Chrome."""
    # https://pytest-selenium.readthedocs.io/en/latest/user_guide.html#id2
    chrome_options.add_argument("--headless")
    # So screeshots contain more information - note that it's longer than larger
    # as this will allow to see more content
    chrome_options.add_argument("--window-size=1080,1920")
    return chrome_options
