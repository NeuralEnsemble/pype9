FROM ubuntu:trusty
MAINTAINER tom.close@monash.edu

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y nginx openssh-server git-core openssh-client curl
RUN apt-get install -y build-essential
RUN apt-get install -y openssl libreadline6 libreadline6-dev curl zlib1g zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 libxml2-dev libxslt-dev autoconf libc6-dev ncurses-dev automake libtool bison subversion pkg-config

RUN useradd -ms /bin/bash travis; echo "travis:travis" | chpasswd; adduser travis sudo
USER travis
ENV HOME=/home/travis

# Install Ruby
ENV RUBY_VER=2.3.3
RUN mkdir -p $HOME/ruby/build
WORKDIR $HOME/ruby
RUN wget https://cache.ruby-lang.org/pub/ruby/2.3/ruby-$RUBY_VER.tar.gz
RUN tar xzf ruby-$RUBY_VER.tar.gz
WORKDIR $HOME/ruby/build
RUN ls ..
RUN ../ruby-$RUBY_VER/configure --prefix=$HOME/ruby/install
RUN make install
RUN find $HOME/ruby/install
ENV PATH=$HOME/ruby/install/bin/:$PATH

# Install Bundler
RUN gem install bundler --no-ri --no-rdoc

# Install travis
WORKDIR $HOME
RUN git clone https://github.com/travis-ci/travis-build.git
WORKDIR $HOME/travis-build
RUN gem install travis
RUN travis
RUN ln -s `pwd` ~/.travis/travis-build
RUN bundle install

# Create build directory
RUN git clone https://github.com/tclose/PyPe9.git $HOME/pype9
WORKDIR $HOME/pype9
RUN travis compile > ci.sh
