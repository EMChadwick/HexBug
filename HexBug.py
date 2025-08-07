import os
import json
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import requests as req
from decouple import config
import datetime
import re
import random
import time
import HexCharacterSheet as sheets
import userManager as usr


# Quick, write that down!
def log(Message):
    with open("hexLog.txt","a") as f:     
        f.write(str(datetime.datetime.now())+ '   ' + str(Message) + '\n')
    
#load the environment variables
try:
    TOKEN = config('DISCORD_TOKEN')
except:
    log("Environment file missing or incorrectly formatted.")
    quit()
    
#define command prefix character
prefix = "~"

#define which events the bot can recieve
intents = discord.Intents.default()
intents.message_content = True 

#define client
client =  Bot(description='', command_prefix=prefix, pm_help = False, intents=intents)

#map commands to function names and whether they're admin-only or not
command_library = {
        "help":["list_commands", False, ""],
        "hi": ["greet",False, ""],
        "roll": ["process_dice",False, "*xD[die]+xD[die]...* or [skill/ability]"],
        "save": ["save_roll", False, "[ability]"],
        "flip": ["flip",False, ""],
        "luck": ["user_luck", False, ""],
        "invent": ["invent",False, ""],
        "users": ["count_users",True, ""],
        "servers": ["list_servers",True, ""],
        "kill": ["kill_bot",True, ""],
        "spell": ["spell_lookup", False, "*[spell name]*"],
        "condition": ["get_condition", False, "*[condition name]*"],
        "sheet": ["handle_sheet", False, "Interact with character sheet. ~sheet help"]
        }

wizard_names = ["aganazzar's",
                "snilloc's",
                "tasha's",
                "otto's",
                "mordenkainen's",
                "tenser's",
                "melf's",
                "nystul's",
                "bigby's",
                "otiluke's",
                "leomund's",
                "evard's",
                "rary's",
                "drawmij's"]


# Generate a profile for a user
def create_profile_if_none(auth_ID, auth_L):
    user_dir = os.path.join(os.getcwd(), 'UserProfiles', auth_ID)
    user_file = os.path.join(os.getcwd(), 'UserProfiles', auth_ID, 'UserData.json')
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    if not os.path.exists(user_file):
        with open('UserDataTemplate.json') as template:
            new_data = json.load(template)
            new_data['Username'] = auth_L
        with open(os.path.join(user_dir, 'UserData.json'), 'w') as new_profile:
            json.dump(new_data, new_profile)
        log('New profile created for {0}#{1}'.format(auth_L, auth_ID))


# Who's in charge here?
def get_admins():
    if os.path.exists('Admins.json'):
        with open('Admins.json') as adminfile:
            a_list = json.load(adminfile)['admins']
            print(a_list)
            return a_list
    else:
        print("failed to load admins")
        return []


# Good or bad, it's going in the book.
def update_user_Rolls(auth_ID, dice, crits, fails):
    user_file = os.path.join(os.getcwd(), 'UserProfiles', auth_ID, 'UserData.json')
    with open(user_file) as profile:
        user_json = json.load(profile)
        if dice != '':
            die = int(dice)
        else:
            die = 1
        if 'DiceLuck' not in user_json.keys():
            user_json['DiceLuck'] = {
                    "TotalRolls": die,
                    "Crits": int(crits),
                    "Fails": int(fails)
                    }
        else:
            user_json['DiceLuck']['TotalRolls'] = user_json['DiceLuck']['TotalRolls'] + die
            user_json['DiceLuck']['Crits'] = user_json['DiceLuck']['Crits'] + int(crits)
            user_json['DiceLuck']['Fails'] = user_json['DiceLuck']['Fails'] + int(fails)
    with open(user_file, 'w') as new_profile:
        json.dump(user_json, new_profile)

# Paying anything to roll the dice just one more itme.
def roll(die, num=1):
    results = {"total":0,"dieRolls":[]}
    crits = 0
    fails = 0
    for z in range(num):
        chuck = random.randint(1,die)
        results["total"] = results["total"] + chuck
        results["dieRolls"].append([chuck,die])
    if die == 20:
        for r in results['dieRolls']:
            if r[0] == 20:
                crits = crits + 1
            if r[0] == 1:
                fails = fails + 1
    return results, crits, fails


# Hello world!
async def greet(message, args):
    log("saying hi to " + str(message.author) + " in " + str(message.guild))
    await message.channel.send( "Hi, I'm HexBug!")

