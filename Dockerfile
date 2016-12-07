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

USER root
RUN apt-get update; apt-get install -y python-lxml
# Use the master Sympy branch as there is a bug in 1.0
RUN pip install https://github.com/sympy/sympy/archive/master.zip

# Install the required dependencies
RUN pip install https://github.com/tclose/lib9ML/archive/develop.zip
RUN pip install https://github.com/tclose/Diophantine/archive/master.zip

USER docker
# Add a symbolic link to the modlunit command into the virtual env bin dir
RUN ln -s $HOME/env/neurosci/x86_64/bin/modlunit $VENV/bin

# Set up bashrc and add welcome message
RUN sed 's/#force_color_prompt/force_color_prompt/' $HOME/.bashrc > $HOME/tmp; mv $HOME/tmp $HOME/.bashrc
RUN echo "source /home/docker/env/neurosci/bin/activate" >> $HOME/.bashrc
RUN echo "echo \"Docker container for running PyPe9 examples.\"" >> $HOME/.bashrc
RUN echo "echo \"See the $HOME/examples directory for the example \"" >> $HOME/.bashrc
RUN echo "echo \"python scripts (supply the '--help' option to see usage).\"" >> $HOME/.bashrc

# Install the catalog
RUN git clone https://github.com/INCF/NineMLCatalog.git $HOME/packages/ninemlcatalog
ENV PYTHONPATH $HOME/packages/ninemlcatalog/python:$PYTHONPATH

# Install PyPe9
RUN git clone https://github.com/CNS-OIST/PyPe9.git $HOME/packages/pype9
ENV PYTHONPATH $HOME/packages/pype9:$PYTHONPATH
RUN ln -s $HOME/packages/pype9/bin/pype9 $VENV/bin

# Compile the libninemlnrn shared library (with the random distributions in it)
WORKDIR $HOME/packages/pype9/pype9/neuron/cells/code_gen/libninemlnrn
RUN make
ENV LD_LIBRARY_PATH $HOME/packages/pype9/pype9/neuron/cells/code_gen/libninemlnrn:$LD_LIBRARY_PATH

# Create a link to the examples and catalog directories
RUN ln -s $HOME/packages/pype9/examples $HOME/examples
RUN ln -s $HOME/packages/ninemlcatalog/xml $HOME/catalog

WORKDIR $HOME
