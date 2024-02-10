FROM python:slim

RUN apt-get update && \
    apt-get install -y libzbar0 --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/sh app && \
    mkdir -p /app && \
    chown -R app:app /app

COPY . /app
WORKDIR /app
USER app
RUN pip install --no-cache-dir -e .
EXPOSE 1337
CMD [ "python", "-m", "matryoshka", \
    "--port", "1337", \
    "--host", "0.0.0.0"]