import logging
import os
from dotenv import load_dotenv
load_dotenv
# Configure logging
logging = logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

MODEL= "o4-mini"
PROJECT_NAME = os.getenv("PROJECT_NAME", "my_generated_app")