FROM python:3.8

WORKDIR app/

# install NodeJS
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get install -yq nodejs build-essential

ADD ./ ./

# Install IDOM
RUN pip install -r requirements/docs.txt
RUN pip install .[all]

# Build the documentation
RUN sphinx-build -b html docs/source docs/build

EXPOSE 80

CMD python docs/main.py
