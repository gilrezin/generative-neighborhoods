from app import app  # Import the Flask instance from 'myapp'
from waitress import serve

if __name__ == '__main__':
    print("starting server...")
    serve(app, host='0.0.0.0', port=5000)  # Use waitress to serve the app