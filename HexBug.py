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



def roll(die, num=1):
    results = {"total":0,"dieRolls":[]}
    for z in range(num):
        chuck = random.randint(1,die)
        results["total"] = results["total"] + chuck
        results["dieRolls"].append([chuck,die])
    return results

def process_dice(equation):
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
    return(total, rollSummary, error)

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
            await message.channel.send( "Here's what I can do:\n~hi: I'll say hi back!\n~roll n[die]+n[die]....: I'll roll the dice for you!\n~invent: I'll come up with an invention\n~flip: I'll flip a coin for you.")
         
         
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
        
        #flips a coin.
        elif(command == prefix + "flip"):
            await message.channel.send('flipping a coin...')
            log("Flipping a coin for {0} in {1}".format(auth, str(message.guild)))
            flip = roll(2)
            time.sleep(1.2)
            if flip["total"] == 1:
                await message.channel.send('Heads!')
                log('Heads')
            else:
                await message.channel.send('Tails!')
                log('Tails')
            
        #roll the dice. State dice before fixed numbers.
        elif(command == prefix + "roll"):
            equation = ' '.join(args[1:]).lower().replace(" ", "").split("+")
            log("rolling {0} for {1} in {2}".format('+'.join(equation),auth,str(message.guild)))
            tot, summ, err = process_dice(equation)
            if len(err) > 0:
                await message.channel.send(err)
                log('{0} raised error: {1} in {2}'.format(auth,err,str(message.guild)))
            else:
                await message.channel.send('your result is {0}\n{1}'.format(tot,summ))
                log("Result: {0}".format(summ))
        else:
            await message.channel.send('Command '+ command + ' not found. Try running ~help')
            
    else:
       pass


        
client.run(TOKEN)
