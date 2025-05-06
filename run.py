from app import create_app
import logging
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=port, debug=True)