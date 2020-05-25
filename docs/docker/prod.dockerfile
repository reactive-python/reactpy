FROM python:3.8

# install NodeJS
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential

# install Git to clone repo
RUN apt-get install git

# clone repository
ARG GIT_REPO=https://github.com/rmorshea/idom
ARG GIT_BRANCH=master
RUN git clone $GIT_REPO
WORKDIR /idom
RUN git checkout $GIT_BRANCH

# Install IDOM
RUN pip install -r requirements/docs.txt
RUN pip install .[all]

# Build the documentation
RUN sphinx-build -b html docs/source docs/build

CMD python docs/main.py
