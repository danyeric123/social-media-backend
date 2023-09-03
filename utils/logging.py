import json
import logging
import os


class CustomFormatter:

    def __init__(self, fmt):
        self.fmt = fmt

    def format(self, record):
        return self.fmt(record)


class GlobalLogManager:

    def __init__(self, service_name: str):
        self.loggers = {}
        self.service_name = service_name
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(
            CustomFormatter(lambda record: json.dumps({
                "level": record.levelname,
                "message": f"{record.getMessage()}",
                "lambda": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
                "timestamp": record.created,
                "service": self.service_name,
                **getattr(record, "extra", {}),
            })))

    def getLogger(self, name):
        logger_name = f"{self.service_name}:{name}"
        if logger_name not in self.loggers:
            self.loggers[logger_name] = logging.getLogger(logger_name)
            self.loggers[logger_name].setLevel(logging.INFO)
            self.loggers[logger_name].addHandler(self.handler)
        return self.loggers[logger_name]


LOG_MANAGER = GlobalLogManager("social-media-backend")
