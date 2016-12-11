#
# A Docker image for running PyPe9 examples
#
# Steps to run the examples using Docker:
# 
#  1. Install Docker (see https://docs.docker.com/engine/installation/)
#
#  2. Pull the Pype9 "Docker image"
#
#        docker pull tclose/pype9
#
#  3. Create a "Docker container" from the downloaded image 
#
#        docker run -v `pwd`/<your-local-output-dir>:/home/docker/output -t -i tclose/pype9 /bin/bash
#
#    This will create a folder called <your-local-output-dir> in the
#    directory you are running the docker container, which you can access
#    from your host computer (i.e. outside of the container) and view the
#    output figures from.
#
#  4. From inside the running container run the examples with
#
#        python ~/examples/izhikevich.py --save_fig ~/output/<output-name>.pdf
#
#    or 
#
#        python ~/examples/brunel.py --save_fig ~/output/<output-dir>
#
#    Supply the '--help' option to see a full list of options for each example.
#
#  5. Edit the xml descriptions in the ~/catalog directory to alter the
#     simulated models as desired.
#

FROM neuralensemble/simulation:py2
MAINTAINER tom.g.close@gmail.com

# Install LXML Python library
USER root
RUN apt-get update; apt-get install -y python-lxml

USER docker

# Add a symbolic link to the modlunit command into the virtual env bin dir
RUN ln -s $HOME/env/neurosci/x86_64/bin/modlunit $VENV/bin

# Install the catalog via git clone (can be installed via pip but more convenient to have local version)
RUN git clone https://github.com/tclose/NineMLCatalog.git $HOME/packages/ninemlcatalog
WORKDIR $HOME/packages/ninemlcatalog
RUN git checkout merging_with_master

# Install PyPe9
RUN echo "Installing Python 9ML library and Pype9"
RUN PATH=$PATH:$VENV/bin $VENV/bin/pip install https://github.com/tclose/lib9ML/archive/develop.zip
RUN PATH=$PATH:$VENV/bin $VENV/bin/pip install https://github.com/CNS-OIST/PyPe9/archive/master.zip

# Create a link to the examples and catalog directories
RUN ln -s $HOME/packages/ninemlcatalog/xml $HOME/catalog

# Set up bashrc and add welcome message
RUN sed 's/#force_color_prompt/force_color_prompt/' $HOME/.bashrc > $HOME/tmp; mv $HOME/tmp $HOME/.bashrc
RUN echo "source /home/docker/env/neurosci/bin/activate" >> $HOME/.bashrc
RUN echo "export PYTHONPATH=$HOME/packages/ninemlcatalog:$PYTHONPATH" >> $HOME/.bashrc
RUN echo "echo \"Type 'pype9 help' for instructions on how to run pype9\"" >> $HOME/.bashrc
RUN echo "echo \"See $HOME/catalog for example 9ML models\"" >> $HOME/.bashrc

WORKDIR $HOME
