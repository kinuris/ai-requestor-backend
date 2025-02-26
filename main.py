from flask import request, Response
from dotenv import load_dotenv

import flask
import requests
import os
import json
import codecs
import translators

app = flask.Flask(__name__)

load_dotenv(override=True)

print("\n")
print(f"LOCAL_URL: {os.getenv('OLLAMA_AI_LOCAL_URL')}")
print(f"AI_MODEL: {os.getenv('OLLAMA_AI_MODEL')}")
print(f"AI_MODEL_SUGGESTION: {os.getenv('OLLAMA_AI_MODEL_SUGGESTION')}")
print("\n")

@app.route('/api/schema/ai-query', methods=['POST'])
def schema_query():
    pass

@app.route('/api/ai-query', methods=['POST'])
def query():
    # Validate request JSON body
    try:
        data = request.get_json()
        if 'prompt' not in data or 'data' not in data:
            return { 'error': 'Missing required fields : ["data", "prompt"]' }, 400
    except:
        return { 'error': 'Invalid JSON in request body' }, 400
    
    # Translate each record in data to plain text format
    prompt_data = ""
    for record in data['data']:
        translator = translators.PlainTextTranslator(record['table'], record['data'], fields=record['fields'] if 'fields' in record else '*')
        prompt_data += f'{translator.translate()}\n\n'

    # Prepare request to Ollama AI service
    url = os.getenv('OLLAMA_AI_LOCAL_URL') 
    req_body = {
        'model': os.getenv('OLLAMA_AI_MODEL'),
        'prompt': data['prompt'] + '\n\n' + prompt_data, 
    }

    # Make request to AI service
    response = requests.post(f'{url}/api/generate', json=req_body, stream=True)
    
    # Check for AI service errors
    if response.status_code != 200:
        return {'error': f'AI service error: {response.status_code}'}, response.status_code

    def stream_responsder():
        # Track AI thinking/reasoning state
        global thinking
        global reasoning_model

        thinking = False
        reasoning_model = False

        # Process response chunks
        for chunk in response.iter_lines():
            chunk = codecs.decode(chunk, 'utf-8')
            chunk = json.loads(chunk)

            # Update thinking state based on special tags
            if '<think>' in chunk['response']:
                thinking = True
                reasoning_model = True
            elif '</think>' in chunk['response']:
                chunk['thinking'] = thinking 
                chunk['reasoning_model'] = reasoning_model

                yield json.dumps(chunk)

                thinking = False 

                continue

            # Add state flags to response
            chunk['thinking'] = thinking 
            chunk['reasoning_model'] = reasoning_model 

            yield json.dumps(chunk)

    # Return streaming response
    return Response(stream_responsder(), mimetype='text/event-stream')

@app.route('/api/schema/ai-suggest', methods=['POST'])
def schema_gen_suggestions():
    pass

@app.route('/api/ai-suggest', methods=['POST'])
def gen_suggestions():
    try:
        data = request.get_json()
        if 'schema' not in data:
            return { 'error': 'Missing required fields : ["schema"]' }, 400
    except:
        return { 'error': 'Invalid JSON in request body' }, 400
    
    # prompt_data = ""
    # for record in data['data']:
    #     translator = translators.PlainTextTranslator(record['table'], record['data'], fields=record['fields'] if 'fields' in record else '*')

    #     prompt_data += f'{translator.translate()}\n'

    prompt_data = json.dumps(data['schema'])

    url = os.getenv('OLLAMA_AI_LOCAL_URL') 
    req_body = {
        'model': os.getenv('OLLAMA_AI_MODEL_SUGGESTION'),
        'prompt': prompt_data, 
    }

    response = requests.post(f'{url}/api/generate', json=req_body, stream=True)
    def stream_responder():
        global thinking
        global reasoning_model

        thinking = False
        reasoning_model = False

        for chunk in response.iter_lines():
            chunk = codecs.decode(chunk, 'utf-8')
            chunk = json.loads(chunk)

            if '<think>' in chunk['response']:
                thinking = True
                reasoning_model = True
            elif '</think>' in chunk['response']:
                chunk['thinking'] = thinking 
                chunk['reasoning_model'] = reasoning_model

                yield json.dumps(chunk)

                thinking = False 

                continue 

            chunk['thinking'] = thinking 
            chunk['reasoning_model'] = reasoning_model 

            # yield chunk['response']
            yield json.dumps(chunk)
        
    return Response(stream_responder(), mimetype='application/json')

@app.route('/api/translate/<method>', methods=['POST'])
def translate(method):
    if not method in ['plain', 'json']:
        return { 'error': 'Method must be plain or json' }, 400

    body = request.get_json()
    if 'data' not in body:
        return { 'error': 'Missing required field: data in request body' }, 400

    data = body['data']
    if 'data' not in data or 'table' not in data:
        return { 'error': 'Missing required fields: data and table in data object' }, 400

    if method == 'plain':
        plain = translators.PlainTextTranslator(data['table'], data['data'], fields=data['fields'] if 'fields' in data else '*')

        return Response(plain.translate(), mimetype='text/plain')
    elif method == 'json':
        return { 'error': 'JSON translation not implemented yet' }, 501
    else:
        return { 'error': 'Invalid translation method' }, 400

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')