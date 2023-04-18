FROM python:3.9

WORKDIR /app/

# Install NodeJS
# --------------
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential
RUN npm install -g npm@8.5.0

# Create Python Venv
# ------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip

# Install ReactPy
# ------------
COPY requirements ./requirements

# Install Dependencies
RUN pip install --no-cache-dir -r requirements/docs-container-env.txt

COPY src ./src
COPY scripts ./scripts
COPY setup.py ./
COPY pyproject.toml ./
COPY MANIFEST.in ./
COPY README.md ./
RUN pip install .[all]

# COPY License
# -----------
COPY LICENSE /app/

# Build the Docs
# --------------
COPY docs/__init__.py ./docs/
COPY docs/app.py ./docs/
COPY docs/examples.py ./docs/
COPY docs/source ./docs/source
COPY branding ./branding
RUN sphinx-build -v -W -b html docs/source docs/build

# Define Entrypoint
# -----------------
ENV PORT 5000
ENV REACTPY_DEBUG_MODE=1
ENV REACTPY_CHECK_VDOM_SPEC=0
CMD python scripts/run_docs.py
