#
# A Docker image for running PyPe9 examples
#

FROM neuralensemble/simulation:py2
MAINTAINER tom.g.close@gmail.com

USER root
RUN apt-get update; apt-get install -y python-lxml
RUN pip install sympy

USER docker
# Add a symbolic link to the modlunit command into the virtual env bin dir
RUN ln -s $HOME/env/neurosci/x86_64/bin/modlunit $VENV/bin

# Clone the required repositories
RUN git clone https://github.com/tclose/NineMLCatalog.git $HOME/packages/ninemlcatalog
RUN git clone https://github.com/tclose/lib9ML.git $HOME/packages/lib9ml
RUN git clone https://github.com/tclose/Diophantine.git $HOME/packages/diophantine

# Checkout appropriate branches of the git repos
RUN cd $HOME/packages/ninemlcatalog; git checkout develop
RUN cd $HOME/packages/lib9ml; git checkout develop

# Set the PYTHONPATH to look at the git repos
ENV PYTHONPATH $HOME/packages/ninemlcatalog/python:$PYTHONPATH
ENV PYTHONPATH $HOME/packages/lib9ml:$PYTHONPATH
ENV PYTHONPATH $HOME/packages/diophantine:$PYTHONPATH

# Create a link to the examples
RUN ln -s $HOME/packages/pype9/examples $HOME/examples
WORKDIR $HOME/examples

# Set up bashrc and add welcome message
RUN sed 's/#force_color_prompt/force_color_prompt/' .bashrc > tmp; mv tmp .bashrc
RUN echo "source /home/docker/env/neurosci/bin/activate" >> .bashrc
RUN echo 'echo "Docker container for running PyPe9 examples."' >> $HOME/.bashrc
RUN echo 'echo "See the $HOME/examples directory for the example "' >> $HOME/.bashrc
RUN echo 'echo "python scripts (supply the '--help' option to see usage)."' >> $HOME/.bashrc

# Install PyPe9
RUN git clone https://github.com/CNS-OIST/PyPe9.git $HOME/packages/pype9
ENV PYTHONPATH $HOME/packages/pype9:$PYTHONPATH

# Compile the libninemlnrn shared library (with the random distributions in it)
WORKDIR $HOME/packages/pype9/pype9/neuron/cells/code_gen/libninemlnrn
RUN make
ENV LD_LIBRARY_PATH $HOME/packages/pype9/pype9/neuron/cells/code_gen/libninemlnrn:$LD_LIBRARY_PATH
