FROM python:3.8

WORKDIR /app/

# Install NodeJS
# --------------
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential
RUN npm install -g npm@7.13.0

# Create Python Venv
# ------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip

# Install IDOM
# ------------
ADD requirements ./requirements
ADD .git ./.git
ADD src ./src
ADD scripts ./scripts
ADD setup.py ./
ADD setup.cfg ./
ADD MANIFEST.in ./
ADD README.md ./

RUN pip install -e .[all]

ENV IDOM_DEBUG_MODE=1
ENV IDOM_CLIENT_BUILD_DIR=./build

RUN python -m idom install htm victory semantic-ui-react @material-ui/core

# Build the Docs
# --------------
ADD docs/main.py ./docs/
ADD docs/source ./docs/source

RUN pip install -r requirements/build-docs.txt
RUN sphinx-build -b html docs/source docs/build

# Define Entrypoint
# -----------------
ENV PORT 5000
CMD python docs/main.py
