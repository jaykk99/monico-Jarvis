from fastapi import FastAPI
app = FastAPI()

@app.get('/')
def home():
    return {'message': 'Monico Jarvis is alive in the cloud! Say your command.'}

@app.post('/chat')
def chat(query: str):
    return {'response': f'Monico here. Processing: {query}. (Full agent coming online)'}