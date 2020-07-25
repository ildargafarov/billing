from environs import Env

_env = Env()

LOG_LEVEL = _env.log_level("LOG_LEVEL",
                           default="INFO")

REDIS_HOST = _env.str("REDIS_HOST",
                      default="localhost")
REDIS_PORT = _env.int("REDIS_PORT",
                      default=6379)
REDIS_PASSWORD = _env.str("REDIS_PASSWORD",
                          default=None)

RABBIT_HOST = _env.str("RABBIT_HOST",
                       default="localhost")

PG_HOST = _env.str("POSTGRES_HOST",
                   default="localhost")
PG_PORT = _env.int("POSTGRES_PORT",
                   default=5432)
PG_DB = _env.str("POSTGRES_DATABASE",
                 default="billing")
PG_USER = _env.str("POSTGRES_USER",
                   default="postgres")
PG_PASSWORD = _env.str("POSTGRES_PASSWORD",
                       default="postgres")

QUEUE_NAME_PREFIX = _env.str("QUEUE_NAME_PREFIX",
                             default="billing")

QUEUES_COUNT = _env.int("QUEUES_COUNT", default=3)
QUEUE_INDEX = _env.int("QUEUE_INDEX", default=None)
