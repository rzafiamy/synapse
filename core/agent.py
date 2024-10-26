from prettytable import PrettyTable
from colorama import Fore, Style, init
from tqdm import tqdm
import asyncio
import re


# Initialize colorama
init(autoreset=True)

SEQUENCE_MODE = 1
PARALLEL_MODE = 2

class Agent:
    def __init__(self, name, cortex, recall, tools=None):
        self.name = name
        self.cortex = cortex
        self.recall = recall
        self.tools = tools if tools is not None else []
        self.environment = []

    def add_task(self, tasks):
        for task in tasks:
            task_with_id = {
                "goal": task["goal"],
                "service": task["service"],
                "options": {**task.get("options", {}), "prompt": task.get("prompt")}
            }

            task_id = self.recall.add_task(self.name, task_with_id)
            print(Fore.GREEN + f"{self.name} added task: {task['goal']} (ID: {task_id})")

    async def execute_task(self, task_id):
        task = self.recall.get_task_by_id(self.name, task_id)
        if not task:
            print(Fore.RED + f"Task with ID {task_id} not found for {self.name}.")
            return

        if task["state"] != 'pending':
            print(Fore.YELLOW + f'Task "{task["goal"]}" (ID: {task_id}) is already in progress or completed.')
            return

        self.recall.update_task(self.name, task_id, {"state": "in_progress"})
        print(Fore.CYAN + f"{self.name} is executing task: {task['goal']} (state: in_progress, ID: {task_id})")

        if task.get("service") and task.get("options"):
            try:
                result = await self.cortex.think(task["service"], task["options"])
                print(Fore.GREEN + f"{self.name} completed task: {task['goal']} (ID: {task_id})")

                self.recall.update_task(self.name, task_id, {"state": "completed", "result": result})
                if "onSuccess" in task:
                    task["onSuccess"](result)
            except Exception as error:
                print(Fore.RED + f"{self.name} encountered an error with task: {task['goal']} (ID: {task_id})", error)

                self.recall.update_task(self.name, task_id, {"state": "failed", "result": str(error)})
                if "onError" in task:
                    task["onError"](error)
        else:
            print(Fore.YELLOW + f"{self.name} is processing a non-Cortex task: {task['goal']} (ID: {task_id})")
            self.recall.update_task(self.name, task_id, {"state": "completed", "result": "Non-Cortex task completed"})

        print(Fore.GREEN + f"{self.name} finished task: {task['goal']} (ID: {task_id})")

    async def react(self, mode=SEQUENCE_MODE):
        tasks = self.recall.get_pending_tasks(self.name)

        if mode == SEQUENCE_MODE:
            for task in tqdm(tasks, desc=f"{self.name} executing tasks", colour="green"):
                await self.execute_task(task["id"])
        elif mode == PARALLEL_MODE:
            await asyncio.gather(*(self.execute_task(task["id"]) for task in tasks))

    def recall_tasks(self):
        tasks = self.recall.get_tasks(self.name)
        table = PrettyTable(["Task ID", "Goal", "State"])
        for task in tasks:
            table.add_row([task["id"], task["goal"], task["state"]])
        print(Fore.BLUE + f"Recall for {self.name}:\n{table}")
        return tasks

    def recall_task_by_id(self, task_id):
        task = self.recall.get_task_by_id(self.name, task_id)
        print(Fore.MAGENTA + f"Recall for {self.name} with task ID '{task_id}': {task}")
        return task

    def interact_with(self, agent, message):
        print(Fore.YELLOW + f"{self.name} to {agent.name}: {message}")

    def request_help(self, agent, task):
        agent.add_task([task])
        print(Fore.YELLOW + f"{self.name} requested help from {agent.name} for task: {task['goal']}")

    def give_help(self, agent, task_id):
        self.execute_task(task_id)
        print(Fore.GREEN + f"{self.name} helped {agent.name} with task ID: {task_id}")


