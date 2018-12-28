import sc2reader

from data_structs import SupplyNamePair
from data_structs import ReplayData

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

def handle_unit_init_event(event, me, build_order_buildings):
    player = event.unit_controller
    if player is not me:
        return 0

    unit = event.unit
    supply = unit.supply
    if supply > 0:
        me.current_food_used += unit.supply
    me.current_minerals -= unit.minerals
    me.current_vespene -= unit.vespene

    build_order_score_diff = 0

    # TODO: Not perfect. Should remove the building from build_order_buildings when it is complete. Consider a temporary buildings_in_progress struct
    for i in range(0, len(build_order_buildings)):
        building = build_order_buildings[i]
        #print("CHECKING: '" + unit.name + "' against '" + building.name + "'")
        if unit.name == building.name:
            #print("BUILT: " + unit.name + " from build order")
            supply_diff = me.current_food_used - building.supply
            if supply_diff > 0:
                # Building was too early
                build_order_score_diff -= supply_diff * 100
                #print("TOO EARLY: " + unit.name)
            elif supply_diff < 0:
                # Building was too late
                build_order_score_diff -= -supply_diff * 100
                #print("TOO LATE: " + unit.name)
            build_order_buildings.remove(building)
            break

    # print("INIT UNIT: " + str(round(event.frame)) + " " + unit.name)

    return build_order_score_diff + food_and_resources_check(event, me)

def handle_upgrade_complete_event(event, me):
    return 0

def handle_data_command_event(event, me):
    #print("DATA_COMMAND_EVENT:" + event.ability_name)
    #print(event.ability.build_unit)
    return 0

def handle_basic_command_event(event, me, build_order_research):
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
        #print(event.name)
        pass

    # TODO can I extract the upgrade and its cost?
    # Upgrade order
    build_order_score_diff = 0

    for i in range(0, len(build_order_research)):
        research = build_order_research[i]
        #print("CHECKING: '" + event.ability_name + "' against '" + research.name + "'")
        if event.ability_name == research.name:
            #print("RESEARCHED: " + research.name + " from build order")
            supply_diff = me.current_food_used - research.supply
            if supply_diff > 0:
                # Building was too early
                build_order_score_diff -= supply_diff * 100
                #print("TOO EARLY: " + event.ability_name)
            elif supply_diff < 0:
                # Building was too late
                build_order_score_diff -= -supply_diff * 100
                #print("TOO LATE: " + event.ability_name)
            build_order_research.remove(research)
            break

    return build_order_score_diff + food_and_resources_check(event, me)

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

    return score_delta


def analyze_replay(replay_path, my_name, build_name):
    replay = sc2reader.load_replay(replay_path, load_map=True)

    macro_score = 100000.0;

    print(replay.map_name)
    print(replay.type)

    me = None

    content = None
    #Read build order file
    with open("build_order") as f:
        content = f.readlines()

    for i in range(0, len(content)):
        content[i] = content[i].rstrip().split(":")

    #Total build order time
    t_min = int(content[0][0])
    t_sec = int(content[0][1])
    game_fps = replay.game_fps

    build_order_buildings = []
    build_order_research = []

    for i in range(1, len(content)):
        if content[i][1] == "b":
            build_order_buildings.append(SupplyNamePair(int(content[i][0]), content[i][2]))
        if content[i][1] == "r":
            build_order_research.append(SupplyNamePair(int(content[i][0]), content[i][2]))

    # print all players
    for i in range(0, len(replay.teams)):
        for j in range(0, len(replay.teams[i].players)):
                player = replay.teams[i].players[j]
                print(player)
                #print(player.name)
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
            macro_score += handle_unit_init_event(event, me, build_order_buildings)
        elif type(event) is sc2reader.events.tracker.UnitDoneEvent:
            macro_score += handle_unit_done_event(event, me)
        elif type(event) is sc2reader.events.tracker.UpgradeCompleteEvent:
            macro_score += handle_upgrade_complete_event(event, me)
        elif type(event) is sc2reader.events.game.BasicCommandEvent:
            macro_score += handle_basic_command_event(event, me, build_order_research)
        elif type(event) is sc2reader.events.game.DataCommandEvent:
            macro_score += handle_data_command_event(event, me)
        elif type(event) is sc2reader.events.tracker.UnitDiedEvent:
            macro_score += handle_unit_died_event(event, me)

        #print(build_order_buildings[0].name)

        if len(build_order_buildings) == 0 and len(build_order_research) == 0:
            me.done = True

        if me.done:
            break

    # Subtract for every building and research left
    macro_score -= (len(build_order_buildings) + len(build_order_research)) * 1000

    # Time factor
    #print(me.last_checked_frame)
    #print(me.checked_seconds * 16)
    time_factor = me.checked_seconds * game_fps / me.last_checked_frame

    macro_score = max(round(macro_score) * time_factor, 0)

    #print(game_fps)
    replay_name = replay_path.split("/")[-1]
    return ReplayData(replay_name, my_name, build_name, replay.end_time, macro_score)
