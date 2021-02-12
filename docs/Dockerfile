FROM python:3.8

WORKDIR /app/

# Install NodeJS
# --------------
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential

# Upgrad PIP
# ----------
RUN pip install --upgrade pip

# Install IDOM
# ------------
ADD requirements ./requirements
ADD .git ./.git
ADD idom ./idom
ADD scripts ./scripts
ADD setup.py ./
ADD setup.cfg ./
ADD MANIFEST.in ./
ADD README.md ./

RUN pip install -e .[all]
RUN python -m idom install victory semantic-ui-react @material-ui/core

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
