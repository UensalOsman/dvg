FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY shopeasy ./shopeasy
COPY tools ./tools
COPY proto ./proto
COPY examples ./examples
RUN python -m tools.generate_proto
RUN mkdir -p /data && chown -R 10001:10001 /data /app
USER 10001:10001
EXPOSE 8000 50051
CMD ["python","-m","shopeasy"]
