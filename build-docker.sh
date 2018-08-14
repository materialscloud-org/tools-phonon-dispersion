#!/bin/bash

BAREBONE_IMAGE=`docker images tools-barebone -q`

if [ "$BAREBONE_IMAGE" == "" ]
then
    echo "##############################################################"
    echo "# You need to build first the barebone image."
    echo "# For now, you need to do it by hand (in the future "
    echo "# we will push this to dockerhub (organization materialslcoud)"
    echo "#"
    echo "# To do this, do:"
    echo "#   git clone https://github.com/materialscloud-org/tools-barebone"
    echo "#   cd tools-barebone"
    echo "#   ./build-docker.sh"
    echo "##############################################################"   
    exit 1
else
    echo "Starting from image 'tools-barebone' with id $BAREBONE_IMAGE"
fi

docker build -t tools-phonon-dispersion .
