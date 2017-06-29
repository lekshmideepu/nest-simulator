#!/bin/bash

if [ xMUSIC=1 ]; then

    # Install current MUSIC version.
    - git clone https://github.com/INCF/MUSIC.git music
    - cd music
    - ./autogen.sh
    - ./configure --prefix=$HOME/.cache/music.install
    - make
    - make install
    - cd $HOME/build

  # Change directory back to the NEST source code directory.
   - cd $SOURCEDIR
   
fi