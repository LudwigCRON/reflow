import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s: %(message)s")

def info(text: str, *args, **kwargs):
  sys.stdout.write("\33[1;37m")
  logging.info(text, *args, **kwargs)
  sys.stdout.write("\33[0m")

def note(text: str, *args, **kwargs):
  sys.stdout.write("\33[1;32m")
  logging.info(text, *args, **kwargs)
  sys.stdout.write("\33[0m")

def warning(text: str, *args, **kwargs):
  sys.stdout.write("\33[1;34m")
  logging.warning(text, *args, **kwargs)
  sys.stdout.write("\33[0m")

def error(text: str, *args, **kwargs):
  sys.stdout.write("\33[1;31m")
  logging.error(text, *args, **kwargs)
  sys.stdout.write("\33[0m")