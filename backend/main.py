from app import app
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv('../.env')
    app.run(host='0.0.0.0', port=5000)
