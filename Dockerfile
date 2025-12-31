FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    openssh-server \
    bash \
    && mkdir -p /var/run/sshd \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY AESCipher.py .
COPY config.py .
COPY bot.py .
COPY controller.py .

CMD ["/usr/sbin/sshd", "-D"]
