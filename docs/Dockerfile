FROM python:3.9

WORKDIR /app/

# Install NodeJS
# --------------
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential
RUN npm install -g npm@8.5.0

# Install Pipx
# ------------
RUN pip install pipx

# Copy Files
# ----------
COPY LICENSE ./
COPY src ./src
COPY docs ./docs
COPY branding ./branding

# Install and Build Docs
# ----------------------
WORKDIR /app/docs
RUN pipx run poetry install
RUN pipx run poetry run sphinx-build -v -W -b html source build

# Define Entrypoint
# -----------------
ENV PORT 5000
ENV REACTPY_DEBUG_MODE=1
ENV REACTPY_CHECK_VDOM_SPEC=0
CMD pipx run poetry run python main.py
