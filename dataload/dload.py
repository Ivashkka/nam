import yaml
import json

class _YAMLload(object):
    @staticmethod
    def load(path):
        with open(path) as f:
            data = yaml.safe_load(f)
        return data

class _JSONload(object):
    @staticmethod
    def load(path):
        with open(path) as f:
            data = json.load(f)
        return data
    def save(path, data):
        with open(path, 'w') as f:
            json.dump(data, f)

def load_yaml(path):
    return _YAMLload.load(path)

def load_json(path):
    return _JSONload.load(path)

def save_json(path, data):
    _JSONload.save(path=path, data=data)
