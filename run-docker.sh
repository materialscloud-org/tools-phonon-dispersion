#!/bin/bash
docker run -p 8093:80 --rm --name=tools-phonon-dispersion-instance tools-phonon-dispersion && echo "You can connect to http://localhost:8093"