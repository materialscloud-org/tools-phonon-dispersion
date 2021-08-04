# import json
import os

import pytest

# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from urllib.parse import urlparse

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


## Next lines commented for now (coming from tool-layer-raman-ir)
## These need to be adapted still
# def get_file_examples():
#     """Get all valid files from the STRUCTURE_EXAMPLES_PATH and returns
#     a list of tuples in the format (parser_name, file_relpath)."""
#     retval = []
#     top_dir = STRUCTURE_EXAMPLES_PATH
#     for parser_name in os.listdir(top_dir):
#         if parser_name.startswith("."):
#             continue
#         parser_dir = os.path.join(top_dir, parser_name)
#         if not os.path.isdir(parser_dir):
#             continue
#         for filename in os.listdir(parser_dir):
#             file_abspath = os.path.join(parser_dir, filename)
#             if (
#                 filename.endswith("~")
#                 or filename.startswith(".")
#                 or filename.endswith(".expectedstrings.txt")
#                 or not os.path.isfile(file_abspath)
#             ):
#                 continue
#             expected_strings_file = os.path.join(
#                 os.path.dirname(file_abspath),
#                 "{}.expectedstrings.txt".format(os.path.basename(file_abspath)),
#             )
#             try:
#                 with open(expected_strings_file) as fhandle:
#                     expected_strings = [line.strip() for line in fhandle.readlines()]
#             except IOError:
#                 # The file does not exist: I put in a string that does not exist, and
#                 # explains what is going on. In this way I don't stop all tests, but only
#                 # the tests with missing expectedstrings file will fail.
#                 expected_strings = [
#                     f"YOU NEED TO ADD A FILE '{os.path.basename(expected_strings_file)}' WITH THE LIST OF EXPECTED STRINGS!"
#                 ]
#             # remove empty strings
#             expected_strings = [line for line in expected_strings if line]
#             retval.append((parser_name, filename, expected_strings))

#     return retval


# def submit_structure(
#     selenium, file_abspath, parser_name
# ):  # pylint: disable=too-many-locals
#     """Given a selenium driver, submit a file."""
#     # Load file
#     file_upload = selenium.find_element_by_name("structurefile")
#     file_upload.send_keys(file_abspath)

#     # Select format
#     format_selector = selenium.find_element_by_id("fileformatSelect")
#     Select(format_selector).select_by_value(parser_name)

#     # Check if there is additional extra information to put in the form
#     # If there, it's in a file named .extra.XXX for a XXX file_path.
#     # It is a JSON where the key is the 'name' of the input field, and the
#     # value is the value to type in.
#     # In this case type it in the right input form.
#     extra_file = os.path.join(
#         os.path.dirname(file_abspath),
#         ".extra.{}".format(os.path.basename(file_abspath)),
#     )
#     if os.path.isfile(extra_file):
#         with open(extra_file) as fhandle:
#             extra_data = json.load(fhandle)
#         for extra_name, extra_value in extra_data.items():
#             if extra_name == "skin-factor":
#                 # Move the slider one step at a time; I do it by clicking on the
#                 # right arrow enough times

#                 element = selenium.find_element(By.NAME, extra_name)
#                 current_value = float(element.get_attribute("value"))
#                 target_value = float(extra_value)
#                 # I expect a step of 0.01
#                 step = 0.01
#                 assert abs(step - float(element.get_attribute("step"))) < 1.0e-5

#                 count = int(round((target_value - current_value) / step))

#                 for _ in range(abs(count)):
#                     if count > 0:
#                         element.send_keys(Keys.RIGHT)
#                     else:
#                         element.send_keys(Keys.LEFT)

#                 assert (
#                     abs(extra_value - float(element.get_attribute("value"))) < 1.0e-5
#                 ), "I tried to move the slider but I failed, I wanted {}, I got {}".format(
#                     extra_value, float(element.get_attribute("value"))
#                 )

#             else:
#                 selenium.find_element(By.NAME, extra_name).send_keys(str(extra_value))

#     # Submit form
#     # selenium.find_element_by_xpath("//input[@value='Calculate my structure']").click()
#     selenium.find_element_by_xpath(
#         "//form[@action='compute/process_structure/']"
#     ).submit()


# @pytest.mark.nondestructive
# @pytest.mark.parametrize(
#     "parser_name, file_relpath, expected_strings", get_file_examples()
# )
# def test_send_structure(request, selenium, parser_name, file_relpath, expected_strings):
#     """Test submitting various files."""
#     selenium.get(TEST_URL)

#     try:
#         # Load file
#         file_abspath = os.path.join(STRUCTURE_EXAMPLES_PATH, parser_name, file_relpath)
#         submit_structure(selenium, file_abspath, parser_name)

#         # We should have been redirected back to /
#         assert urlparse(selenium.current_url).path == "/compute/process_structure/"

#         assert "Input crystal structure" in selenium.page_source

#         for expected_string in expected_strings:
#             hall = "---".join(
#                 [l for l in selenium.page_source.splitlines() if "Hall number" in l]
#             )
#             assert (
#                 expected_string in selenium.page_source
#             ), f"String '{expected_string}' not found in the page source - {hall}"
#     except Exception:
#         # Create a screenshot and raise
#         selenium.save_screenshot(f"{request.node.name}.png")
#         raise
