FROM materialscloud/tools-barebone:1.1.3

LABEL maintainer="Materials Cloud <info@materialscloud.org>"

# Python requirements
COPY ./requirements.txt /home/app/code/requirements.txt
# Run this as sudo to replace the version of pip
RUN pip3 install -U 'pip>=10' setuptools wheel
# install packages as normal user (app, provided by passenger)
USER app
WORKDIR /home/app/code
# Install pinned versions of packages
RUN pip3 install --user -r requirements.txt
# Go back to root.
# Also, it should remain as user root for startup
USER root


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
