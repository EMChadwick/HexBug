#Written by Ed Chadwick - super OC, do not steal
#imports
import os
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import requests as req
from dotenv import load_dotenv
import datetime
import re
import random

#load the environment variables
try:
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
except:
    log("Environment file missing or incorrectly formatted.")
    quit()
    
#define command prefix character
prefix = "~"

#define client
client =  Bot(description='', command_prefix=prefix, pm_help = False)

#write logs to a file, create one if it doesn't exist
def log(Message):
    f = open("hexLog.txt","a")      
    f.write(str(datetime.datetime.now())+ '   ' + str(Message) + '\n')


def roll(die, num=1):
    tot = 0
    results = {"total":0,"dieRolls":[]}
    for z in range(num):
        chuck = random.randint(1,die)
        results["total"] = results["total"] + chuck
        results["dieRolls"].append([chuck,die])
    return results

#tell the command line HexBug is online!
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    log("Now online as " + str(client.user) + ". Connected to " + str(len(client.guilds)) + " servers")
        
#TODO: make hexbug learn colours, and scream the thomas the tank engine intro in tescos 

#handle events
@client.event
async def on_message(message):
    if(message.content[:1] == prefix):
        #get the message, split it into the command and its arguments for later use. 
        args = message.content.split(" ")
        command = args[0]
        auth = str(message.author)
        authL = auth[:-5]
        #say hi
        if(command == (prefix + "hi")):
            log("saying hi to " + auth + " in " + str(message.guild))
            await message.channel.send( "Hi, I'm HexBug!")
        
        #list commands      
        elif(command == (prefix + "help")):
            await message.channel.send( "Here's what I can do:\n~hi: I'll say hi back!\n~roll n[die]+n[die]....: I'll roll the dice for you!\n~invent: I'll come up with an invention\n~")
         
         
         #say an affirming statement         
        elif(command == (prefix + "affirmation")):
            log("Fetching words of affirmation for " + auth)
            request = req.get('https://www.affirmations.dev/')
            if (request.status_code != 200):
                await message.channel.send("Affirmation machine broke.")
            else:
                await message.channel.send(request.json()["affirmation"])
        
        #come up with a random invention: an x for a y
        elif (command == (prefix + "invent")):
            log("generating ideas to share with " + auth)
            request = req.get('http://itsthisforthat.com/api.php?json')
            if (request.status_code != 200):
                await message.channel.send('Ideas machine broke.')
            else:
                await message.channel.send("What about " + request.json()["this"] + " for " + request.json()['that'])
 
        #look at how you massacred my boy.
        elif (command == (prefix + "kill")):
           log(auth + " initiated kill command \nShutting down...")
           await message.channel.send('Going offline')
           quit()
            
         #show how many users there are  
        elif(command == (prefix + "users")):
            
            await message.channel.send('There are ' + str(message.guild.member_count) + ' users in this server')
            await message.channel.send('I am connected to:')
            for s in client.guilds:
                await message.channel.send(str(s))

        elif(command == (prefix + "servers")):
            await message.channel.send('I am connected to:')
            for s in client.guilds:
                await message.channel.send(str(s))
                
        #roll the dice. State dice before fixed numbers.
        elif(command == prefix + "roll"):
            equation = ' '.join(args[1:]).lower().replace(" ", "").split("+")
            print(equation)
            if(re.match('^([0-9]*[dD](4|6|8|10|12|20)\+?)+(\+[0-9]+)*$','+'.join(equation))):
                total = 0
                rolls = []
                nums = []
                for eq in equation:
                    if 'd' in eq:
                        die = eq.split('d')
                        if re.match('[0-9]',eq[0]):
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
                await message.channel.send('your result is '+ str(total))
                rollSummary = ''
                for item in rolls:
                    rollSummary = rollSummary + 'D'+str(item[1]) +': '+ str(item[0]) + ' '
                for n in nums:
                    rollSummary = rollSummary + '+' + eq + ' '
                await message.channel.send(rollSummary)
            else:
                await message.channel.send('Invalid dice equation, please try again.')
         
         
        else:
            await message.channel.send("Whadda you meeeeaaaan?")
            
    else:
       pass


        
client.run(TOKEN)
