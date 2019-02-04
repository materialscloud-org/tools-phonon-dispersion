FROM tools-barebone

MAINTAINER Materials Cloud <info@materialscloud.org>

COPY ./config.yaml /home/app/code/webservice/static/config.yaml
COPY ./user_requirements.txt /home/app/code/user_requirements.txt
COPY ./user_templates/ /home/app/code/webservice/templates/user_templates/
COPY ./user_static/ /home/app/code/webservice/user_static/
COPY ./compute/ /home/app/code/webservice/compute/

# Set proper permissions
RUN chown -R app:app $HOME

RUN pip install -r /home/app/code/user_requirements.txt
