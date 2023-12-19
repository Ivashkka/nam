import g4f

g4f.debug.logging = True  # Enable debug logging
g4f.debug.check_version = False  # Disable automatic version checking

# Print all available providers
print([
    provider.__name__
    for provider in g4f.Provider.__providers__
    if provider.working
])

print(g4f.Provider.ChatgptAi.params) # Print supported args for ChatgptAi

# Using automatic a provider for the given model
## Streamed completion
response = g4f.ChatCompletion.create(
    model="gpt-3.5-turbo",
    provider=g4f.Provider.ChatgptAi,
    messages=[{"role": "user", "content": "what's new in the world?"}],
    stream=True,
)

for message in response:
    print(message, flush=True, end='')
