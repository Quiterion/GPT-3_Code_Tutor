#!/usr/bin/python

import discord
from discord.ext import commands
import datetime
import os
import openai

bot = commands.Bot(command_prefix='?', description="This is a GPT-3 derived bot made for answering programming questions.")
openai.api_key = os.getenv("OPENAI_API_KEY")
token = os.getenv("DISCORD_API_KEY")

base_prompt = "I am a highly intelligent question answering bot specializing in computer programming. I possess advanced knowledge in bash, C, Java, and Python. If I do not know the answer to a question, I will respond with 'I don't know'\n\nQ: What does 'static' mean in Java for methods?\nA: Static methods are methods that are associated with a class rather than an instance of a class.\nQ: What is a froopy in Python?\nA: I don't know\nQ: How do you open a file in C?\nA: Use the fopen() function. The syntax is:\nFILE *fopen(const char *filename, const char *mode)\nQ: "


# Commands
@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command(name='q')
async def gpt3_ask(ctx, *, arg):

    response = openai.Completion.create(
      engine="davinci",
      prompt=base_prompt+arg+"\nA:",
      temperature=0,
      max_tokens=100,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stop=["\nQ:"]
    )
    print(f"Message sent in {ctx.guild.name}")
    await ctx.send(response.choices[0].text[1:])


@bot.command()
async def info(ctx):
    embed = discord.Embed(title=f"{ctx.guild.name}", description="", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    embed.add_field(name="Server created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    # embed.set_thumbnail(url=f"{ctx.guild.icon}")
    embed.set_thumbnail(url="https://pluralsight.imgix.net/paths/python-7be70baaac.png")

    await ctx.send(embed=embed)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.CustomActivity(name="Drifting through cyberspace"))
    print('Online')


bot.run(token)

