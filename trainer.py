import sys
import sc2reader

def handle_camera_event(event, me):
    return 0

def handle_player_stats_event(event, me):
    player = event.player
    if player is not me:
        return 0
    minerals = event.minerals_current
    vespene = event.vespene_current
    #print("Handling PlayerStatsEvent...")
    if minerals + vespene > 500:
        return -10
    return 0

def handle_unit_born_event(event, me):
    player = event.unit_controller
    print("Unit born: " + event.unit.name)
    #print(event.unit.minerals)
    #print(event.unit.vespene)
    return 0

def handle_unit_done_event(event, me):
    print("Unit done: " + event.unit.name)
    return 0

def handle_unit_init_event(event, me):
    player = event.unit_controller
    print("Unit init: " + event.unit.name)
    return 0

def handle_upgrade_complete_event(event, me):
    return 0

replay = sc2reader.load_replay('MyReplay.SC2Replay', load_map=True)

macro_score = 10000;

print(replay.map_name)
print(replay.type)

my_name = "Groove"
me = None

# print all players
for i in range(0, len(replay.teams)):
    for j in range(0, len(replay.teams[i].players)):
            player = replay.teams[i].players[j]
            print(player)
            print(player.name)
            if player.name == my_name:
                me = player
                print("I am " + me.name)

if me is None:
    print("Failed to initialize me")
    sys.exit()

for i in range(0, len(replay.events)):
    event = replay.events[i]

    #print(event.name)
    #print(type(event))
    if type(event) is sc2reader.events.game.CameraEvent:
        macro_score += handle_camera_event(event, me)
    elif type(event) is sc2reader.events.tracker.PlayerStatsEvent:
        macro_score += handle_player_stats_event(event, me)
    elif type(event) is sc2reader.events.tracker.UnitBornEvent:
        macro_score += handle_unit_born_event(event, me)
    elif type(event) is sc2reader.events.tracker.UnitInitEvent:
        macro_score += handle_unit_init_event(event, me)
    elif type(event) is sc2reader.events.tracker.UnitDoneEvent:
        macro_score += handle_unit_done_event(event, me)
    elif type(event) is sc2reader.events.tracker.UpgradeCompleteEvent:
        macro_score += handle_upgrade_complete_event(event, me)
    #print()

print("final macro score: " + str(macro_score))
