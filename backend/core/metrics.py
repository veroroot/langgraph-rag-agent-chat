"""Prometheus metrics configuration."""
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI


def setup_metrics(app: FastAPI):
    """Setup Prometheus metrics for the FastAPI application.
    
    Note: prometheus-fastapi-instrumentator 7.0+ has removed many parameters.
    Using minimal configuration that is compatible with the latest version.
    """
    # Create instrumentator with minimal, compatible configuration
    instrumentator = Instrumentator(
        # Exclude health check endpoints from metrics collection
        excluded_handlers=["/health", "/"],
    ).instrument(app)
    
    # Expose metrics endpoint
    # Note: exclude /metrics from schema to avoid cluttering API docs
    instrumentator.expose(app, include_in_schema=False)

