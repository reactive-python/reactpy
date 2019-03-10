# get Conda and Poetry installers
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
wget https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py -O ~/get-poetry.py

# install Conda
bash ~/miniconda.sh -b -p ~/.conda
if ! grep -r "Added when installing Miniconda3" ~/.bashrc
then
    printf "\n# Added when installing Miniconda3\n. ~/.conda/etc/profile.d/conda.sh\n" >> ~/.bashrc
fi

# install Poetry
python ~/get-poetry.py

# load Conda and Poetry into current shell
. ~/.conda/etc/profile.d/conda.sh
. ~/.poetry/env

# set Poetry virtual env location to Conda's
poetry config settings.virtualenvs.path ~/.conda/envs

rm ~/miniconda.sh
rm ~/get-poetry.py
