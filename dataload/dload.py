########################## dload.py ##########################

import yaml
import json

class _YAMLload(object): # class for working with yaml files
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            return None

class _JSONload(object): # class for working with json files
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = json.load(f)
            return data
        except Exception as e:
            return None
    def save(path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            return False

class _TXTload(object): # class for working with all text files
    @staticmethod
    def load(path):
        try:
            with open(path) as f:
                data = f.read()
            return data
        except Exception as e:
            return None

def load_yaml(path):
    return _YAMLload.load(path)

def load_json(path):
    return _JSONload.load(path)

def save_json(path, data):
    return _JSONload.save(path=path, data=data)

def load_txt(path):
    return _TXTload.load(path)

def test_file(path): # check if file exists and readable
    if _TXTload.load(path) == None: return False
    else: return True
