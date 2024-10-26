# Importing ServiceFactory from core.services (assuming this module is implemented separately)
from service.services import ServiceFactory
import asyncio

class Cortex:
    def __init__(self):
        self.services = {}

    def register_service(self, name, options):
        self.services[name] = ServiceFactory(options['provider'], 
            options['type'], 
            endpoint=options.get('endpoint', None), 
            api_key=options.get('api_key', None))

    async def think(self, name, options):
        if name in self.services:
            try:
                result = await self.services[name].run(options)
                return result
            except Exception as error:
                print(f"Error occurred while running service {name}: {error}")
                raise error
        else:
            error_message = f"Service {name} not registered"
            print(error_message)
            raise ValueError(error_message)
