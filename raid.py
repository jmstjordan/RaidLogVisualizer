import json
import sys
import requests
import pandas as pd
import datetime
import os

API_KEY = os.environ['WOW_API_KEY']

def get_fights(code):
    url = 'https://www.warcraftlogs.com:443/v1/report/fights/{code}?api_key={API_KEY}'.format(code=code, API_KEY=API_KEY)
    res = requests.get(url)
    return json.loads(res.content)

def get_raid_events_by_player(player_id, end):
    start = 0
    url = 'https://www.warcraftlogs.com/v1/report/events/damage-done/{code}?start={start}&end={end}&sourceid={player_id}&api_key={API_KEY}'.format(code=code, start=start, end=end, player_id=player_id, API_KEY=API_KEY)
    res = requests.get(url)
    data = json.loads(res.content)
    # for debugging purposes, I write our data so we don't have to make 40 API calls again
    with open('playersdata/' + str(player_id) + '.json', 'w') as f:
        json.dump(data, f)
    return data

def get_raid_events_by_player_file(fi, end):
    with open('playersdata/'+str(fi) + '.json') as f:
        return json.load(f)

def get_raid_time_range(fights):
    return fights['start'], fights['fights'][len(fights['fights']) - 1]['end_time']

def get_partition(row, time_sections):
    return get_time_index(row.timestamp, time_sections)
    
def create_time_sections(end, num_sections):
    times = [0]
    for i in range(1, num_sections+1):
        times.append(times[i-1] + end // num_sections)
    return times

def build_friendly_times(friendlies, times):
    names = friendlies['name'].values.tolist()
    out_obj = []
    for time in times:
        for name in names:
            out_obj.append({"timestamp":time, "name": name})
    return pd.DataFrame(out_obj)

def get_running_amounts(raid_df, name, start):
    df=raid_df[raid_df.name == name]
    out_amounts = []
    category = df['type_2'].values.tolist()[0]
    amounts = df[['timestamp', 'amount']].values.tolist()
    out_amounts.append({"time": start + int(amounts[0][0]), "name": name, "value": int(amounts[0][1]), "category": category})
    for i in range(1, len(amounts)):
        amounts[i][1] = amounts[i-1][1] + amounts[i][1]
        out_amounts.append({"time": start + int(amounts[i][0]), "name": name, "value": int(amounts[i][1]), "category": category})
    return pd.DataFrame(out_amounts)

def get_raid_running_amounts(raid_df, friendlies, start):
    names = friendlies['name'].values.tolist()
    dfs = []
    for name in names:
        df = get_running_amounts(raid_df, name, start)
        dfs.append(df)
    return pd.concat(dfs)

def get_time_index(timestamp, times):
    for i in range(0, len(times)):
        if timestamp < times[i]:
            return times[i-1]

def get_raid_data_frame(friendlies, end):
    player_ids = friendlies['id'].tolist()
    dfs = []
    for player_id in player_ids:
        data = get_raid_events_by_player(player_id, end)
        dfs.append(pd.DataFrame(data['events']))
    return pd.concat(dfs)

code = sys.argv[1]
fights = get_fights(code)

# Get character object
friendlies = pd.DataFrame(fights['friendlies'])

# Get start timestamp of raid and end ms to add to the raid
start, end = get_raid_time_range(fights)

# Merge all the character events into one df
raid_df = get_raid_data_frame(friendlies, end)

# join it back to friendlies to get class
friendly_raid_df = raid_df.merge(friendlies, left_on='sourceID', right_on='id', how='inner', suffixes=('_1', '_2'))

# filter out unneeded columns
df1 = friendly_raid_df[['timestamp','name','amount','type_2']]

# sort the values by time
df1.sort_values(by=['timestamp'], inplace=True)

# get 12 evenly distributed timestamps so our race times are consistent
times = create_time_sections(end, 12)
df1['timestamp'] = df1.apply(lambda row: get_partition(row, times), axis=1)

# squash amounts for each section
squashed = df1.groupby(['timestamp', 'name', 'type_2'])['amount'].sum().to_frame('amount').reset_index()

# add non existing players on each section
friendly_df = build_friendly_times(friendlies, times)

# join it back to get a player for each section
all_players = friendly_df.merge(squashed, on=['name', 'timestamp'], how='left', suffixes=('_1', '_2')).fillna(0)

# append rolling values for each player
final_df = get_raid_running_amounts(all_players, friendlies, start)

# back join to get the missing classes because players who didn't deal damage get lost
back_merged = final_df.merge(friendlies, on='name', how='inner')
filtered = back_merged[['time', 'name', 'value', 'type']]
filtered.columns = ['time','name','value','category']

# finally we write out the csv
filtered.to_csv('raid.csv', index=False)

