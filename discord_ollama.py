from discord import Intents, Attachment
from os import environ
from ollama import AsyncClient
from discord.ext import commands
from requests import get
from PIL import Image
from io import BytesIO
import base64

discord_token = environ['DISCORD_TOKEN']
ollama_host = environ['OLLAMA_HOST']
ollama_model = environ['OLLAMA_MODEL']
image_model = environ['IMAGE_MODEL']

### SET UP OLLAMA

ollama_client = AsyncClient(
    host=ollama_host,
)

### SET UP DISCORD BOT

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)
chunk_length = 1500

def response_split(response):
    res = ''.join(response)
    if len(res) > chunk_length and res[-1] == ".":
        return True

def get_image_base64(url):
    buffered = BytesIO()
    r = get(url, stream=True)
    r.raw.decode_content = True
    im = Image.open(r.raw)
    im.save(buffered, format='JPEG')
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def convert_to_b64(url):
    pass

@bot.command()
async def chat(ctx, *args, think=False):
    input_str = ' '.join(args)
    message = {'role': 'user',
                'content':input_str
               }
    response = []
    thinking = False

    async for part in await ollama_client.chat(model=ollama_model, messages=[message], stream=True):
        bit = part['message']['content']
        done = part['done']
        if bit == '<think>':
            #print("I'm thinking")
            thinking = True

        if think and thinking:
            #print("I'm writing my thoughts")
            response.append(bit)
            if bit == '\n\n' or done or response_split(response):
                chunk = "".join(response)
                if len(chunk) > 0 and not chunk == "\n\n":
                    await ctx.send(chunk)
                response = []

        elif not thinking:
            #print("I'm not thinking")
            response.append(bit)
            if bit == '\n\n' or done or response_split(response):
                chunk = "".join(response)
                if len(chunk) > 0 and not chunk == "\n\n":
                    await ctx.send(chunk)
                response = []

        if bit == '</think>':
            #print("I'm finished thinking")
            thinking = False

@bot.command()
async def image(ctx, attachment: Attachment, *args, think=False):
    input_str = ' '.join(args)
    message = {'role': 'user',
               'content':input_str,
               'images': [get_image_base64(attachment)]
               }
    response = []
    thinking = False

    async for part in await ollama_client.chat(model=image_model, messages=[message], stream=True):
        bit = part['message']['content']
        done = part['done']
        if bit == '<think>':
            #print("I'm thinking")
            thinking = True

        if think and thinking:
            #print("I'm writing my thoughts")
            response.append(bit)
            if bit == '\n\n' or done or response_split(response):
                chunk = "".join(response)
                if len(chunk) > 0 and not chunk == "\n\n":
                    await ctx.send(chunk)
                response = []

        elif not thinking:
            #print("I'm not thinking")
            response.append(bit)
            if bit == '\n\n' or done or response_split(response):
                chunk = "".join(response)
                if len(chunk) > 0 and not chunk == "\n\n":
                    await ctx.send(chunk)
                response = []

        if bit == '</think>':
            #print("I'm finished thinking")
            thinking = False

bot.run(discord_token)