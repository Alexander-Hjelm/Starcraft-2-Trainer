import sys
import sc2reader

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

    # Overlords gain supply when spawned
    supply = event.unit.supply
    if supply < 0:
        me.current_food_made += supply

    #print("Unit born: " + event.unit.name)
    return food_and_resources_check(event, me)

def handle_unit_done_event(event, me):
    #print("Unit done: " + event.unit.name)
    player = event.unit.owner
    if player is not me:
        return 0

    # Pylons and Depots gain supply when done
    supply = event.unit.supply
    if supply < 0:
        me.current_food_made += supply

    return food_and_resources_check(event, me)

def handle_unit_died_event(event, me):
    player = event.unit.owner
    if player is not me:
        return 0

    unit = event.unit
    supply = unit.supply

    if supply > 0:
        me.current_food_used -= supply

    return food_and_resources_check(event, me)

def handle_unit_init_event(event, me):
    player = event.unit_controller
    if player is not me:
        return 0


    unit = event.unit
    supply = unit.supply
    if supply > 0:
        me.current_food_used += unit.supply
    me.current_minerals -= unit.minerals
    me.current_vespene -= unit.vespene

    print("INIT UNIT: " + unit.name)

    return food_and_resources_check(event, me)

def handle_upgrade_complete_event(event, me):
    return 0

def handle_data_command_event(event, me):
    #print("DATA_COMMAND_EVENT:" + event.ability_name)
    #print(event.ability.build_unit)
    return 0

def handle_basic_command_event(event, me):
    if event.player is not me:
        return 0

    #print("BASIC_COMMAND_EVENT:" + event.ability_name)
    ability = event.ability
    if(ability.is_build):
        #print("BUILD UNIT: " + ability.build_unit.name)
        unit = ability.build_unit
        supply = unit.supply
        if supply > 0:
            me.current_food_used += unit.supply
        me.current_minerals -= unit.minerals
        me.current_vespene -= unit.vespene

    # TODO Handle Stop event (Unit cancelled event, restore resources) (Can I get the entity that was stopped?)
    if event.ability_name == "Stop":
        #print("STOP_EVENT")
        print(event.name)
    # TODO Handle Upgrade initiated here (can I extract the upgrade and its cost?)

    return food_and_resources_check(event, me)

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
        #print(str(frame) + " :: " + str(delta_frames) + " fr - " + str(score_delta) + " from capped supply")

    if minerals + vespene > 500:
        score_delta -= 1.6 * delta_frames
        #print(str(frame) + " :: " + str(delta_frames) + " fr - " + str(score_delta) + " from too many resources")

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
t_min = 15
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
    if type(event) is sc2reader.events.tracker.PlayerStatsEvent:
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
    elif type(event) is sc2reader.events.game.DataCommandEvent:
        macro_score += handle_data_command_event(event, me)
    elif type(event) is sc2reader.events.tracker.UnitDiedEvent:
        macro_score += handle_unit_died_event(event, me)
    #print()

    if me.done:
        break

macro_score = round(macro_score)

print("final macro score: " + str(macro_score))
