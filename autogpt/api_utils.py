# api_utils.py
import requests
import json

def post_api_call(message, unique_id, command_name=None, arguments=None, thoughts=None, reasoning=None, plan=None, criticism=None):
    print("Making API GGG call...")
    url = 'https://mightyhq.com/version-test/api/1.1/wf/autogptq'
    
    # Convert non-string objects to JSON strings
    for var_name in ['message', 'command_name', 'arguments', 'thoughts', 'reasoning', 'plan', 'criticism']:
        var_value = locals()[var_name]
        if not isinstance(var_value, str) and var_value is not None:
            locals()[var_name] = json.dumps(var_value)

    json_data = {
        'message': message,
        'unique_id': unique_id,
        'command_name': command_name,
        'arguments': arguments,
        'thoughts': thoughts,
        'reasoning': reasoning,
        'plan': plan,
        'criticism': criticism
    }
    response = requests.post(url, json=json_data)

