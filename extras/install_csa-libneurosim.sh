#!/bin/bash                                                                           
# Install libneurosim
git clone https://github.com/INCF/libneurosim.git libneurosim.src
pushd libneurosim.src
#autoreconf -f -i
if [[ "$OSTYPE" == "darwin"* ]]; then brew install automake; fi
./autogen.sh
./configure --prefix=$HOME/.cache/libneurosim.install --with-mpi
make
make install
popd
rm -rf libneurosim.src

# Install csa
git clone https://github.com/INCF/csa.git csa.src
pushd csa.src
git checkout tags/v0.1.8
./autogen.sh
./configure --with-libneurosim=$HOME/.cache/libneurosim.install --prefix=$HOME/.cache/csa.install
make
make install
popd
rm -rf csa.src
