import sys

from loguru import logger

from .cli import main


logger.remove(0)
logger.add(sys.stdout, format="{message}", level="INFO")


if __name__ == "__main__":
    main()
