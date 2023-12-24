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

def load_yaml(path):
    return _YAMLload.load(path)

def load_json(path):
    return _JSONload.load(path)
