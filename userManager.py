import os, json


# Retrieve a user's UserData file path
def get_user_file(user_id):
    if os.path.exists(os.path.join(os.getcwd(), 'UserProfiles', user_id, 'UserData.json')):
        return os.path.join(os.getcwd(), 'UserProfiles', user_id, 'UserData.json')
    else:
        return None
    
    
def get_user_json(user_id):
    profile = get_user_file(user_id)
    if profile is not None:
        with open(profile) as p:
            return json.load(p)
    else:
        return None
    
def write_data(user_id, user_json):
    with open(get_user_file(user_id), 'w') as new_sheet:
        json.dump(user_json, new_sheet)