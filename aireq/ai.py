import uuid
import g4f


class g4fai(object):
    init = False
    model=None
    provider=None
    @staticmethod
    def send_req(messages):
        if (g4fai.init):
            response = g4f.ChatCompletion.create(
                model=g4fai.model,
                provider=g4fai.provider,
                messages=[{"role": "user", "content": messages}],
            )
            return response
        else: return "g4f was not inited"


def ask(messages):
    return g4fai.send_req(messages=messages)

def initg4f():
    g4f.debug.logging = False  # Disable debug logging
    g4f.debug.check_version = False  # Disable automatic version checking
    g4fai.model=g4f.models.gpt_35_turbo
    g4fai.provider=g4f.Provider.ChatBase
    g4fai.init=True
