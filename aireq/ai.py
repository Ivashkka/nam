import g4f

class g4fai(object): #base static class for implementing g4f requests with context (later with different models, depends on clientside)
    init = False
    model=None
    provider=None
    @staticmethod
    def send_req(messages):
        if (g4fai.init):
            response = g4f.ChatCompletion.create(
                model=g4fai.model,
                provider=g4fai.provider, #later with asyncio all providers simultaneously
                messages=messages,
            )
            return response
        else: return "g4f was not inited"

def ask(messages): #main function to ask g4f (later g4f or openai, depends on init)
    return g4fai.send_req(messages=messages)

def initg4f(): #init g4f: set base parameters and toggle g4f on (later g4f or openai)
    g4f.debug.logging = False  # Disable debug logging
    g4f.debug.check_version = False  # Disable automatic version checking
    g4fai.model=g4f.models.gpt_35_turbo
    g4fai.provider=g4f.Provider.ChatgptAi
    g4fai.init=True
