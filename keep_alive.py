from flask import Flask
from threading import Thread
import logging
import socket
import time
import sys
import os
import traceback
from werkzeug.serving import make_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keep_alive.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Silence Flask development server logs to keep console clean
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

# Create Flask app with a unique name
app = Flask('discord_bot_keepalive')
server = None
PORT = 8080
MAX_RETRIES = 3

# Define a route for the root endpoint with explicit endpoint name
@app.route('/', endpoint='home')
def home():
    return "Welcome to Aarohi's system!"

# Define a second route for the status endpoint
@app.route('/status', endpoint='status')
def status():
    return "Aarohi is alive and running smoothly!"

# Health check endpoint for monitoring
@app.route('/health', endpoint='health')
def health():
    return {"status": "healthy", "timestamp": time.time()}, 200

# Define a utility to check if a port is available
def is_port_in_use(port):
    """Check if the specified port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Find an available port starting from the specified one
def find_available_port(start_port=8080, max_attempts=10):
    """Find an available port starting from start_port"""
    current_port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(current_port):
            return current_port
        current_port += 1
    # If we got here, we couldn't find an available port
    logger.warning(f"Could not find an available port after {max_attempts} attempts")
    # Return the original port and hope for the best
    return start_port

class FlaskServerThread(Thread):
    def __init__(self, app, host='0.0.0.0', port=8080):
        Thread.__init__(self, daemon=True)
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        
    def run(self):
        logger.info(f"Starting Flask server on port {self.srv.port}")
        try:
            self.srv.serve_forever()
        except Exception as e:
            logger.error(f"Error in Flask server: {e}")
    
    def shutdown(self):
        logger.info("Shutting down Flask server")
        self.srv.shutdown()

# More robust run function with retry logic
def run(port=PORT):
    """Run the Flask server with error handling and port flexibility"""
    global server
    
    # Try to find an available port
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use")
        port = find_available_port(port)
        logger.info(f"Using alternative port: {port}")
    
    # Attempt to start the server
    retries = 0
    while retries < MAX_RETRIES:
        try:
            logger.info(f"Starting Flask keep-alive server on port {port} (attempt {retries+1}/{MAX_RETRIES})...")
            server = FlaskServerThread(app, port=port)
            server.start()
            logger.info(f"Flask server started successfully on port {port}")
            return True
        except Exception as e:
            logger.error(f"Error starting Flask server (attempt {retries+1}): {e}")
            retries += 1
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in 2 seconds...")
                time.sleep(2)
                # Try a different port on retry
                port = find_available_port(port + 1)
    
    logger.error(f"Failed to start Flask server after {MAX_RETRIES} attempts")
    return False

# More robust keep_alive function with error recovery
def keep_alive():
    """Start the Flask server in a separate thread with error handling"""
    try:
        success = run()
        if not success:
            logger.warning("Could not start keep-alive server, bot will continue without it")
            return False
        logger.info("Keep-alive server started successfully")
        return True
    except Exception as e:
        logger.error(f"Error in keep_alive: {e}")
        logger.error(traceback.format_exc())
        logger.warning("Bot will continue without keep-alive server")
        return False

# Function to stop the keep-alive server gracefully
def stop_keep_alive():
    """Stop the keep-alive server gracefully"""
    global server
    if server:
        try:
            server.shutdown()
            logger.info("Keep-alive server stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping keep-alive server: {e}")
            return False
    return True

# Only run the server directly if this file is run as main
if __name__ == '__main__':
    # Set up signal handlers for graceful shutdown
    import signal
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        stop_keep_alive()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    keep_alive()
    
    # Keep the main thread alive while the server is running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        stop_keep_alive()
