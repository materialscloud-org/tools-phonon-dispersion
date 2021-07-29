#######################
tools-phonon-dispersion
#######################

In this repository we provide the code to deploy an online service for
the interactive visualization of the phonon modes.
A live demo is currently hosted on the `Materials Cloud`_ web portal.

This tool leverages the `phonon visualizer`_ developed by Henrique Miranda.

============
Contributors
============

- Snehal Kumbhar, Elsa Passaro (EPFL) [tool development]
- Giovanni Pizzi (EPFL) [tool development]
- Henrique Miranda (UCL, Belgium) [development of the original phonon visualizer]
- Thibault Sohier (EPFL) [support on the python code and on the examples]
- Chara Cignarella (EPFL) [bug reporting and fixing]

=======
License
=======

The code is open-source (licensed with a MIT license, see LICENSE.txt).

===================
Online service/tool
===================

The following is a screenshot of the selection window:

.. image:: https://raw.githubusercontent.com/materialscloud-org/tools-phonon-dispersion/master/misc/screenshots/selector.png
     :alt: Interactive phonon dispersion tool: selection window
     :width: 50%
     :align: center

And the following is a screenshot of the main output window, showing the phonon dispersion and the corresponding interactive eigenvectors.

.. image:: https://raw.githubusercontent.com/materialscloud-org/tools-phonon-dispersion/master/misc/screenshots/mainwindow.png
     :alt: Interactive phonon dispersion tool: main output
     :width: 50%
     :align: center


=========================================
Docker image and running the tool locally
=========================================
Docker images are automatically built and hosted on `DockerHub under the repository materialscloud/tools-phonon-dispersion`_.

If you want to run locally the latest version, you can execute::

  docker pull materialscloud/tools-phonon-dispersion:latest
  docker run -p 8093:80 materialscloud/tools-phonon-dispersion:latest

and then connect to ``http://localhost:8093`` with your browser.


.. _Materials Cloud: https://www.materialscloud.org/work/tools/interactivephonon
.. _phonon visualizer: http://henriquemiranda.github.io/phononwebsite/
.. _DockerHub under the repository materialscloud/tools-phonon-dispersion: https://hub.docker.com/repository/docker/materialscloud/tools-phonon-dispersion
