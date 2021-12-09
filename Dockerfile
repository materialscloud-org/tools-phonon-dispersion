FROM materialscloud/tools-barebone:1.3.0

LABEL maintainer="Materials Cloud <info@materialscloud.org>"

# Copy various files
COPY ./config.yaml /home/app/code/webservice/static/config.yaml
COPY ./user_templates/ /home/app/code/webservice/templates/user_templates/
COPY ./compute/ /home/app/code/webservice/compute/
COPY ./user_static/ /home/app/code/webservice/user_static/

RUN cp /home/app/code/webservice/templates/header.html /home/app/code/webservice/templates/header_pages.html && \
    sed -i "s|base.html|user_templates/base.html|g" /home/app/code/webservice/templates/header_pages.html && \
    sed -i "s|static/|../../static/|g" /home/app/code/webservice/templates/header_pages.html

# Set proper permissions on files just copied
RUN chown -R app:app /home/app/code/webservice/
# Make sure files are readable by everybody (and executable where appropriate)
# (e.g. to avoid unreadable folders by apache etc.)
RUN chmod -R a+rX /home/app/code/webservice/

EXPOSE 80
