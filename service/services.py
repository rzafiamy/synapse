import aiohttp
from abc import ABC, abstractmethod

class Service(ABC):
    @abstractmethod
    async def run(self, options, callback, fallback):
        raise NotImplementedError("run service not implemented")

class BaseTextGenerator(Service):
    def __init__(self, endpoint, token, model):
        self.endpoint = endpoint
        self.token = token
        self.model = model

    async def run(self, options, callback=None, fallback=None):
        request_body = self.prepare_request_body(options)
        return await self.run_request(request_body, options, callback, fallback)

    def prepare_request_body(self, options):
        # Prepares the common request body format
        prompt = options.get("prompt", "")
        request_body = {
            "model": options.get("model", self.model),
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant about {options.get('category', '')}"
                }
            ]
        }

        # Include conversation context if provided
        if options.get("context"):
            for context_item in options["context"]:
                request_body["messages"].append({
                    "role": "user",
                    "content": f"{context_item['prompt']}\n{context_item['response']['choices'][0]['text']}"
                })

        # Add user prompt to the messages
        request_body["messages"].append({"role": "user", "content": prompt})
        return request_body

    async def run_request(self, request_body, options, callback=None, fallback=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}"
                    },
                    json=request_body
                ) as response:

                    # Check for non-200 status and raise a custom exception with status code
                    if response.status != 200:
                        raise Exception(f"HTTP error! status: {response.status}")

                    # Parse the JSON response data
                    data = await response.json()

                    # Execute callback on success
                    if callable(callback):
                        callback(data)
                    return data

        except Exception as error:
            print("Error during fetch operation:", str(error))
            if callable(fallback):
                fallback(error)
            return {"error": str(error)}


class OpenAITextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="gpt-4o-mini-2024-07-18")

class MistralTextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="mistral-large-latest")

class GroqTextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="llama3-70b-8192")

class InfodevTextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="infodev-ai-2024-07-18")

class AterinietoTextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="llama3.1:latest")

class OllamaTextGenerator(BaseTextGenerator):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, model="llama3.1:latest")


def ServiceFactory(provider, type, endpoint=None, api_key=None):
    if type == 'TextGeneration':
        if provider == 'OpenAI':
            return OpenAITextGenerator("https://api.openai.com/v1/chat/completions", api_key)
        elif provider == 'Infodev':
            return InfodevTextGenerator("https://zara.infodev.ovh/completions", api_key)
        elif provider == 'Groq':
            return GroqTextGenerator("https://api.groq.com/openai/v1/chat/completions", api_key)
        elif provider == 'Aterinieto':
            return AterinietoTextGenerator("https://api.aterinieto.com/v1/chat/completions", api_key)
        elif provider == 'Mistral':
            return MistralTextGenerator("https://api.mistral.ai/v1/chat/completions", api_key)
        elif provider == 'Ollama':
            return OllamaTextGenerator("http://localhost:11434/api/chat", api_key)
    else:
        raise ValueError(f"Unsupported service type: {type}")
