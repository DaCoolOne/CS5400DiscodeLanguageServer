import socket
import json
import time
import asyncio

import os
import dotenv
# Keep sensitive bot info in a secure file

import errno
import discord
from discord.ext import commands
from discord import guild_only
# Specifically, this refers to the library installed by running:
# pip install py-cord
# Documentation for Pycord is very easy to locate.

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("localhost", 3540))
client.setblocking(False)

# =================== Server Communication =================== #

def nonBlockSend(port: int, message):
    # Sends data packets to the server, to reduce rendundant code.

    client.send((json.dumps(message) + '\n').encode(encoding='utf8'))
    print('Sent message:', message)


def load(server_id: int, server_name: str, channel_id: int, channel_name:str, message_id: int, code: str):
    # Load a new codeblock into the server

    message = {
        "Name": "Load",
        "Server_ID": str(server_id),
        "Server_Name": server_name,
        "Channel_ID": str(channel_id),
        "Channel_Name": channel_name,
        "Code": code
    }

    nonBlockSend(3540, message)


def run(func_name: str, server_id: int, server_name: str, channel_id: int, channel_name: str, arguments = {}):
    # Tell the server to run a command, probably triggered by a user's slash command

    print ("Trying to run function", func_name)
    message = {
        "Name": "Run",
        "Server_ID": str(server_id),
        "Server_Name": server_name,
        "Channel_ID": str(channel_id),
        "Channel_Name": channel_name,
        "Function": func_name,
        "Message": {  },
    }

    nonBlockSend(3540, message)
    print ("Run request sent...")


async def add_func(Server_id, Function_name, arguments):
    @bot.slash_command(name=Function_name, guild_ids = [Server_id])
    @guild_only()
    async def temp(ctx):
        interaction = await ctx.respond("Handing command to server!")
        origin = await interaction.original_response()
        print(origin)
        run((ctx.command.name), ctx.guild_id, ctx.guild.name, ctx.channel_id, ctx.channel.name)

    await bot.sync_commands(force = True, guild_ids=[Server_id])


async def send_message(channel_id, output):
    channel = bot.get_channel(channel_id)
    await channel.send(output)


async def handle_message(message: dict):
    if message != None :
        if message['Name'] == 'Add Func' :
            # Server says a function compiled and we're good to let users run it

            # !! TODO:  Replace this ID with message['Server_ID'] once the server is ready to handle that
            await add_func(message['Server_ID'], message['Function_name'], message['Arguments'])
            # ID the code was sent in, the name of the function, and the arguments it takes
        elif message['Name'] == 'Send Message' :
            # Server says we need to send output

            # !! TODO:  Replace this id with message['Channel_ID'] once the server is ready to handle that properly
            print("Sending message", message['Message'], "to", message['Channel_ID'])
            await send_message(message['Channel_ID'], message['Message'])
            print("Message should be sent!")
            # The ID of the message that requested the server run the command, and the desired output in response to that.



# ======================== Bot  Setup ======================== #

intents = discord.Intents.default()
intents.guild_messages = True
intents.message_content = True

bot = discord.Bot(intents = intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.event
async def on_message(message):

    # Where was this message sent?
    category = bot.get_channel(message.channel.category_id)

    # Don't freak out if the channel has no category...
    if (category == None) :
        cat_name = "none"
        # Just give a default value that won't set off the command
    else :
        cat_name = category.name

    # Check if the message is code in the appropriate channel
    if message.content.startswith("```") and cat_name == "DISCODE-CODE" :
        server_id = message.guild.id
        server_name = message.guild.name
        channel_id = message.channel.id
        channel_name = message.channel.name
        message_id = message.id
        code = message.content[3:-3]
        load(server_id, server_name, channel_id, channel_name, message_id, code)



# =========================== MAIN =========================== #

async def main_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 3541))
    s.setblocking(False)

    try : 
        while True :
            try :
                message = s.recv(4096)
                obj = json.loads(message.decode(encoding='utf8'))
                await handle_message(obj)
            except BlockingIOError :
                pass
            except Exception as e :
                print('Error: ', e)
                raise e
                break
            await asyncio.sleep(.01)
    except Exception as e :
        print('Error: ', e)
    finally :
        s.close()
        client.close()
            

if __name__ == "__main__" :
    # Process server inputs as a thread on their own,
    # as bot.run seems to be a constant loop
    asyncio.get_event_loop().create_task(main_loop())

    bot.run(token)