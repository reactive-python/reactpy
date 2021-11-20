FROM python:3.9

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
ADD src ./src
ADD scripts ./scripts
ADD setup.py ./
ADD setup.cfg ./
ADD MANIFEST.in ./
ADD README.md ./

RUN pip install -e .[all]

# Add License
# -----------
Add LICENSE /app/

# Build the Docs
# --------------
ADD run_docs.py ./
ADD docs/__init__.py ./docs/
ADD docs/app.py ./docs/
ADD docs/examples.py ./docs/
ADD docs/source ./docs/source

RUN pip install -r requirements/build-docs.txt
RUN sphinx-build -W -b html docs/source docs/build

# Define Entrypoint
# -----------------
ENV PORT 5000
ENV IDOM_DEBUG_MODE=1
ENV IDOM_CHECK_VDOM_SPEC=0
CMD python scripts/run_docs.py
