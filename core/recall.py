from utils.utils import uuid
from prettytable import PrettyTable
from colorama import Fore, Style, init


class Recall:
    def __init__(self):
        self.memory = {}

    def add_task(self, agent_name, task):
        if agent_name not in self.memory:
            self.memory[agent_name] = []
        
        # Create a new task with a unique ID and initial state
        task_with_id = {**task, "id": str(uuid()), "state": "pending", "result": None}
        self.memory[agent_name].append(task_with_id)
        
        return task_with_id["id"]  # Return the task ID for reference

    def update_task(self, agent_name, task_id, updates):
        agent_tasks = self.memory.get(agent_name, [])
        task = next((t for t in agent_tasks if t["id"] == task_id), None)
        
        if task:
            task.update(updates)

    def get_tasks(self, agent_name):
        return self.memory.get(agent_name, [])

    def get_pending_tasks(self, agent_name):
        return [task for task in self.memory.get(agent_name, []) if task["state"] == "pending"]

    def get_task_by_id(self, agent_name, task_id):
        agent_tasks = self.memory.get(agent_name, [])
        return next((task for task in agent_tasks if task["id"] == task_id), None)

    def summarize_tasks(self, agent_name):
        """Summarizes and prints tasks for a specified agent in a table format."""
        tasks = self.get_tasks(agent_name)
        if not tasks:
            print(Fore.YELLOW + f"No tasks found for {agent_name}.")
            return {}

        # Creating a table with PrettyTable
        table = PrettyTable()
        table.field_names = ["Task ID", "Goal", "State", "Result"]

        # Adding each task to the table
        for task in tasks:
            message = task["result"]['message']['content'] if task["result"] else "None"
            message = message[:50] + "..." if len(message) > 50 else message

            table.add_row([task["id"], task["goal"], task["state"], message])

        # Print the table in color and return the summarized dictionary
        print(Fore.CYAN + f"Tasks Summary for {agent_name}:")
        print(table)

        return {task["id"]: task["goal"] for task in tasks}