# no shame in asking for help.
async def list_commands(message, args):
    cmd_list = 'Available commands:\n'
    for cmd in command_library.keys():
        # only show non-admin commands
        if command_library[cmd][1] == False:
            cmd_list = cmd_list + '~{0} {1}\n'.format(cmd, command_library[cmd][2])
    await message.channel.send(cmd_list)

# A D2 roll that's not tracked. 
async def flip(message, args):
    await message.channel.send('flipping a coin...')
    log("Flipping a coin for {0} in {1}".format(str(message.author), str(message.guild)))
    flip, c, f = roll(2)
    time.sleep(1.2)
    if flip["total"] == 1:
        await message.channel.send('Heads!')
        log('Heads')
    else:
        await message.channel.send('Tails!')
        log('Tails')        

              
# Process the dice equation            
async def process_dice(message, args):
    positiveSum = ''
    negativeSum = ''
    total = 0
    #ability checks
    if args[-1][0:3].upper() in ["STR","DEX","CON","INT","WIS","CHA"] and args[-1].lower() != "intimidation":
        a_roll = ability_roll(message, args[-1][0:3].upper(), False)
        await message.channel.send(f"**{args[-1][0:3].upper()}** check: {a_roll[0]} {a_roll[1]}")
        return
    #skill checks
    if '-'.join(args[1:]) in sheets.get_skills(None):
        skill = '-'.join(args[1:])
        rl, c, f = roll(20)
        s_req = req.get(f"https://www.dnd5eapi.co/api/skills/{skill}")
        if s_req.status_code == 200:
            s_json = s_req.json()
            bonus = sheets.get_bonus(s_json["ability_score"]["name"], message)
            t_text = ''
            prof = sheets.get_proficiency(message, skill)
            total = rl['total'] + bonus + prof
            if bonus != 0 or prof != 0:
                t_text = f"({rl['total']}"
                if bonus > 0:
                    t_text = f"{t_text} +{bonus}"
                if bonus < 0:
                    t_text = f"{t_text} {bonus}"
                if prof > 0:
                    t_text = f"{t_text} `+{prof}`"
                t_text = f"{t_text})"
            update_user_Rolls(str(message.author)[-4:], 1, c, f)
            await message.channel.send(f"**{s_json['name'].replace('-', ' ')}** check: {total} {t_text} *{s_json['ability_score']['name']}*")
            return
        else:
            await message.channel.send(f"Failed to fetch ability score for {skill}")
            return
    #dice equations   
    equation = ''.join(args[1:]).lower()
    log("rolling {0} for {1} in {2}".format(equation,str(message.author),str(message.guild)))
    posRolls = []
    posNums = []
    negRolls = []
    negNums = []
    error = ''
    equation_parts = re.findall(r'(-?(?:\d*[dD](?:4|6|8|10|12|20|100)|\d+))', equation)
    if(re.match(r'^((-?[0-9])*[dD](4|6|8|10|12|20|100)\+?)(([+-][0-9]+)|([+-][0-9]*[dD](4|6|8|10|12|20|100)\+?))*$',equation)) and len(equation) <= 10:
        for eq in equation_parts:
            if 'd' in eq:
                die = eq.split('d')
                if re.match('-?[0-9]',die[0]):
                    if int(die[0]) > 20:
                        error = 'Too many dice'
                        break
                    rl, c, f = roll(int(die[1]),abs(int(die[0])))
                    update_user_Rolls(str(message.author)[-4:], die[0], c, f)
                    if('-' in eq):
                        total = total - rl["total"]
                    else:
                        total = total + rl["total"]

                else:
                    rl, c, f = roll(int(die[1]))
                    update_user_Rolls(str(message.author)[-4:], die[0], c, f)
                    total = total + rl["total"]
                for r in rl["dieRolls"]:
                    if('-' in eq):
                        negRolls.append(r)
                    else:
                        posRolls.append(r)
            elif (re.match('^-?[0-9]+$',eq)):
                total = total + int(eq)
                if('-' in eq):
                    negNums.append(eq.replace('-',''))
                else:
                    posNums.append(eq)
        for item in posRolls:
            positiveSum = positiveSum + 'D'+str(item[1]) +': '+ str(item[0]) + ' '
        for n in posNums:
            positiveSum = positiveSum + '+' + n + ' '
        for item in negRolls:
            negativeSum = negativeSum + 'D'+str(item[1]) +': '+ str(item[0]) + ' '
        for n in negNums:
            negativeSum = negativeSum + '+' + n + ' '
        if(negativeSum[0] == '+'):
            negativeSum = negativeSum[1:]

    else:
        if len(equation) > 10:
            error = 'Dice Equation too long'
        else:
            error = 'Invalid dice equation, please try again.'
    if len(error) > 0:
        await message.channel.send(error)
        log('{0} raised error: {1} in {2}'.format(str(message.author),error,str(message.guild)))
    else:
        negatives = '' if len(negativeSum) == 0 else '\n \\- ({0})'.format(negativeSum)
        await message.channel.send('your result is {0}\n{1}{2}'.format(total,positiveSum, negatives))
        log("Result: {0}".format(positiveSum))
        
        
