from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title='Monico-Jarvis')

@app.get('/')
def root():
    return {'status': 'Monico Jarvis is alive in the cloud! Say "Hey Monico" to start.'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)