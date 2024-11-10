import json
import logging
import time
import traceback
import uuid
import socket
import os
import random
from collections import Counter
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import concurrent.futures
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# App version and host information
app_version = "1.0.0"
hostname = socket.gethostname()

# Paths and headers settings
EXCLUDED_PATHS = ["/health", "/favicon.ico"]
LOGGABLE_CONTENT_TYPES = ["application/json", "text/plain"]

# Sampling, size limits, and thresholds
LOG_SAMPLE_RATE = float(os.getenv("LOG_SAMPLE_RATE", 1.0))
MAX_BODY_SIZE = 1024  # Maximum size in bytes for logged body content
LATENCY_THRESHOLD = float(os.getenv("LATENCY_THRESHOLD", 2.0))  # Seconds

# Sensitive fields to mask in request bodies
SENSITIVE_FIELDS = ["password", "token"]

# Initialize FastAPI app and thread pool for async logging
app = FastAPI()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# Status counter for response aggregation
status_counter = Counter()
request_count = 0

# Helper function to mask sensitive fields
def mask_sensitive_data(data):
    if isinstance(data, dict):
        return {k: (mask_sensitive_data(v) if k.lower() not in SENSITIVE_FIELDS else "*****") for k, v in data.items()}
    return data

# Enhanced Logging Middleware
class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global request_count
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start_time = time.time()

        # Skip logging for excluded paths
        if request.url.path in EXCLUDED_PATHS or random.random() > LOG_SAMPLE_RATE:
            return await call_next(request)

        # Try to process the request
        try:
            response = await call_next(request)
        except Exception as e:
            error_log = {
                "event_type": "http_request",
                "event_timestamp": time.time(),
                "correlation_id": correlation_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "method": request.method,
                "url": request.url.path,
                "client_ip": request.client.host,
            }
            logging.error(json.dumps(error_log))
            return JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)

        # Calculate processing time
        process_time = time.time() - start_time
        log_level = self.determine_log_level(response.status_code, process_time)

        # Collect log details
        log_details = {
            "event_type": "http_request",
            "event_timestamp": time.time(),
            "request": {
                "method": request.method,
                "url": request.url.path,
                "headers": {k: (v if k.lower() != "authorization" else "*****") for k, v in dict(request.headers).items()},
                "query_params": dict(request.query_params),
                "body": await self.get_request_body(request)
            },
            "response": {
                "status_code": response.status_code,
                "content": await self.get_response_content(response),
                "latency": process_time,
            },
            "metadata": {
                "correlation_id": correlation_id,
                "client_ip": request.client.host,
                "hostname": hostname,
                "app_version": app_version
            }
        }

        # Log aggregated status summary periodically
        request_count += 1
        status_counter[response.status_code] += 1
        if request_count % 100 == 0:  # Log summary every 100 requests
            logging.info(f"Status Summary: {dict(status_counter)}")
            status_counter.clear()

        # Log asynchronously with appropriate log level
        executor.submit(self.log_async, json.dumps(log_details), log_level)

        return response

    @staticmethod
    def determine_log_level(status_code, process_time):
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        elif process_time > LATENCY_THRESHOLD:
            return logging.WARNING
        return logging.INFO

    async def get_request_body(self, request):
        try:
            body = await request.body()
            body_json = json.loads(body)
            masked_body = mask_sensitive_data(body_json)
            return json.dumps(masked_body)[:MAX_BODY_SIZE] if len(body) <= MAX_BODY_SIZE else "Body too large to log"
        except Exception:
            return "Unable to read body"

    async def get_response_content(self, response):
        content_type = response.headers.get("content-type", "")
        if any(loggable_type in content_type for loggable_type in LOGGABLE_CONTENT_TYPES):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response.body_iterator = iter([response_body])  # Reset iterator for response
            return response_body[:MAX_BODY_SIZE].decode() if len(response_body) <= MAX_BODY_SIZE else "Response too large to log"
        return "Skipped logging due to content type"

    @staticmethod
    def log_async(log_message, log_level):
        if log_level == logging.ERROR:
            logging.error(log_message)
        elif log_level == logging.WARNING:
            logging.warning(log_message)
        else:
            logging.info(log_message)

# Add middleware to the app
app.add_middleware(EnhancedLoggingMiddleware)
