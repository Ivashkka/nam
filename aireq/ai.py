import g4f

class _G4Fai(object): #base static class for implementing g4f requests with context (later with different models, depends on clientside)
    init = False
    provider=None
    @staticmethod
    def send_req(messages, model):
        if not _G4Fai.init: return "g4f was not inited"
        response = g4f.ChatCompletion.create(
            model=model,
            provider=_G4Fai.provider, #later with asyncio all providers simultaneously
            messages=messages,
        )
        return response

def ask(messages, model): #main function to ask g4f (later g4f or openai, depends on init)
    return _G4Fai.send_req(messages=messages, model=getattr(g4f.models, model))

def initg4f(): #init g4f: set base parameters and toggle g4f on (later g4f or openai)
    g4f.debug.logging = False  # Disable debug logging
    g4f.debug.check_version = False  # Disable automatic version checking
    _G4Fai.provider=g4f.Provider.ChatgptAi
    _G4Fai.init=True
