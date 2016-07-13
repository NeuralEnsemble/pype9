#
# A Docker image for running PyPe9 examples
#
# To run:
#
#     python ~/packages/pype9/examples/brunel.py --help
#
# or
#
#     python ~/packages/pype9/examples/izhikevich.py --help
#

FROM neuralensemble/simulation:py2
MAINTAINER tom.close@monash.edu

RUN sed 's/#force_color_prompt/force_color_prompt/' .bashrc > tmp; mv tmp .bashrc
RUN echo "source /home/docker/env/neurosci/bin/activate" >> .bashrc

USER root
RUN apt-get update; apt-get install -y python-lxml
USER docker

WORKDIR $HOME/packages

# Install lib9ML libraries
RUN git clone https://github.com/tclose/lib9ML.git lib9ml
RUN cd ./lib9ml; git checkout dyn_arrays_conn_groups; $VENV/bin/pip install .

# Install NineMLCatalog
RUN git clone https://github.com/tclose/NineMLCatalog.git ninemlcatalog
RUN cd ./ninemlcatalog; git checkout develop_backport; $VENV/bin/pip install .

# Install PyPe9
RUN git clone https://github.com/tclose/PyPe9.git pype9
RUN $VENV/bin/pip install ./pype9

# Install the project directory
RUN mkdir $HOME/projects
WORKDIR $HOME/projects

# Welcome message
RUN echo 'echo "Docker container for running PyPe9 examples. See README.rst for instructions."' >> $HOME/.bashrc
