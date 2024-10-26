import asyncio
from core.cortex import Cortex  # Assuming this is the AI processing module
from core.recall import Recall  # Assuming this handles task memory
from service.services import ServiceFactory
from core.agent import Agent, Boss, Client, SEQUENCE_MODE, PARALLEL_MODE

async def main():
    # Step 1: Initialize core components
    cortex = Cortex()
    recall = Recall()

    cortex.register_service("TextGeneration",{
        "provider": "Ollama",
        "type": "TextGeneration",
        "api_key": ""
    })

    agent_boss = Boss("Boss", cortex, recall)
    agent_writer = Agent("Writer", cortex, recall)

    agent_boss.add_task([
        {
            "goal": "Generate a story", 
            "service": "TextGeneration",
            "prompt": "Once upon a time...",
            "options": {"max_tokens": 100}
        }
    ])

    agent_boss.add_agent_to_crew(agent_writer)

    respose =  await agent_boss.react(SEQUENCE_MODE)
    

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
