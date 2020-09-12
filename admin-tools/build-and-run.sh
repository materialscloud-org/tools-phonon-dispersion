#!/bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# To build container
docker build -t tools-phonon-dispersion "$DIR/.."

LAYER_CONTAINER=`docker ps --filter="name=tools-phonon-dispersion-instance" -q`
if [ "$LAYER_CONTAINER" != "" ]
then
    docker kill "$LAYER_CONTAINER"
fi  

# To launch container
docker run -d -p 8093:80 --rm --name=tools-phonon-dispersion-instance tools-phonon-dispersion

# Pass '-n' to avoid opening a new browser window
if [ "$1" != "-n" ]
then
    # Give it a second to let apache start
    sleep 1
    python -c "import webbrowser; webbrowser.open('http://localhost:8093')"
    echo "Browser opened at http://localhost:8093"
    echo "Pass -n to avoid opening it"
else
    echo "You can access the webservice at:"
    echo "http://localhost:8093"
fi

echo ""
echo "You can kill the service with:"
echo "docker kill tools-phonon-dispersion-instance"
