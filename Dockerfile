# Host the web app for others, e.g. on a free Docker host. Add AI keys as secrets, never in the image.
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
RUN useradd --create-home app
USER app
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "idea-xray serve --host 0.0.0.0 --port ${PORT}"]
