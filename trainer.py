import sys
import sc2reader

def handle_camera_event(event, me):
    return 0

def handle_player_stats_event(event, me):
    player = event.player
    if player is not me:
        return 0

    me.current_food_used = event.food_used
    me.current_food_made = event.food_made
    me.current_minerals = event.minerals_current
    me.current_vespene = event.vespene_current

    score_delta = food_and_resources_check(event, me)

    return score_delta

def handle_unit_born_event(event, me):
    player = event.unit_controller
    if player is not me:
        return 0

    supply = event.unit.supply
    if supply > 0:
        me.current_food_used += supply
    elif supply < 0:
        me.current_food_made += supply

    print("Unit born: " + event.unit.name)
    return food_and_resources_check(event, me)

def handle_unit_done_event(event, me):
    print("Unit done: " + event.unit.name)
    return 0

def handle_unit_init_event(event, me):
    player = event.unit_controller
    if player is not me:
        return 0

# TODO: Not perfect. Depots add their supply on InitEvent
    supply = event.unit.supply
    if supply > 0:
        me.current_food_used += supply
    elif supply < 0:
        me.current_food_made += supply

    print("Unit init: " + event.unit.name)
    return 0

def handle_upgrade_complete_event(event, me):
    return 0

def handle_basic_command_event(event, me):
    print("BASIC_COMMAND_EVENT:" + event.ability_name)
    ability = event.ability


    return 0

# TODO Create building, "build event"
# TODO Unit cancelled event, restore resources
# TODO Target frames, when should event be done? If target frame is met in a handler, set a property on the player and return from the program
# TODO Handle Upgrade initiated (Train XYZ?)
# TODO Unit destroyed event, restore supply

def food_and_resources_check(event, me):
    frame = event.frame
    delta_frames = frame - me.last_checked_frame

    food_used = me.current_food_used
    food_made = me.current_food_made
    minerals = me.current_minerals
    vespene = me.current_vespene

    score_delta = 0

    if food_used >= food_made:
        score_delta -= 1.6 * delta_frames

    #print("Handling PlayerStatsEvent...")
    if minerals + vespene > 500:
        score_delta -= 1.6 * delta_frames

    me.last_checked_frame = frame
    if frame >= me.checked_seconds * 16:
        me.done = True

    return score_delta

replay = sc2reader.load_replay('MyReplay.SC2Replay', load_map=True)

macro_score = 10000.0;

print(replay.map_name)
print(replay.type)

my_name = "Groove"
me = None
t_min = 5
t_sec = 0

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

me.checked_seconds = t_min * 60 + t_sec
me.done = False

me.current_food_used = 0
me.current_food_made = 0
me.current_minerals = 0
me.current_vespene = 0
me.last_checked_frame = 0

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
    elif type(event) is sc2reader.events.game.BasicCommandEvent:
        macro_score += handle_basic_command_event(event, me)
    #print()

    if me.done:
        break

print("final macro score: " + str(macro_score))
