import logging
import os
import yaml
import json
import flask
from flask import Blueprint
from flask import Markup

try:
    from compute.phononweb.qephonon_qetools import QePhononQetools
except Exception:
    import traceback

    traceback.print_exc()


import qe_tools  # mostly to get its version
from tools_barebone import __version__ as tools_barebone_version

__version__ = "21.08.0"

blueprint = Blueprint("compute", __name__, url_prefix="/compute")

logger = logging.getLogger("tools-app")

directory = os.path.abspath(os.path.split(os.path.realpath(__file__))[0] + "/../")
static_folder = os.path.join(directory, "static")
config_file_path = os.path.join(static_folder, "config.yaml")
template_folder = os.path.join(directory, "templates/user_templates")

try:
    with open(config_file_path) as config_file:
        config = yaml.load(config_file, Loader=yaml.SafeLoader)
        data_folder = os.path.join(directory, config["data_folder"])
except IOError as exc:
    if exc.errno == 2:  # No such file or directory
        config = {}
        data_folder = None
    else:
        raise


def get_version_info():
    """Return a dictionary with the version info, to be put at the footer."""
    return {
        "qe_tools_version": qe_tools.__version__,
        "this_tool_version": __version__,
        "tools_barebone_version": tools_barebone_version,
    }


class FlaskRedirectException(Exception):
    """Custom exception used for redirect errors."""


@blueprint.route("/input_help/", methods=["GET"])
def show_custom_json_format():
    """Endpoint to display the help on the input format."""
    return flask.send_from_directory(template_folder, "input_help_text.html")


@blueprint.route("/terms_of_use/", methods=["GET"])
def show_terms_of_use():
    """
    View for the terms of use.
    """
    return flask.send_from_directory(template_folder, "terms_of_use.html")


@blueprint.route("/process_structure/", methods=["GET", "POST"])
def process_structure():
    """Endpoint to process a structure provided by the user."""
    if flask.request.method == "POST":
        custom_json_file = flask.request.files["custom_json_file"]
        qe_input_file = flask.request.files["qe_input_file"]
        qe_output_file = flask.request.files["qe_output_file"]
        qe_modes_file = flask.request.files["qe_modes_file"]

        file_format = flask.request.form.get("file_format")

        # CASE 1: check if custom json file is uploaded
        if file_format == "custom_json_file":
            filename = custom_json_file.filename
            filecontent = custom_json_file.read().decode("utf8")
            if filecontent:
                try:
                    jsondata = json.loads(filecontent)
                    assert isinstance(
                        jsondata, dict
                    ), "The JSON file should contain a dictionary"
                    # Check that there are a few of the important keys
                    assert all(
                        key in jsondata
                        for key in [
                            "atom_numbers",
                            "atom_pos_car",
                            "atom_types",
                            "eigenvalues",
                            "natoms",
                            "qpoints",
                            "vectors",
                        ]
                    ), "The JSON file does not have some of the required keys"
                    return flask.render_template(
                        "user_templates/visualizer.html",
                        structure=jsondata.get("name", filename),
                        page_title=Markup(jsondata.get("name", filename)),
                        jsondata=jsondata,
                        **get_version_info()
                    )
                except (ValueError, AssertionError) as exc:
                    flask.flash(
                        "Uploaded file is not having correct JSON format. Error: "
                        + str(exc)
                    )
            else:
                flask.flash("Uploaded file is empty.")

        # CASE 2: QE input
        elif file_format == "qe_files":
            qe_input = qe_input_file.read().decode("utf8", errors="replace")
            qe_output = qe_output_file.read().decode("utf8", errors="replace")
            qe_modes = qe_modes_file.read().decode("utf8", errors="replace")

            if not qe_input:
                flask.flash("You didn't specify a QE input file")
                return flask.redirect(flask.url_for("input_data"))
            if not qe_output:
                flask.flash("You didn't specify a QE output file")
                return flask.redirect(flask.url_for("input_data"))
            if not qe_modes:
                flask.flash("You didn't specify a QE matdyn.modes file")
                return flask.redirect(flask.url_for("input_data"))

            page_title = "{} + {} + {}".format(
                qe_input_file.filename, qe_output_file.filename, qe_modes_file.filename
            )

            try:
                # This should be a dict, not a JSON string
                jsondata = QePhononQetools(
                    scf_input=qe_input, scf_output=qe_output, matdyn_modes=qe_modes
                ).get_dict()
                if jsondata:
                    return flask.render_template(
                        "user_templates/visualizer.html",
                        page_title=page_title,
                        jsondata=jsondata,
                        **get_version_info()
                    )
                flask.flash(
                    "Error in processing uploaded Quantum ESPRESSO input files, no data parsed."
                )
            except Exception as e:
                flask.flash(
                    "Error in processing uploaded Quantum ESPRESSO input files. Error: "
                    + str(e)
                )
        else:
            flask.flash("Unknown file format specified")

        return flask.redirect(flask.url_for("input_data"))
    return flask.redirect(flask.url_for("input_data"))


@blueprint.route("/process_example_structure/", methods=["GET", "POST"])
def process_structure_example():
    """Endpoint to show an example."""
    if flask.request.method == "POST":
        example_structure = flask.request.form.get(
            "example_structure", "No structure selected"
        )
        try:
            if config:
                page_title = config["data"][example_structure]["title"]
                if data_folder:
                    filename = config["data"][example_structure]["filename"]
                    filepath = os.path.join(directory, data_folder, filename)
                    jsondata = {}
                    with open(filepath) as structurefile:
                        jsondata = json.load(structurefile)

                    return flask.render_template(
                        "user_templates/visualizer.html",
                        page_title=Markup(page_title),
                        jsondata=jsondata,
                        **get_version_info()
                    )
                raise FlaskRedirectException(
                    "data_folder path is missing in config file."
                )
            raise FlaskRedirectException("Config file is missing.")
        except FlaskRedirectException as e:
            flask.flash(str(e))
            return flask.redirect(flask.url_for("input_data"))
    # GET request
    return flask.redirect(flask.url_for("input_data"))
