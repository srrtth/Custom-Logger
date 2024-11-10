
# FastAPI Enhanced Logging Middleware

This repository contains a custom middleware for FastAPI applications, designed to provide comprehensive and configurable logging. The middleware captures detailed information about each request and response, while including useful features like sampling, latency alerts, sensitive data masking, and structured logging in JSON format.

## Features

- **Customizable Log Format**: Easily configure log details and formats.
- **Sensitive Data Masking**: Masks sensitive fields (e.g., `password`, `token`) in request logs.
- **Latency Alerts**: Logs a warning if request processing time exceeds a specified threshold.
- **Log Sampling**: Configurable sampling rate to control log volume.
- **Request/Response Size Limits**: Controls maximum size of logged request and response bodies.
- **Aggregated Status Code Summary**: Periodically logs aggregated counts of response status codes.
- **Structured JSON Logs**: Consistent JSON schema for easy parsing by log analysis tools.
- **Distributed Tracing Support**: Includes correlation ID for tracing requests across systems.
- **Path Exclusions**: Option to exclude paths (e.g., health checks) from logging.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/fastapi-enhanced-logging.git
   cd fastapi-enhanced-logging
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Import and add the `EnhancedLoggingMiddleware` to your FastAPI application:

   ```python
   from fastapi import FastAPI
   from enhanced_logging_middleware import EnhancedLoggingMiddleware

   app = FastAPI()
   app.add_middleware(EnhancedLoggingMiddleware)
   ```

2. Configure environment variables to customize the logging behavior:

   - **`LOG_SAMPLE_RATE`**: Fraction of requests to log (1.0 = log all requests).
   - **`LATENCY_THRESHOLD`**: Maximum acceptable latency in seconds before a warning is logged.
   - **`MAX_BODY_SIZE`**: Maximum size in bytes for logged request and response bodies.

3. Run the application:

   ```bash
   uvicorn main:app --reload
   ```

## Configuration

You can control various aspects of logging behavior through environment variables or by modifying the middleware code directly:

- `LOG_SAMPLE_RATE`: Set to a decimal between 0.0 and 1.0 to control what fraction of requests are logged.
- `LATENCY_THRESHOLD`: Defines a latency threshold in seconds; requests exceeding this will trigger a warning.
- `MAX_BODY_SIZE`: Specifies the maximum size (in bytes) for logging request/response bodies.

## Example

Here’s an example of a log entry with structured JSON:

```json
{
  "event_type": "http_request",
  "event_timestamp": 1699027733.5465,
  "request": {
    "method": "GET",
    "url": "/api/data",
    "headers": {
      "host": "localhost:8000",
      "accept": "application/json",
      "authorization": "*****"
    },
    "query_params": {
      "filter": "all"
    },
    "body": "Body too large to log"
  },
  "response": {
    "status_code": 200,
    "latency": 0.067
  },
  "metadata": {
    "correlation_id": "d257efc0-8d68-4c74-b829-7e3d12345678",
    "client_ip": "127.0.0.1",
    "hostname": "my-server",
    "app_version": "1.0.0"
  }
}
```

## Development

To run the application locally and make changes:

1. Clone the repository and install dependencies.
2. Update the `EnhancedLoggingMiddleware` class as needed.
3. Run `uvicorn` to test your FastAPI app:

   ```bash
   uvicorn main:app --reload
   ```

## Testing

If you want to add tests, you can install `pytest` and write test cases for your middleware:

```bash
pip install pytest
pytest
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request to suggest improvements or report bugs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
