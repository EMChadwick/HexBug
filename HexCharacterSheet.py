import json, re
from discord.ext.commands import Bot
from discord.ext import commands
import requests as req
import userManager as usr

#Character sheet functions
sheet_map = {
        "create": "create_character_sheet",
        "set": "set_stat",
        "select": "select_sheet",
        "autoroll": "roll_stats",
        "skill": "choose_skill"
        }

async def find_func(message, args):
        execute = globals()[sheet_map[args[1]]]
        reply = await execute(message, args)
        return(reply)


async def create_character_sheet(message, args):
    if len(args) < 3:
        return('Please give a name - usage: ~sheet create Joe Bloggs')
    if len("".join(args)) > 34:
        return('Please give a name 20 characters or fewer in length.')
    u_json = usr.get_user_json(str(message.author)[-4:])
    if "Selected_sheet" not in u_json.keys():
        u_json["Selected_sheet"] = None
    if "Character_Sheets" not in u_json.keys():
        u_json["Character_Sheets"] = []
    if len(u_json["Character_Sheets"]) == 5:
        return('You already have 5 character sheets. Please delete one first')
    u_json["Character_Sheets"].append({   
                "Name": " ".join(args[2:]),
                "Class": None,
                "Race": None,
                "Background": None,
                "Level": 1,
                "Ability_Scores": {
                        "STR": 10,
                        "DEX": 10,
                        "CON": 10,
                        "INT": 10,
                        "WIS": 10,
                        "CHA": 10,
                        },
                "Skills": [],
                "Saves" : [],
                "Proficiency": 1,
                "Under_Construction": True,
                "Incomplete": ["Class","Skills", "Race", "Background"]
                })
    u_json["Selected_sheet"] = len(u_json["Character_Sheets"]) -1
    usr.write_data(str(message.author)[-4:], u_json)
    return(f"{' '.join(args[2:])} has been created. Please choose a class and race. manually set ability scores or roll for them")
    
def get_skills(s_class):
    if s_class is None:
        skill_rep = req.get("https://www.dnd5eapi.co/api/skills/")
        if skill_rep.status_code == 200:
            skill_json = skill_rep.json()
            return [x['index'] for x in skill_json['results']]
        else:
            return []


def get_bonus(stat, message):
    b_json = usr.get_user_json(str(message.author)[-4:])
    if "Character_Sheets" not in b_json.keys():
        return 0
    return int(b_json["Character_Sheets"][b_json["Selected_sheet"]]["Ability_Scores"][stat]/2)-5


def get_proficiency(message, attr):
    p_json = usr.get_user_json(str(message.author)[-4:])
    if p_json is not None:
        if "Proficiency" in p_json["Character_Sheets"][p_json["Selected_sheet"]].keys():
            if (attr[:3].upper() in p_json["Character_Sheets"][p_json["Selected_sheet"]]["Saves"] and attr != "intimidation") or (attr in p_json["Character_Sheets"][p_json["Selected_sheet"]]["Skills"]):

                return p_json["Character_Sheets"][p_json["Selected_sheet"]]["Proficiency"]
    return 0  


async def set_stat(message, args):
    u_profile = usr.get_user_json(str(message.author)[-4:])
    if args[2][0:3].upper() not in ["STR","DEX","CON","INT","WIS","CHA"]:
        return('Please select an ability score: STR, DEX, CON, INT, WIS, CHA')
    if len(args) < 4:
        return('Please specify the number')
    if not re.match('^([1-9]|1\d|20)$', args[3]):
        return('valid range is 1-20')
    u_profile["Character_Sheets"][u_profile["Selected_sheet"]]["Ability_Scores"][args[2][0:3].upper()] = int(args[3])
    usr.write_data(str(message.author)[-4:], u_profile)
    return(f'{args[2]} for {u_profile["Character_Sheets"][u_profile["Selected_sheet"]]["Name"]} is now {args[3]}')
  

async def choose_skill(message, args):   
    u_profile = usr.get_user_json(str(message.author)[-4:])
    choice = '-'.join(args[2:]).lower()
    if choice not in get_skills(None):
        return('please input a valid skill name')
    if choice in u_profile["Character_Sheets"][u_profile["Selected_sheet"]]["Skills"]:
        return (f'{u_profile["Character_Sheets"][u_profile["Selected_sheet"]]["Name"]} already has {choice}')
    u_profile["Character_Sheets"][u_profile["Selected_sheet"]]["Skills"].append(choice)
    usr.write_data(str(message.author)[-4:], u_profile)
    return(f"{choice} added to skills.")
    
    
    
async def select_sheet(message, args):
    s_profile = usr.get_user_json(str(message.author)[-4:])
    if len(args) == 2:
        return(list_sheets(s_profile))
    if len(args) != 3:
        return('Please specify a character sheet index')
    if re.match('^([1-5])$', args[2]):
        if int(args[2]) > len(s_profile["Character_Sheets"]) or int(args[2]) < 1:
            return("Index out of bounds. Please choose from your profiles:\n{0}".format(list_sheets(s_profile)))
        s_profile["Selected_sheet"] = int(args[2]) -1
        usr.write_data(str(message.author)[-4:], s_profile)
        return("Profile {0}: *{1}* selected".format(args[2], s_profile["Character_Sheets"][s_profile["Selected_sheet"]]["Name"]))
    else:
        return('Please specify a valid character sheet index')
    
         
def list_sheets(profile):
    sheet_list = ""
    for i, sheet in enumerate(profile["Character_Sheets"]):
        if i == profile["Selected_sheet"]:
            sheet_list = "{0}\n **{1}: {2}**".format(sheet_list, i+1, profile["Character_Sheets"][i]["Name"])
        else:
            sheet_list = "{0}\n {1}: {2}".format(sheet_list, i+1, profile["Character_Sheets"][i]["Name"])
    return(sheet_list)