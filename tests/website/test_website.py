# import json
import os

import pytest

from selenium.webdriver.support.ui import Select
from urllib.parse import urlparse

# Note: you need to build docker and start it with
# ./admin-tools/build-and-run.sh
# Then, you can run the tests
TEST_URL = "http://localhost:8093"
STRUCTURE_EXAMPLES_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "structure_examples"
)


@pytest.mark.nondestructive
def test_input_data_page(selenium):
    """Check the page that is shown by default when there is no configuration."""
    selenium.get(TEST_URL)

    assert "interactive phonon visualizer" in selenium.title.lower()
    format_selector = selenium.find_element_by_id("file_format")

    # This does not need to be a complete list, but at least these
    # should be present
    expected_importer_names = set(["Quantum ESPRESSO files", "PhononVis JSON format"])

    # If the difference is not empty, at least one of the expected importer names is not there!
    assert not expected_importer_names.difference(
        option.text for option in format_selector.find_elements_by_tag_name("option")
    )

    # Check the presence of a string in the source code
    assert "Henrique Miranda" in selenium.page_source


def get_file_examples():
    """Get all valid files from the STRUCTURE_EXAMPLES_PATH and returns
    a list of tuples in the format (parser_name, file_relpath)."""
    retval = []
    top_dir = STRUCTURE_EXAMPLES_PATH
    for parser_name in os.listdir(top_dir):
        if parser_name.startswith("."):
            continue
        parser_dir = os.path.join(top_dir, parser_name)
        if not os.path.isdir(parser_dir):
            continue
        for filename in os.listdir(parser_dir):
            # Note that 'filename' is actually a folder name for the qe-files format
            file_abspath = os.path.join(parser_dir, filename)
            if (
                filename.endswith("~")
                or filename.startswith(".")
                or filename.endswith(".expectedstrings.txt")
            ):
                continue
            expected_strings_file = os.path.join(
                os.path.dirname(file_abspath),
                "{}.expectedstrings.txt".format(os.path.basename(file_abspath)),
            )
            try:
                with open(expected_strings_file) as fhandle:
                    expected_strings = [line.strip() for line in fhandle.readlines()]
            except IOError:
                # The file does not exist: I put in a string that does not exist, and
                # explains what is going on. In this way I don't stop all tests, but only
                # the tests with missing expectedstrings file will fail.
                expected_strings = [
                    f"YOU NEED TO ADD A FILE '{os.path.basename(expected_strings_file)}' WITH THE LIST OF EXPECTED STRINGS!"
                ]

            # remove empty strings
            expected_strings = [line for line in expected_strings if line]
            retval.append((parser_name, filename, expected_strings))

    return retval


def submit_structure(
    selenium, file_abspath, format_name
):  # pylint: disable=too-many-locals
    """Given a selenium driver, submit a file."""
    # Select format
    format_selector = selenium.find_element_by_id("file_format")
    Select(format_selector).select_by_value(format_name)

    # Load file(s)
    # for JSON, it's the file; for Quantum ESPRESSO, it's the folder with the files
    if format_name == "custom_json_file":
        file_upload = selenium.find_element_by_name("custom_json_file")
        file_upload.send_keys(file_abspath)
    elif format_name == "qe_files":
        for input_name, filename in [
            ["qe_input_file", "scf.in"],
            ["qe_output_file", "scf.out"],
            ["qe_modes_file", "matdyn.modes"],
        ]:
            file_upload = selenium.find_element_by_name(input_name)
            file_upload.send_keys(os.path.join(file_abspath, filename))

    # Submit form
    # selenium.find_element_by_xpath("//input[@value='Calculate my structure']").click()
    selenium.find_element_by_xpath(
        "//form[@action='compute/process_structure/']"
    ).submit()


@pytest.mark.nondestructive
@pytest.mark.parametrize(
    "parser_name, file_relpath, expected_strings", get_file_examples()
)
def test_send_structure(request, selenium, parser_name, file_relpath, expected_strings):
    """Test submitting various files."""
    selenium.get(TEST_URL)

    try:
        # Load file
        file_abspath = os.path.join(STRUCTURE_EXAMPLES_PATH, parser_name, file_relpath)
        submit_structure(selenium, file_abspath, parser_name)

        # We should not have been redirected back to /
        assert urlparse(selenium.current_url).path == "/compute/process_structure/"

        assert "Atomic positions" in selenium.page_source

        for expected_string in expected_strings:
            assert (
                expected_string in selenium.page_source
            ), f"String '{expected_string}' not found in the page source - {parser_name} - {file_relpath}"
    except Exception:
        # Create a screenshot and raise
        selenium.save_screenshot(f"{request.node.name}.png")
        raise
