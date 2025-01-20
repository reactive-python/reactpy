FROM python:3.9
WORKDIR /app/

RUN apt-get update

# Install NodeJS
# --------------
RUN curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

# Install Poetry
# --------------
RUN pip install poetry

# Create/Activate Python Venv
# ---------------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip

# Copy Files
# ----------
COPY LICENSE ./
COPY src ./src
COPY docs ./docs
COPY branding ./branding

# Install and Build Docs
# ----------------------
WORKDIR /app/docs
RUN poetry install
RUN sphinx-build -v -W -b html source build

# Define Entrypoint
# -----------------
ENV PORT=5000
ENV REACTPY_DEBUG_MODE=1
ENV REACTPY_CHECK_VDOM_SPEC=0
CMD ["python", "main.py"]
