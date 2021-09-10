#!/usr/bin/python
import discord
from discord.ext import commands
import datetime
import os
import openai

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='?', description="This is a GPT-3 derived bot made for answering programming questions.", intents=intents)
openai.api_key = os.getenv("OPENAI_API_KEY")
token = os.getenv("DISCORD_API_KEY")

base_prompt = "I am a highly intelligent question answering bot specializing in computer programming. I possess advanced knowledge in bash, C, Java, and Python. If I do not know the answer to a question, I will respond with 'I don't know'. If a question is not about coding, I will not respond.\n\nQ: What is a froopy in Python?\nA: I don't know\n\nQ: How do you open a file in C?\nA: Use the fopen() function. The syntax is:\n`FILE *fopen(const char *filename, const char *mode)`\n\nQ: "



def check_completion_label(content_to_classify, author_id):
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
          logprobs=10,
          user=author_id
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
class Gpt3Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.last_prompt_dict = {}

    @commands.command(name='q')
    async def gpt3_ask(self, ctx, *, arg):
        if len(arg) > 120:
            await ctx.send("I'm sorry, this question is too large.")
        else:
            await ctx.channel.trigger_typing()
            author_id = ctx.author.name + ctx.author.discriminator
            full_prompt = base_prompt+self.last_prompt_dict.get(ctx.channel.id, '')+arg+"\nA:"
            response = openai.Completion.create(
              engine="davinci",
              prompt=full_prompt,
              temperature=0,
              max_tokens=75,
              top_p=1,
              frequency_penalty=0,
              presence_penalty=0.50,
              stop=["\nQ:","\nA:"],
              user=author_id
            )
            answer = response.choices[0].text

            # Check for invalid output
            if answer[1:].strip() == "" or check_completion_label(full_prompt, author_id) == "2":
                await ctx.send("I have no answer to that question.")
            else:
                # Store completion for context
                self.last_prompt_dict[ctx.channel.id] = arg + "\nA:" + answer + "\n\nQ: "
                await ctx.send(answer[1:])
                if ctx.guild is not None:
                    print(f"Message sent in {ctx.guild.name}: {ctx.channel.name}")
                    print(f"Guild ID: {ctx.guild.id}")
                elif ctx.channel.type == discord.ChannelType.private:
                    print(f"Message sent in DM to: {ctx.channel.recipient}")



    @commands.command(name="last")
    async def get_last(self, ctx):
        last = self.last_prompt_dict.get(ctx.channel.id)
        if last:
            await ctx.send("Q: " + last[:-3])
        else:
            await ctx.send("None")


class misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

    @commands.command()
    async def servinfo(self, ctx):
        try:
            embed = discord.Embed(title=f"{ctx.guild.name}", description="", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
            embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{self.bot.user.avatar_url}")
            embed.add_field(name="Server created at", value=f"{ctx.guild.created_at}")
            embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
            embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
            embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
            embed.set_thumbnail(url=f"{ctx.guild.icon_url}")
            await ctx.send(embed=embed)
        except:
            await ctx.send("Oops! It seems like I don't have embed permissions.")

    @commands.command()
    async def support(self, ctx):
        try:
            embed = discord.Embed(title=f"Help support my API fees!", description="Each answer costs my maintainer a few cents to generate, which can add up quickly! Please help them cover the cost :)", timestamp=datetime.datetime.utcnow(), color=discord.Color.red())
            embed.set_author(name=f"{self.bot.user.name}", icon_url=f"{self.bot.user.avatar_url}")
            embed.add_field(name="Buy me a coffee with kofi", value="https://ko-fi.com/andromeda106", inline=False)
            embed.set_thumbnail(url="https://uploads-ssl.webflow.com/5c14e387dab576fe667689cf/5ca5bf1dff3c03fbf7cc9b3c_Kofi_logo_RGB_rounded.png")
            await ctx.send(embed=embed)
        except:
            await ctx.send("Please help support my API fees on kofi: https://ko-fi.com/andromeda106")

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name="?help for help, ?q to ask questions :)", type=discord.ActivityType.watching))
    print('Online')


if __name__ == "__main__":
    bot.add_cog(Gpt3Commands(bot))
    bot.add_cog(misc(bot))
    bot.run(token)
