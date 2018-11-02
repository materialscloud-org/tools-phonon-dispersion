import logging
import flask
from flask import Blueprint
import io
blueprint = Blueprint('compute', __name__, url_prefix='/compute')

logger = logging.getLogger('tools-app')

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
        return flask.redirect(flask.url_for('compute.process_structure_example'))
        #flask.flash("Redirecting...")
        #return flask.redirect(flask.url_for('input_data'))

@blueprint.route('/process_example_structure/', methods=['GET', 'POST'])
def process_structure_example():
    if flask.request.method == 'POST':
        examplestructure = flask.request.form.get('examplestructure', '<none>')
        return flask.render_template("user_templates/visualizer.html", structure=examplestructure)
        #return "This was a POST " + examplestructure
    else:
        return flask.redirect(flask.url_for('compute.process_structure_example'))
        #return flask.render_template("user_templates/visualizer.html", structure="C2")
        #return "This was a GET"