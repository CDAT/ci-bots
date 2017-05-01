#!/usr/bin/env bash
PKG_NAME=cibots
USER=uvcdat

export PATH="$HOME/miniconda/bin:$PATH"
mkdir ~/conda-bld
cd ~/conda-bld
conda config --set anaconda_upload no
export CONDA_BLD_PATH=${HOME}/conda-bld
echo "Cloning recipes"
git clone git://github.com/UV-CDAT/conda-recipes
cd conda-recipes
python ./prep_for_build.py
conda build cibots -c conda-forge
anaconda -t $CONDA_UPLOAD_TOKEN upload -u $USER -l nightly $CONDA_BLD_PATH/noarch/$PKG_NAME-`date +%Y.%m.%d.%H.%M`.*-py_0.tar.bz2 --force
