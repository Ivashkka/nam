########################## ai.py ##########################

import g4f
import asyncio
import enum
import time

class AIexcode(enum.Enum):
    Success     =   0
    Fail        =   2

class _G4Fai(object): #base static class for implementing g4f requests with context
    init = False
    providers = []

    @staticmethod
    async def send_async_req(provider: g4f.Provider.BaseProvider, messages, model):
        if not _G4Fai.init: return "g4f was not inited"
        start_time = time.time()
        try:
            response = await g4f.ChatCompletion.create_async(
                model=model,
                provider=provider,
                messages=messages,
            )
            end_time = time.time()
            execution_time = end_time - start_time
            return({"provider": provider.__name__, "response": response, "time": execution_time})
        except Exception as e:
            pass
        end_time = time.time()
        execution_time = end_time - start_time
        return({"provider": provider.__name__, "response": "", "time": execution_time})

    @staticmethod
    async def ask_all(messages, model):
        calls = [
            _G4Fai.send_async_req(provider, messages, model) for provider in _G4Fai.providers
        ]
        responses = await asyncio.gather(*calls)
        for res in responses:
            if res["time"] > 15.0:
                _G4Fai.providers.remove(getattr(g4f.Provider, res["provider"]))
        for res in responses:
            if res != None:
                if res["response"] != '':
                    return res["response"]
        return AIexcode.Fail

def ask(messages, model): #main function to ask g4f (later g4f or openai, depends on init)
    try:
        return asyncio.run(_G4Fai.ask_all(messages, getattr(g4f.models, model)))
    except: return AIexcode.Fail

def initg4f(settings): #init g4f: set base parameters and toggle g4f on (later g4f or openai)
    try:
        g4f.debug.logging = False  # Disable debug logging
        g4f.debug.check_version = False  # Disable automatic version checking
        for prov in settings["providers"]:
            try:
                _G4Fai.providers.append(getattr(g4f.Provider, prov))
            except: pass
        _G4Fai.init=True
        return AIexcode.Success
    except: return AIexcode.Fail
