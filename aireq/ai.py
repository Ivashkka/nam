import g4f
import asyncio

class _G4Fai(object): #base static class for implementing g4f requests with context (later with different models, depends on clientside)
    init = False
    model=None
    providers = [
        g4f.Provider.FakeGpt,
        g4f.Provider.ChatBase,
        g4f.Provider.GeekGpt,
        g4f.Provider.Liaobots,
        g4f.Provider.ChatgptAi,
        g4f.Provider.Bing,
        g4f.Provider.ChatForAi 
    ]
    @staticmethod
    async def send_async_req(provider: g4f.Provider.BaseProvider, messages, model):
        if not _G4Fai.init: return "g4f was not inited"
        try:
            response = await g4f.ChatCompletion.create_async(
                model=model,
                provider=provider, #later with asyncio all providers simultaneously
                messages=messages,
            )
            return({"provider": provider.__name__, "response": response})
        except Exception as e:
            pass

    @staticmethod
    async def ask_all(messages, model):
        calls = [
            _G4Fai.send_async_req(provider, messages, model) for provider in _G4Fai.providers
        ]
        responses = await asyncio.gather(*calls)
        for res in responses:
            if res != None:
                if res["response"] != '':
                    return res["response"]

def ask(messages, model): #main function to ask g4f (later g4f or openai, depends on init)
    return asyncio.run(_G4Fai.ask_all(messages, getattr(g4f.models, model)))

def initg4f(): #init g4f: set base parameters and toggle g4f on (later g4f or openai)
    g4f.debug.logging = False  # Disable debug logging
    g4f.debug.check_version = False  # Disable automatic version checking
    _G4Fai.provider=g4f.Provider.ChatgptAi
    _G4Fai.init=True
