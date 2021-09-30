FROM dokku/tools-barebone

LABEL maintainer="Materials Cloud <info@materialscloud.org>"

# Copy various files
COPY ./config.yaml /home/app/code/webservice/static/config.yaml
COPY ./user_templates/ /home/app/code/webservice/templates/user_templates/
COPY ./compute/ /home/app/code/webservice/compute/
COPY ./user_static/ /home/app/code/webservice/user_static/

# Set proper permissions on files just copied
RUN chown -R app:app /home/app/code/webservice/
# Make sure files are readable by everybody (and executable where appropriate)
# (e.g. to avoid unreadable folders by apache etc.)
RUN chmod -R a+rX /home/app/code/webservice/

EXPOSE 80