class Boss(Agent):
    def __init__(self, name, cortex, recall, tools=None):
        super().__init__(name, cortex, recall, tools)
        self.crew = []  # List of agents managed by the Boss

    def add_agent_to_crew(self, agent):
        """Adds an agent to the Boss's crew."""
        self.crew.append(agent)
        print(Fore.GREEN + f"{self.name} added {agent.name} to the crew.")

    def assign_task(self, agent, task):
        """Assigns a task to a specific agent."""
        agent.add_task([task])
        print(Fore.BLUE + f"Boss {self.name} assigned task '{task['goal']}' to {agent.name}")

    async def execute_task(self, task_id):
        """Executes a task for the Boss."""
        await super().execute_task(task_id)
    
    async def react(self, mode=SEQUENCE_MODE):
        """Executes all tasks for the Boss by delegating to crew members based on the generated planning."""
        
        # Retrieve the next pending task for the Boss
        tasks = self.recall.get_pending_tasks(self.name)
        if not tasks:
            print(Fore.RED + f"No pending tasks found for {self.name}.")
            return

        for task in tasks:
            # Create a planning prompt for the crew members
            task['options']['prompt'] = f"""
            You have a mission to accomplish.
            Create a planning for only the following crew members:
            { (", ").join([agent.name for agent in self.crew]) }.
            Expected output format is a list of tasks assigned to each crew member.
            Example:
            [BEG_PLANNING]
            [BEG_AGENT : Agent1 Name]
            Task 1
            Task 2
            Task 3
            ...
            [END_AGENT]
            [BEG_AGENT : Agent2 Name]
            Task 4
            Task 5
            ...
            [END_AGENT]
            ...
            [END_PLANNING]
            Do not add extra information or any introduction.
            """

            # Update the task in the recall
            self.recall.update_task(self.name, task['id'], task)

            # Execute the task using Cortex to generate the planning
            await super().execute_task(task["id"])

            print(Fore.CYAN + f"Results for task '{task['goal']}' (ID: {task['id']}): {task['result']}")
            # Parse the planning result from Cortex
            planning = self.__parse_planning(task['result']['message']['content'])

            # Assign tasks to each crew member based on the parsed planning
            for agent_name, tasks in planning.items():
                agent = next((a for a in self.crew if a.name == agent_name), None)
                if agent:
                    for subtask in tasks:
                        self.assign_task(agent, {"goal": subtask, 'prompt': subtask, "service": task["service"], "options": {}})
                else:
                    print(Fore.YELLOW + f"Warning: Agent '{agent_name}' not found in crew.")

            # react all agents in sequence mode
            for agent in self.crew:
                await agent.react(SEQUENCE_MODE)
                self.recall.summarize_tasks(agent.name)

    def __parse_planning(self, text):
        """
        Parses a structured planning text to create a dictionary mapping agent names to their tasks.

        Args:
            text (str): The planning text containing agents and tasks.

        Returns:
            dict: A dictionary where each key is an agent's name and the value is a list of tasks.
        """
        # Dictionary to store agents and their tasks
        agent_tasks = {}

        # Regular expression pattern to match each agent's section
        # Finds "[BEG_AGENT : AgentName] ... tasks ... [END_AGENT]"
        pattern = r"\[BEG_AGENT\s*:\s*(?P<agent>[\w\s]+)\](?P<tasks>.+?)(?=\[END_AGENT\])"

        # Find all matches for agents and their tasks
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            agent_name = match.group("agent").strip()  # Extract the agent's name
            tasks_section = match.group("tasks").strip()  # Extract the tasks section

            # Split tasks by line, ignoring any blank lines
            tasks = [task.strip() for task in tasks_section.splitlines() if task.strip()]
            if not agent_name in agent_tasks:
                agent_tasks[agent_name] = tasks
            else:
                agent_tasks[agent_name].extend(tasks)

        print(Fore.CYAN + f"Parsed planning: {agent_tasks}")
        return agent_tasks

    def assign_task(self, agent, task):
        """Assigns a task to a specific agent."""
        agent.add_task([task])
        print(Fore.BLUE + f"Boss {self.name} assigned task '{task['goal']}' to {agent.name}")

        


class Client(Agent):
    def request_task(self, boss, task):
        print(Fore.GREEN + f"Client {self.name} requested task: {task['goal']}")
        boss.assign_task(self, task)

    def check_task_progress(self, agent):
        print(Fore.CYAN + f"Client {self.name} checking progress of agent: {agent.name}")
        return agent.recall_tasks()