# Access information from the user's character sheet to make an ability check roll. Defaults to no bonus if sheet not found.        
def ability_roll(message, stat, save):
    total = 0
    rl, c, f = roll(20)
    bonus = sheets.get_bonus(stat, message)
    t_text = ''
    prof = 0
    if save:
        prof = sheets.get_proficiency(message, stat)
        print(prof)
    total = rl['total'] + bonus + prof
    if bonus != 0 or prof != 0:
        t_text = f"({rl['total']}"
        if bonus > 0:
            t_text = f"{t_text} +{bonus}"
        if bonus < 0:
            t_text = f"{t_text} {bonus}"
        if prof > 0:
            t_text = f"{t_text} `+{prof}`"
        t_text = f"{t_text})"
    update_user_Rolls(str(message.author)[-4:], 1, c, f)
    return [total, t_text]

async def save_roll(message, args):
    if args[-1][0:3].upper() in ["STR","DEX","CON","INT","WIS","CHA"] and args[-1].lower() != "intimidation":
        a_roll = ability_roll(message, args[-1][0:3].upper(), True)
        await message.channel.send(f"**{args[-1][0:3].upper()}** save: {a_roll[0]} {a_roll[1]}")
        return
    
# Search for spell descriptions from an online API
async def spell_lookup(message, args):
    spell_index = 1
    if args[1].lower() in wizard_names:
        spell_index = 2
    spell_name = '-'.join(args[spell_index:])
    request = req.get("https://www.dnd5eapi.co/api/spells/{0}".format(spell_name.lower()))
    if request.status_code == 200:       
        spell_json = request.json()
        if spell_json['level'] == 0:
            level_school = '{0} Cantrip'.format(spell_json['school']['name'])
        else:
            level_school = 'Level {0} {1}'.format(spell_json['level'],spell_json['school']['name'])
        components = '/'.join(spell_json['components'])
        if 'material' in spell_json.keys():
            material = "({0})".format(spell_json['material'])
        else:
            material = ''     
        spell_content = "**{0}**\n*{1}*\n***Casting time*** {2}\n***Range*** {3}\n***Components*** {4} {5}\n***Duration*** {6}\n```\n".format(spell_json['name'],level_school,spell_json['casting_time'],spell_json['range'],components,material,spell_json['duration'])
        limitHit = False
        for d in spell_json['desc']:
            if len(spell_content + d) <= 1997:
                spell_content = "{0}{1}\n".format(spell_content,d)
            else:
                if limitHit == False:
                    await message.channel.send("{0}\n```".format(spell_content))
                    limitHit = True
                else:              
                    await message.channel.send("```\n{0}\n```".format(d))
        if not limitHit:
            await message.channel.send("{0}\n```".format(spell_content))
        log("{0} looked up {1} in {2}".format(message.author,spell_json['name'],message.guild)) 
    else:
        await message.channel.send("Arcane spell failure for {0}. Is that a homebrew spell?".format(spell_name.replace('-',' ')))
        if request.status_code == 500:
            log("Internal server error while calling https://www.dnd5eapi.co/api/spells/{0}").format(spell_name)
        log(f"Error fetching spell {spell_name.replace('-',' ')}: error {request.status_code}")
            

# Show the user's occurence rate of crit successes and crit fails
async def user_luck(message, args):
    file = get_user_file(message)
    if file is not None:
        with open(file) as profile:
            user_json = json.load(profile)
            if 'DiceLuck' not in user_json.keys():
                await message.channel.send("Sorry, you haven't got any posRolls on record yet.")
            else:
                rollData = [user_json['DiceLuck']['TotalposRolls'], user_json['DiceLuck']['Crits'], user_json['DiceLuck']['Fails']]
                rollData.append(round((user_json['DiceLuck']['Crits']/user_json['DiceLuck']['TotalposRolls'])*100, 2))
                rollData.append(round((user_json['DiceLuck']['Fails']/user_json['DiceLuck']['TotalposRolls'])*100, 2))
                await message.channel.send("On record, you've made {0} D20 posRolls.\n{1} of those were crit successes, {2} of those were crit fails.\n{3}% crit rate, {4}% crit fail rate.".format(rollData[0], rollData[1], rollData[2], rollData[3], rollData[4]))
            
    else:
        await message.channel.send("Profile missing - this is awkward.")
   
