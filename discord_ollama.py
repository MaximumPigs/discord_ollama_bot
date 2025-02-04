from discord import Intents, Attachment
from os import environ
from ollama import AsyncClient
from discord.ext import commands
from requests import get
from PIL import Image
from io import BytesIO
import base64
import logging
from uuid import uuid4
from time import time

### GET ENVIRONMENT VARIABLES

discord_token = environ['DISCORD_TOKEN']
ollama_host = environ['OLLAMA_HOST']
chat_model = environ['CHAT_MODEL']
image_model = environ['IMAGE_MODEL']

### SET UP LOGGING

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

### SET UP OLLAMA

ollama_client = AsyncClient(
    host=ollama_host,
)

### SET UP DISCORD BOT

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)
chunk_length = 1500


async def on_command_error(ctx, error):
    await ctx.send(f'An error occurred: {error}')

def response_split(response):
    """
    Determines if response is too long and must be split.
    :param response: A list of response bits (words).
    :return: Boolean.
    """
    res = ''.join(response)
    if len(res) > chunk_length and res[-1] == ".":
        return True


def get_images_from_attachments(attachments: list[Attachment]):
    """
    Returns a list of base64 encoded images from a list of attachments.
    Will only convert attachments with a file type of "image"
    :param attachments: A list of discord Attachment objects.
    :return: A list of base64 encoded images.
    """
    images = []
    for attachment in attachments:
        content_type = attachment.content_type
        file_type = content_type.split('/')[0]
        sub_type = content_type.split('/')[1]
        if file_type == 'image':
            images.append(get_image_base64(attachment.url, sub_type))
    return images


def get_image_base64(url, fmt):
    """
    Returns a base64 encoded image from a URL.
    Stores file in a buffer as to not write anything to disk.
    :param url: A URL obtained from a discord Attachment object.
    :param fmt: The image format obtained from a discord Attachment object.
    :return: A base64 string of the image.
    """
    buffered = BytesIO()
    r = get(url, stream=True)
    r.raw.decode_content = True
    im = Image.open(r.raw)
    im.save(buffered, format=fmt)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@bot.command()
async def chinabot(ctx, *args, think = False):

    uuid = uuid4()
    bits = 0
    chunks = 0
    response = []
    start = time()
    input_str = ' '.join(args)
    attachments = ctx.message.attachments
    thinking = False

    logger.info(f"Command Invocation - uuid: '{uuid}', "
                f"user: '{ctx.message.author}', "
                f"command: '{ctx.command}', "
                f"argument: '{input_str}', "
                f"attachment_count: '{len(attachments)}'")

    for attachment in attachments:
        logger.debug(f"Attachment Uploaded - uuid: '{uuid}', "
                     f"user: '{ctx.message.author}', "
                     f"id: '{attachment.id}', "
                     f"filename: '{attachment.filename}', "
                     f"size: '{attachment.size}', "
                     f"content_type: '{attachment.content_type}')")

    images = get_images_from_attachments(attachments)

    if len(images) > 0:
        model = image_model
    else:
        model = chat_model

    logger.debug(f"Model Selection - uuid: '{uuid}', model: '{model}'")

    message = {'role': 'user',
               'content': input_str,
               'images': images}

    async with ctx.typing():

        async for part in await ollama_client.chat(model=model, messages=[message], stream=True):

            bits += 1
            bit = part['message']['content']
            done = part['done']
            if bit == '<think>':
                logger.debug(f"Think Block - uuid: '{uuid}', message: 'Start'")
                thinking = True

                if think:
                    logger.debug(f"Think Block - uuid: '{uuid}', message: 'Writing'")

                else:
                    logger.debug(f"Think Block - uuid: '{uuid}', message: 'Skipping'")

            if (think and thinking) or (not thinking):
                response.append(bit)
                if bit == '\n\n' or done or response_split(response):
                    chunk = "".join(response)
                    chunks += 1
                    if len(chunk) > 0 and not chunk == "\n\n":
                        await ctx.send(chunk)
                    response = []

            if bit == '</think>':
                logger.debug(f"Think Block - uuid: '{uuid}', message: 'End'")
                thinking = False

            if done:
                end = time()
                duration = round(end - start,2)
                logger.info(f"Command Completion - uuid: '{uuid}', "
                            f"user: '{ctx.message.author}', "
                            f"command: '{ctx.command}', "
                            f"duration_s: '{duration}' "
                            f"bits: {bits}, "
                            f"chunks: {chunks}")

bot.on_command_error = on_command_error
bot.run(discord_token, log_handler=handler)