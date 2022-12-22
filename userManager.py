import os, json


# Generate a profile for a user
def create_profile_if_none(auth_ID, auth_L):
    user_dir = os.path.join(os.getcwd(), 'UserProfiles', auth_ID)
    user_file = os.path.join(os.getcwd(), 'UserProfiles', auth_ID, 'UserData.json')
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    if not os.path.exists(user_file):
        try:
            with open('UserDataTemplate.json') as template:
                new_data = json.load(template)
                new_data['Username'] = auth_L
            with open(os.path.join(user_dir, 'UserData.json'), 'w') as new_profile:
                json.dump(new_data, new_profile)
            return 'New profile created for {0}#{1}'.format(auth_L, auth_ID)
        except Exception as e:
            return f'Error creating profile for {auth_L}: {e}'


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