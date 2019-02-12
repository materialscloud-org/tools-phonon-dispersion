import logging
import os
import yaml
import json
import flask
from flask import Blueprint
from flask import Markup

blueprint = Blueprint('compute', __name__, url_prefix='/compute')

logger = logging.getLogger('tools-app')

directory = os.path.abspath(os.path.split(os.path.realpath(__file__))[0] + "/../")
static_folder = os.path.join(directory, "static")
config_file_path = os.path.join(static_folder, "config.yaml")


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

class FlaskRedirectException(Exception):
    pass

@blueprint.route('/process_structure/', methods=['GET', 'POST'])
def process_structure():
    if flask.request.method == 'POST':
        structurefile = flask.request.files['structurefile']
        fileformat = flask.request.form.get('fileformat', 'unknown')
        filecontent = structurefile.read().decode('utf-8')

        try:
            return "FORMAT: {}<br>CONTENT:<br><code><pre>{}</pre></code>".format(fileformat, filecontent)
        #except FlaskRedirectException as e:
            #flask.flash(str(e))
            #return flask.redirect(flask.url_for('input_data'))
        except Exception:
            flask.flash("Unable to process the data, sorry...")
            return flask.redirect(flask.url_for('input_data'))

    else:
        #return flask.redirect(flask.url_for('compute.process_structure_example'))
        return flask.redirect("/")
        #return flask.redirect(flask.url_for('input_data'))

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

                    return flask.render_template("user_templates/visualizer.html", structure=examplestructure, page_title=Markup(page_title), jsondata=jsondata)
                else:
                    raise FlaskRedirectException("data_folder path is missing in config file")
            else:
                raise FlaskRedirectException("Config file is missing")
        except FlaskRedirectException as e:
            flask.flash(str(e))
            return flask.redirect(flask.url_for('input_data'))
    else:
        return flask.redirect(flask.url_for('input_data'))
