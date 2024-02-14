import os


def set_api_key(api_key):
    os.environ['OPENAI_API_KEY'] = api_key
    return api_key


def stop_api_key(value):
    os.environ.pop('OPENAI_API_KEY', None)
    return 'Stopped API key'
