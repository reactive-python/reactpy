FROM python:3.8

WORKDIR app/

# install NodeJS
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential

# Add files
ADD .git ./.git
ADD docs ./docs
ADD idom ./idom
ADD scripts ./scripts
ADD requirements ./requirements
ADD setup.py ./
ADD setup.cfg ./
ADD MANIFEST.in ./
ADD README.md ./
ADD idom/client/static/favicon.ico ./

# Install IDOM
RUN pip install -r requirements/docs.txt
RUN pip install -e .[all]
RUN python -m idom install victory semantic-ui-react

# Build the documentation
RUN sphinx-build -b html docs/source docs/build

ENV PORT 5000
CMD python docs/main.py
