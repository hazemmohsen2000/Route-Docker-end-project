FROM python:3.12.10-alpine3.21 as builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    find /install -type d -name '__pycache__' -exec rm -rf {} + && \
    find /install -type f -name '*.py[co]' -delete && \
    find /install -type d -name 'tests' -exec rm -rf {} + && \
    rm -rf /install/lib/python3.11/site-packages/pip* && \
    rm -rf /install/lib/python3.11/site-packages/setuptools && \
    rm -rf /install/lib/python3.11/site-packages/wheel && \
    rm -rf /install/lib/python3.11/site-packages/*.dist-info

FROM python:3.12.10-alpine3.21

WORKDIR /app

COPY --from=builder /install /usr/local

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
