#Written by Ed Chadwick - super OC, do not steal
#imports
import os
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import requests as req
from decouple import config
import datetime
import re
import random
import time

def log(Message):
    f = open("hexLog.txt","a")      
    f.write(str(datetime.datetime.now())+ '   ' + str(Message) + '\n')
    
#load the environment variables
try:
    TOKEN = config('DISCORD_TOKEN')
except:
    log("Environment file missing or incorrectly formatted.")
    quit()
    
#define command prefix character
prefix = "~"

#define client
client =  Bot(description='', command_prefix=prefix, pm_help = False)

#write logs to a file, create one if it doesn't exist
command_library = {
        "help":["list_commands", False],
        "roll": ["Process_dice",False],
        "flip": ["flip",False],
        "hi": ["greet",False],
        "invent": ["invent",False],
        "affirmation":["affirmation", False],
        "users": ["count_users",True],
        "servers": ["list_servers",True],
        "kill": ["kill_bot",True]
        }


def roll(die, num=1):
    results = {"total":0,"dieRolls":[]}
    for z in range(num):
        chuck = random.randint(1,die)
        results["total"] = results["total"] + chuck
        results["dieRolls"].append([chuck,die])
    return results


# Hello world!
def greet(message, args):
    log("saying hi to " + str(message.author) + " in " + str(message.guild))
    await message.channel.send( "Hi, I'm HexBug!")

# no shame in asking for help.
def list_commands(message, args):
    cmd_list = ''
    for cmd in command_library.keys():
        cmd_list = cmd_list + '~{0}'.format(cmd)

# WHERE'S RACHEL? 
def flip(message, args):
    await message.channel.send('flipping a coin...')
    log("Flipping a coin for {0} in {1}".format(str(message.author), str(message.guild)))
    flip = roll(2)
    time.sleep(1.2)
    if flip["total"] == 1:
        await message.channel.send('Heads!')
        log('Heads')
    else:
        await message.channel.send('Tails!')
        log('Tails')
                
# Process the dice equation            
def process_dice(message, args):
    equation = ' '.join(args[1:]).lower().replace(" ", "").split("+")
    log("rolling {0} for {1} in {2}".format('+'.join(equation),str(message.author),str(message.guild)))
    total = 0
    rolls = []
    nums = []
    rollSummary = ''
    error = ''
    if(re.match('^([0-9]*[dD](4|6|8|10|12|20)\+?)+(\+[0-9]+)*$','+'.join(equation))) and len(equation) <= 10:
        for eq in equation:
            if 'd' in eq:
                die = eq.split('d')
                if re.match('[0-9]',eq[0]):
                    if int(die[0]) >=20:
                        error = 'Too many dice'
                        return(0,'',error)
                    rl = roll(int(die[1]),int(die[0]))
                    total = total + rl["total"]

                else:
                    rl = roll(int(die[1]))
                    total = total + rl["total"]
                for r in rl["dieRolls"]:
                    rolls.append(r)
            elif (re.match('^[0-9]+$',eq)):
                total = total + int(eq)
                nums.append(eq)
        for item in rolls:
            rollSummary = rollSummary + 'D'+str(item[1]) +': '+ str(item[0]) + ' '
        for n in nums:
            rollSummary = rollSummary + '+' + eq + ' '

    else:
        if len(equation) > 10:
            error = 'Dice Equation too long'
        else:
            error = 'Invalid dice equation, please try again.'
    if len(error) > 0:
        await message.channel.send(error)
        log('{0} raised error: {1} in {2}'.format(str(message.author),error,str(message.guild)))
    else:
        await message.channel.send('your result is {0}\n{1}'.format(total,rollSummary))
        log("Result: {0}".format(rollSummary))


# come up with a random invention: an x for a y
def invent(message, args):
    log("generating ideas to share with " + str(message.author))
    request = req.get('http://itsthisforthat.com/api.php?json')
    if (request.status_code != 200):
        await message.channel.send('Ideas machine broke.')
    else:
        await message.channel.send("What about " + request.json()["this"] + " for " + request.json()['that'])

# Like a fortune cookie you know will be good.
def affirmation(message, args):
    log("Fetching words of affirmation for " + str(message.author))
    request = req.get('https://www.affirmations.dev/')
    if (request.status_code != 200):
        await message.channel.send("Affirmation machine broke.")
    else:
        await message.channel.send(request.json()["affirmation"])


# ADMIN: look at how they massacred my boy.
def kill(message, args):
    log(str(message.author) + " initiated kill command \nShutting down...")
    await message.channel.send('Going offline')
    quit()


#ADMIN: show user count on current server
def count_users(message, args):
    await message.channel.send('There are ' + str(message.guild.member_count) + ' users in this server')

# ADMIN: list all servers HexBug is connected to.
def list_servers(message, args):
    await message.channel.send('I am connected to:')
    for s in client.guilds:
        await message.channel.send(str(s))
        
        
        
        

#tell the command line HexBug is online!
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    log("Now online as " + str(client.user) + ". Connected to " + str(len(client.guilds)) + " servers")
        

#handle message events
@client.event
async def on_message(message):
    if(message.content[:1] == prefix):
        #get the message, split it into the command and its arguments for later use. 
        args = message.content.split(" ")
        command = args[0]
        key_word = command.replace(prefix,'')
        authL = str(message.author)[:-5]
        
        #Check the command exists in the dictionary, and that the user is me if it's an admin command, then run it.
        if key_word in command_library.keys():
            if command_library[key_word][1] == True and str(message.author) != "Hexadextrous#4159":
                await message.channel.send("Access Denied: {0} command for executive users only".format(command))
            else:
                locals()[command_library[key_word][0]](message, args)     
        else:
            await message.channel.send('Command '+ command + ' not found. Try running ~help')
            
    else:
       pass


        
client.run(TOKEN)
