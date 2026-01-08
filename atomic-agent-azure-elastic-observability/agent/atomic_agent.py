import os
import json
import time
import random
import datetime
import logging
from logging.handlers import RotatingFileHandler

from elasticapm import Client
from elasticapm.handlers.logging import LoggingHandler
from elasticapm.instrumentation.control import instrument

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional
    pass


def get_env(name, default=""):
    value = os.getenv(name)
    return value if value else default


def configure_logging(log_file):
    logger = logging.getLogger("atomic-agent")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def configure_apm():
    server_url = get_env("ELASTIC_APM_SERVER_URL")
    secret_token = get_env("ELASTIC_APM_SECRET_TOKEN")
    service_name = get_env("ELASTIC_APM_SERVICE_NAME", "atomic-agent-service")
    environment = get_env("ELASTIC_APM_ENVIRONMENT", "dev")

    if not server_url or not secret_token:
        print("[WARN] APM not fully configured; running in no-send mode.")
        client = Client({
            "SERVICE_NAME": service_name,
            "ENVIRONMENT": environment,
            "DISABLE_SEND": True,
        })
        return client

    client = Client({
        "SERVICE_NAME": service_name,
        "SERVER_URL": server_url,
        "SECRET_TOKEN": secret_token,
        "ENVIRONMENT": environment,
    })
    instrument()
    return client


def load_config(path="config.yaml"):
    import yaml
    if not os.path.exists(path):
        return {
            "agent_id": "agent-01",
            "log_file": "agent.log",
            "interval_seconds": 2,
            "actions": ["fetch_data", "process_order", "run_batch"],
            "success_rate": 0.8,
            "min_latency_ms": 100,
            "max_latency_ms": 800,
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def simulate_action(config, logger, apm_client):
    actions = config.get("actions", ["fetch_data", "process_order", "run_batch"])
    success_rate = float(config.get("success_rate", 0.8))
    min_latency = int(config.get("min_latency_ms", 100))
    max_latency = int(config.get("max_latency_ms", 800))
    agent_id = config.get("agent_id", "agent-01")

    action = random.choice(actions)
    start = time.time()

    time.sleep(random.uniform(min_latency / 1000.0, max_latency / 1000.0))
    latency_ms = int((time.time() - start) * 1000)

    success = random.random() <= success_rate
    status = "OK" if success else "ERROR"

    if success:
        msg_detail = "completed successfully"
    else:
        msg_detail = random.choice([
            "timeout while calling downstream API",
            "database connection failure",
            "invalid input payload",
            "permission denied on resource",
        ])

    message = f"{action} {msg_detail}."

    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "agent_id": agent_id,
        "action": action,
        "status": status,
        "message": message,
        "latency_ms": latency_ms,
    }

    logger.info(json.dumps(log_entry))

    apm_client.begin_transaction("atomic-agent-workload")
    result = "success" if success else "failure"
    apm_client.end_transaction(action, result)


def main():
    config = load_config()
    log_file = config.get("log_file", "agent.log")
    interval = int(config.get("interval_seconds", 2))

    logger = configure_logging(log_file)
    apm_client = configure_apm()

    print(f"[INFO] Atomic Agent starting. log_file={log_file}, interval={interval}s")
    try:
        while True:
            simulate_action(config, logger, apm_client)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[INFO] Atomic Agent stopped by user.")


if __name__ == "__main__":
    main()