# Fetch condition information from an online API
async def get_condition(message, args):
    if len(args) < 2:
        request = req.get(f"https://www.dnd5eapi.co/api/conditions/")
        condition_json = request.json()
        reply = ', '.join([x['name'] for x in condition_json['results']])
        await message.channel.send(f"**Conditions**: {reply}")
    else:
        request = req.get(f"https://www.dnd5eapi.co/api/conditions/{args[1].lower()}")
        if (request.status_code != 200):
            await message.channel.send(f"Couldn't find that condition.")
        else:
            condition_json = request.json()
            reply = ""
            for d in condition_json["desc"]:
                reply = f"{reply}{d}\n"
            await message.channel.send(f"**{condition_json['name']}**\n{reply}")

# come up with a random invention: an x for a y
async def invent(message, args):
    log("generating ideas to share with " + str(message.author))
    request = req.get('http://itsthisforthat.com/api.php?json')
    if (request.status_code != 200):
        await message.channel.send('Ideas machine broke.')
        log(f"Fetching ideas failed: error {request.status_code}")
    else:
        await message.channel.send("What about {0} for {1}".format(request.json()["this"],request.json()['that']))

# Like a fortune cookie you know will be good.
async def affirmation(message, args):
    log("Fetching words of affirmation for " + str(message.author))
    request = req.get('https://www.affirmations.dev/')
    if (request.status_code != 200):
        await message.channel.send("Affirmation machine broke.")
        log(f"Fetching affirmations failed: error {request.status_code}")
    else:
        await message.channel.send(request.json()["affirmation"])



# Access character sheet commands
async def handle_sheet(message, args):
    h_json = usr.get_user_json(str(message.author)[-4:])
    # show sheet if no further args given
    if len(args) == 1:
        print(h_json)
        if 'Character_Sheets' in h_json.keys():
            s_sheet = h_json['Character_Sheets'][h_json['Selected_sheet']]
            await message.channel.send("***{0}***\nLevel {1} {2} {3}\n{4} ".format(s_sheet['Name'], s_sheet['Level'], s_sheet['Race'], s_sheet['Class'], ' '.join([f"__**{x}: {y}**__" if x in s_sheet["Saves"] else f"**{x}**: {y}" for x, y in s_sheet["Ability_Scores"].items()])))
            return
        else:
            await message.channel.send("You don't have any sheets. Create one with ~sheet create [name]")
            return
    if args[1] in sheets.sheet_map.keys():
        if not sheets.check_sheet(h_json) and args[1] != "create":
            return "You don't have any Character sheets"
        reply = await sheets.find_func(message, args)
        await message.channel.send(reply)
    else:
        await message.channel.send(f'Not a sheet command. try these: {", ".join(sheets.sheet_map.keys())}')


# ADMIN: look at how they massacred my boy.
async def kill_bot(message, args):
    log(str(message.author) + " initiated kill command \nShutting down...")
    await message.channel.send('Going offline')
    quit()


#ADMIN: show user count on current server
async def count_users(message, args):
    await message.channel.send('There are ' + str(message.guild.member_count) + ' users in this server')

# ADMIN: list all servers HexBug is connected to.
async def list_servers(message, args):
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
        key_word = command.replace(prefix,'').lower()
        authL = str(message.author)[:-5]
        authID = str(message.author)[-4:]
        
        #Check the command exists in the dictionary, and that the user is me if it's an admin command, then run it.
        if key_word in command_library.keys():
            if command_library[key_word][1] == True and str(message.author) not in get_admins():
                await message.channel.send("Access Denied: ~{0} command for executive users only".format(key_word))
            else:
                prof = usr.create_profile_if_none(authID, authL)
                if prof is not None:
                    log(prof)
                execute = globals()[command_library[key_word][0]]
                await execute(message, args)  
        else:
            await message.channel.send('Command {0} not found. Try running ~help'.format(key_word))
            
    else:
       pass


        
client.run(TOKEN)
