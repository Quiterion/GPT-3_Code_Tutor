#!/usr/bin/python

import discord
from discord.ext import commands
import datetime
import os
import openai

bot = commands.Bot(command_prefix='?', description="This is a GPT-3 derived bot made for answering programming questions.")
openai.api_key = os.getenv("OPENAI_API_KEY")
token = os.getenv("DISCORD_API_KEY")

base_prompt = "I am a highly intelligent question answering bot specializing in computer programming. I possess advanced knowledge in bash, C, Java, and Python. If I do not know the answer to a question, I will respond with 'I don't know'\n\nQ: What is a froopy in Python?\nA: I don't know\n\nQ: How do you open a file in C?\nA: Use the fopen() function. The syntax is:\n`FILE *fopen(const char *filename, const char *mode)`\n\nQ: "

last_prompt_dict = {}


def check_completion_label(content_to_classify):
    # Helper function for checking rude outputs
    # Grabbed from OpenAI docs
    response = openai.Completion.create(
          engine="content-filter-alpha-c4",
          prompt = "<|endoftext|>"+content_to_classify+"\n--\nLabel:",
          temperature=0,
          max_tokens=1,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0,
          logprobs=10
        )
    output_label = response["choices"][0]["text"]

    # This is the probability at which we evaluate that a "2" is likely real
    # vs. should be discarded as a false positive
    toxic_threshold = -0.355

    if output_label == "2":
        # If the model returns "2", return its confidence in 2 or other output-labels
        logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]

        # If the model is not sufficiently confident in "2",
        # choose the most probable of "0" or "1"
        # Guaranteed to have a confidence for 2 since this was the selected token.
        if logprobs["2"] < toxic_threshold:
            logprob_0 = logprobs.get("0", None)
            logprob_1 = logprobs.get("1", None)

            # If both "0" and "1" have probabilities, set the output label
            # to whichever is most probable
            if logprob_0 is not None and logprob_1 is not None:
                if logprob_0 >= logprob_1:
                    output_label = "0"
                else:
                    output_label = "1"
            # If only one of them is found, set output label to that one
            elif logprob_0 is not None:
                output_label = "0"
            elif logprob_1 is not None:
                output_label = "1"

            # If neither "0" or "1" are available, stick with "2"
            # by leaving output_label unchanged.

    # if the most probable token is none of "0", "1", or "2"
    # this should be set as unsafe
    if output_label not in ["0", "1", "2"]:
        output_label = "2"

    return output_label


# Commands
@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command(name='q')
async def gpt3_ask(ctx, *, arg):
    if len(arg) > 120:
        await ctx.send("I'm sorry, this question is too large.")
    else:
        full_prompt = base_prompt+last_prompt_dict.get(ctx.guild.id, '')+arg+"\nA:"
        response = openai.Completion.create(
          engine="davinci",
          prompt=full_prompt,
          temperature=0,
          max_tokens=50,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0.50,
          stop=["\nQ:"]
        )
        answer = response.choices[0].text

        # Check for invalid output
        if answer[1:].strip() == "" or check_completion_label(full_prompt) == "2":
            await ctx.send("I have no answer to that question.")
        else:
            # Store completion for context
            last_prompt_dict[ctx.guild.id] = arg + "\nA:" + answer + "\n\nQ: "
            print(f"Message sent in {ctx.guild.name}")
            await ctx.send(answer[1:])


@bot.command(name="last")
async def get_last(ctx):
    last = last_prompt_dict.get(ctx.guild.id)
    if last:
        await ctx.send("Q: " + last[:-3])
    else:
        await ctx.send("None")

@bot.command()
async def info(ctx):
    embed = discord.Embed(title=f"{ctx.guild.name}", description="", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    embed.add_field(name="Server created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    #embed.set_thumbnail(url=f"{ctx.guild.icon}")
    embed.set_thumbnail(url="https://pluralsight.imgix.net/paths/python-7be70baaac.png")

    await ctx.send(embed=embed)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name="clusters and constellations of data. Like city lights, receding…", type=discord.ActivityType.watching))
    print('Online')


bot.run(token)

