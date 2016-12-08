FROM ubuntu:trusty
MAINTAINER tom.close@monash.edu

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y nginx openssh-server git-core openssh-client curl
RUN apt-get install -y build-essential
RUN apt-get install -y openssl libreadline6 libreadline6-dev curl zlib1g zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 libxml2-dev libxslt-dev autoconf libc6-dev ncurses-dev automake libtool bison subversion pkg-config

RUN useradd -ms /bin/bash travis
USER travis
ENV HOME=/home/travis

# Clone travis
WORKDIR $HOME
RUN git clone https://github.com/travis-ci/travis-build.git

# install RVM, Ruby, and Bundler
RUN gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
RUN \curl -L https://get.rvm.io | bash -s stable
RUN rvm requirements
RUN rvm install 2.3.1
RUN gem install bundler --no-ri --no-rdoc

# Install travis
WORKDIR $HOME/travis-build
RUN gem install travis
RUN travis
RUN ln -s `pwd` ~/.travis/travis-build
RUN /bin/bash -l -c "bundle install"

# Create build directory
RUN git clone https://github.com/tclose/PyPe9.git
WORKDIR $HOME/pype9
RUN travis compile > ci.sh

