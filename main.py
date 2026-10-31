import discord
import os
import json
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import uuid

load_dotenv()

class TodoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        self.tasks = self.load_data()
        self.priority_icons = list(" 🔵🟢🟤🟣🟡🟠🔴🔥")

    def load_data(self):
        try:
            with open("tasks.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except:
            return {}

    def save_data(self):
        try:
            with open("tasks.json", "w", encoding="utf-8") as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=4)
        except:
            return {}

    async def on_ready(self):
        print(f"Enter as {self.user}")
        try:
            synced = await self.tree.sync()
            print(f"Synced commands: {len(synced)}")
        except Exception as e:
            print(e)

bot = TodoBot()

async def task_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})
    
    choices = []

    for id, task in user_tasks.items():
        if current.lower() in task["task"].lower():
            name = task["task"] if len(task["task"]) <= 100 else task["task"][:97] + "..."

            choices.append(app_commands.Choice(name=name, value=id))

    return choices[:25]

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! Latency: {round(bot.latency * 1000)} ms')

@bot.tree.command(name="add", description="Add task")
async def add_task(interaction: discord.Interaction, task: str, priority: int = 0):
    user_id = str(interaction.user.id)
    if not user_id in interaction.client.tasks:
        bot.tasks[user_id] = {}
        bot.save_data()
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})

    if 0 <= priority < len(bot.priority_icons):
        if len(task) < 1000:
            task_id = str(uuid.uuid4())
            user_tasks[task_id] = {
                "task": task,
                "done": False,
                "priority": priority
            }
            bot.save_data()
            await interaction.response.send_message(f"Task added: `{task}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"The message length must be between 0-1000", ephemeral=True)
    else:
        await interaction.response.send_message(f"The priority field must be in range from 0 to {len(bot.priority) - 1}", ephemeral=True)

@bot.tree.command(name="list", description="List of all tasks")
async def task_list(interaction: discord.Interaction):
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})

    embed = discord.Embed(title="Your task list")
    for data in user_tasks.values():
        status = "✅" if data["done"] else "⏳"
        icon = bot.priority_icons[data["priority"]]
        task = data["task"]
        embed.add_field(name="", value=f"- {status} {icon} **{task}**\n", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="del", description="Delete task")
@app_commands.autocomplete(task=task_autocomplete)
async def delete_task(interaction: discord.Interaction, task:str):
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})

    if user_tasks.pop(task, None):
        bot.save_data()
        await interaction.response.send_message(f"Task deleted: {task}", ephemeral=True)
    else:
        await interaction.response.send_message(f"This task does not exist", ephemeral=True)

@bot.tree.command(name="done", description="Mark task as done (delete)")
@app_commands.autocomplete(task=task_autocomplete)
async def task_done(interaction: discord.Interaction, task:str):
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})

    if task in user_tasks:
        user_tasks[task]["done"] = True
        bot.save_data()
        await interaction.response.send_message(f"Task marked as done: {task}", ephemeral=True)
    else:
        await interaction.response.send_message(f"This task does not exist", ephemeral=True)

@bot.tree.command(name="stats", description="Check your to-do statistic")
async def stats(interaction: discord.Interaction):
    user_tasks = interaction.client.tasks.get(str(interaction.user.id), {})

    tasks_number = 0
    done_tasks_number = 0
    productivity_percent = int()

    for task in user_tasks.values():
        tasks_number += 1
        if task["done"]: done_tasks_number += 1

    if tasks_number > 0:
        productivity_percent = round(done_tasks_number / tasks_number * 100)

        embed = discord.Embed(title="Your statistic")
        embed.add_field(name="", value=f"Tasks number: {tasks_number}\nDone tasks number: {done_tasks_number}\nProductivity: {productivity_percent}%", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("There are no tasks in your to-do list yet", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))