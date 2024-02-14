import logging

# Configure logging to display in terminal only
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a stream handler to output to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Get the root logger and add the stream handler
logger = logging.getLogger()
logger.addHandler(stream_handler)
