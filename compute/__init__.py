import logging
import os
import yaml
import json
import flask
from flask import Blueprint
from flask import Markup
from werkzeug.utils import secure_filename

from compute.phononweb.qephonon_qetools import QePhononQetools

import qe_tools # mostly to get its version
from tools_barebone import __version__ as tools_barebone_version

__version__ = "21.06.0"

blueprint = Blueprint('compute', __name__, url_prefix='/compute')

logger = logging.getLogger('tools-app')

directory = os.path.abspath(os.path.split(os.path.realpath(__file__))[0] + "/../")
static_folder = os.path.join(directory, "static")
config_file_path = os.path.join(static_folder, "config.yaml")
tmp_folder = os.path.join(directory, "compute/tmp")
template_folder = os.path.join(directory, 'templates/user_templates')

try:
    with open(config_file_path) as config_file:
        config = yaml.load(config_file)
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
        'qe_tools_version': qe_tools.__version__,
        'this_tool_version': __version__,
        'tools_barebone_version': tools_barebone_version
    }


class FlaskRedirectException(Exception):
    pass

@blueprint.route('/input_help/', methods=['GET'])
def show_custom_json_format():
    return flask.send_from_directory(template_folder, 'input_help_text.html')


@blueprint.route('/terms_of_use/', methods=['GET'])
def show_terms_of_use():
    """
    View for the terms of use
    """
    return flask.send_from_directory(template_folder, 'terms_of_use.html')


@blueprint.route('/process_structure/', methods=['GET', 'POST'])
def process_structure():
    if flask.request.method == 'POST':

        custom_file = None
        qe_scf_file = None
        qe_modes_file = None

        if "custom_json_file" in flask.request.files:
            custom_file = flask.request.files['custom_json_file']

        if "qe_scf_file" in flask.request.files:
            qe_scf_file = flask.request.files["qe_scf_file"]

        if "qe_modes_file" in flask.request.files:
            qe_modes_file = flask.request.files["qe_modes_file"]

        # CASE 1: check if custom json file is uploaded
        if custom_file:
            filename = custom_file.filename
            filecontent = custom_file.read().decode('utf8')
            if filecontent:
                try:
                    jsondata = json.loads(filecontent)
                    return flask.render_template("user_templates/visualizer.html", structure=filename,
                                         page_title=Markup(filename), jsondata=jsondata, **get_version_info())
                except ValueError as e:
                    flask.flash("Uploaded file is not having correct JSON format. Error: " + str(e))
            else:
                flask.flash("Uploaded file is empty.")

        # CASE 2: QE input
        elif qe_scf_file and qe_modes_file:

            qe_scf_filename = secure_filename(qe_scf_file.filename)
            qe_scf_file.save(os.path.join(tmp_folder, qe_scf_filename))

            qe_modes_filename = secure_filename(qe_modes_file.filename)
            qe_modes_file.save(os.path.join(tmp_folder, qe_modes_filename))

            try:
                tmpdata = QePhononQetools("PW", "qe_test", folder=tmp_folder, scf=qe_scf_filename, modes=qe_modes_filename).get_json()
                jsondata =json.loads(tmpdata)
                if jsondata:
                    return flask.render_template("user_templates/visualizer.html", structure="",
                                                 page_title=qe_scf_filename + " & " + qe_modes_filename, jsondata=jsondata, **get_version_info())
                else:
                    flask.flash("Error in processing uploaded QE input files.")
            except Exception as e:
                flask.flash("Error in processing uploaded QE input files. Error: " + str(e))
        else:
            flask.flash("Check if all required file(s) are uploaded.")

        return flask.redirect(flask.url_for('input_data'))
    else:
        return flask.redirect(flask.url_for('input_data'))


@blueprint.route('/process_example_structure/', methods=['GET', 'POST'])
def process_structure_example():
    if flask.request.method == 'POST':
        examplestructure = flask.request.form.get('examplestructure', '<none>')
        try:
            if config:
                page_title = config["data"][examplestructure]["title"]
                if data_folder:
                    filename = config["data"][examplestructure]["filename"]
                    filepath = os.path.join(directory, data_folder, filename)
                    jsondata = {}
                    with open(filepath) as structurefile:
                        jsondata = json.load(structurefile)

                    return flask.render_template("user_templates/visualizer.html",
                        structure=examplestructure, page_title=Markup(page_title), jsondata=jsondata, **get_version_info())
                else:
                    raise FlaskRedirectException("data_folder path is missing in config file.")
            else:
                raise FlaskRedirectException("Config file is missing.")
        except FlaskRedirectException as e:
            flask.flash(str(e))
            return flask.redirect(flask.url_for('input_data'))
    else:
        return flask.redirect(flask.url_for('input_data'))
