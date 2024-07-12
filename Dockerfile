FROM python:3.12.4-alpine

WORKDIR /app

COPY requirments.txt .

RUN pip install -r requirments.txt
RUN apk update && \
    apk add xorg-server xvfb && \
    apk add --no-cache chromium-chromedriver


COPY . .

CMD ["python", "main.py"]