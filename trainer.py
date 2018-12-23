import sc2reader

def handle_camera_event(event):
    print("Handling CameraEvent...")

def handle_player_stats_event(event):
    print("Handling PlayerStatsEvent...")

def handle_unit_born_event(event):
    print("Handling UnitBornEvent...")
    print(event.unit.name)
    print(event.unit.minerals)
    print(event.unit.vespene)

replay = sc2reader.load_replay('MyReplay.SC2Replay', load_map=True)

print(replay.map_name)
print(replay.type)

# print all players
for i in range(0, len(replay.teams)):
    for j in range(0, len(replay.teams[i].players)):
            print(replay.teams[i].players[j])

for i in range(0, len(replay.events)):
    event = replay.events[i]

    print(event.name)
    print(type(event))
    if type(event) is sc2reader.events.game.CameraEvent:
        handle_camera_event(event)
    elif type(event) is sc2reader.events.tracker.PlayerStatsEvent:
        handle_player_stats_event(event)
    elif type(event) is sc2reader.events.tracker.UnitBornEvent:
        handle_unit_born_event(event)
    print()

