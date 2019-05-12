FROM python:3.7
ADD . /code
WORKDIR /code
RUN echo "Installing python libraries"
RUN pip install -r requirements.txt
RUN echo "Creating default config file"
COPY config.yaml.example config.yaml
