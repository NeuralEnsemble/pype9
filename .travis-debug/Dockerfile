FROM ubuntu:trusty
MAINTAINER tom.close@monash.edu

RUN apt-get update
RUN apt-get install -y git nginx openssh-server git-core openssh-client curl \
                       vim build-essential openssl libreadline6 \
                       libreadline6-dev curl zlib1g zlib1g-dev libssl-dev \
                       libyaml-dev libsqlite3-dev sqlite3 libxml2-dev \
                       libxslt-dev autoconf libc6-dev ncurses-dev automake \
                       libtool bison subversion pkg-config
RUN apt-get install -y build-essential autoconf automake libtool \
                       libreadline6-dev libncurses5-dev libgsl0-dev \
                       python-all-dev python-numpy python-scipy openmpi-bin \
                       libopenmpi-dev

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
RUN ../ruby-$RUBY_VER/configure --prefix=$HOME/ruby/install
RUN make install
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

# Set .vimrc property
RUN echo "set nocompatible" > ~/.vimrc
RUN echo "syntax on" >> ~/.vimrc
RUN echo "set background=dark" >> ~/.vimrc
RUN echo "set hlsearch" >> ~/.vimrc
RUN echo "set incsearch" >> ~/.vimrc
RUN echo "filetype plugin indent on" >> ~/.vimrc
RUN echo "set history=50" >> ~/.vimrc
RUN echo "set backspace=indent,eol,start" >> ~/.vimrc
RUN echo "set number" >> ~/.vimrc
RUN echo "set hidden" >> ~/.vimrc
RUN echo "set shiftwidth=4" >> ~/.vimrc
RUN echo "set expandtab" >> ~/.vimrc
RUN echo "set autoindent" >> ~/.vimrc
RUN echo "set statusline=%<%n:\ %-t\ %m%=%-10.(%l,%c%V%)\ %-5P\ %10.(%L\ %y%)" >> ~/.vimrc
RUN echo "set laststatus=2" >> ~/.vimrc
RUN echo "set path+=cmd,lib,src" >> ~/.vimrc
RUN echo "nnoremap ,l :ls<CR>:buf" >> ~/.vimrc
RUN echo "nnoremap <F11> :bprev<CR>" >> ~/.vimrc
RUN echo "nnoremap <F12> :bnext<CR>" >> ~/.vimrc
RUN echo "imap <Tab> <C-n>" >> ~/.vimrc
RUN echo "imap <S-Tab> <C-p>" >> ~/.vimrc
RUN echo "imap jk <Esc>" >> ~/.vimrc

# Set .bashrc property
RUN sed -i 's/#force_color_prompt/force_color_prompt/' $HOME/.bashrc

# Create build directory
ENV BRANCH=master
RUN echo "Recloning $BRANCH branch 16"
RUN git clone https://github.com/CNS-OIST/PyPe9.git $HOME/pype9
WORKDIR $HOME/pype9
RUN git checkout $BRANCH
RUN travis compile > ci.sh
#RUN echo 'travis' | sudo -S chmod +xs ci.sh

# Fix problems with matrix of python version
RUN sed -i 's/\["2\.7"\]/2.7/g' ci.sh
RUN sed -i 's/\\\[\\"2\.7\\"\\\]/2.7/g' ci.sh

# Add missing branch
RUN sed -i "s/branch\\\\=\\\\'\\\\'/branch=\\\\'$BRANCH\\\\'/g" ci.sh

# Fix symlink to virtualenv Python version
RUN sed -i 's/export GIT_ASKPASS=echo/sudo rm $HOME\/virtualenv\/python2.7\nsudo ln -s $HOME\/virtualenv\/python2.7.12 $HOME\/virtualenv\/python2.7\nexport GIT_ASKPASS=echo/g' ci.sh

# Add build switch
RUN sed -i 's/travis_cmd nosetests/if \[ "$1" == "build" \]; then\n    exit\nfi\ntravis_cmd nosetests/g' ci.sh
RUN echo 'travis' | sudo -S bash ci.sh build
RUN echo 'travis' | sudo -S chown -R travis:travis $HOME/virtualenv

RUN echo "source $HOME/virtualenv/python2.7/bin/activate" >> $HOME/.bashrc
RUN chmod +x ci.sh

