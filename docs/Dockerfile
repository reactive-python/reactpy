FROM python:3.11
WORKDIR /app/

RUN apt-get update

# Create/Activate Python Venv
# ---------------------------
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python Build Dependencies
# ---------------------------------
RUN pip install --upgrade pip poetry hatch uv
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Copy Files
# ----------
COPY LICENSE ./
COPY README.md ./
COPY pyproject.toml ./
COPY src ./src
COPY docs ./docs
COPY branding ./branding

# Install and Build Docs
# ----------------------
WORKDIR /app/docs/
RUN poetry install -v
RUN sphinx-build -v -W -b html source build

# Define Entrypoint
# -----------------
ENV PORT=5000
ENV REACTPY_DEBUG=1
ENV REACTPY_CHECK_VDOM_SPEC=0
CMD ["python", "main.py"]
