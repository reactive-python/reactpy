FROM python:3.9
WORKDIR /app/

RUN apt-get update
RUN apt-get install -y ca-certificates curl gnupg

# Install NodeJS
# --------------
# Download and import the Nodesource GPG key
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
#Create deb repository
RUN NODE_MAJOR=20
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
# Run Update and Install
RUN apt-get update
RUN apt-get install nodejs -y

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
ENV PORT 5000
ENV REACTPY_DEBUG_MODE=1
ENV REACTPY_CHECK_VDOM_SPEC=0
CMD python main.py
