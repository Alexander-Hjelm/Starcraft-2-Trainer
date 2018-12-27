import sys
import os.path
from os import walk
import sc2reader

class SupplyNamePair():
    def __init__(self, supply, name):
        self.supply = supply
        self.name = name

class Replay():
    def __init__(self, replay_name, player_name, build_name, match_datetime, macro_score):
        self.replay_name = replay_name
        self.player_name = player_name
        self.build_name = build_name
        self.match_datetime = match_datetime
        self.macro_score = macro_score

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
    return Replay(replay_name, my_name, build_name, replay.end_time, macro_score)

# Main program

if(len(sys.argv) > 1 and sys.argv[1] == "-b"):
    if len(sys.argv) != 3:
        print("USAGE: python3 trainer.py -b <build order name>")
    else:
        build_name = sys.argv[2]
        open("info", "a+")
        content = None
        with open("info", "r") as f:
            content = f.readlines()
        build_found = False
        for i in range(0, len(content)):
            if(content[i].rstrip() == build_name):
                build_found = True
                break
        if build_found:
            print("ERROR: Build with that name was already found. Terminating...")
        else:
            if not os.path.exists("builds"):
                os.makedirs("builds")
            open("builds/" + build_name, "a+")
            with open("info", "a") as f:
                f.write(build_name + "\n")
            print("Build order created successfully")

# Set replay folder
if(len(sys.argv) > 1 and sys.argv[1] == "-r"):
    if len(sys.argv) != 3:
        print("USAGE: python3 trainer.py -r <path to SC2 replay folder>")
    else:
        replay_path = sys.argv[2]
        content = None
        if not os.path.exists(replay_path):
            print("ERROR: " + replay_path + " is not a valid directory. Terminating...")
        else:
            if replay_path[len(replay_path)-1] != "/":
                replay_path = replay_path + "/"
            with open("replay_path", "w+") as f:
                f.write(replay_path)
            print("Replay path successfully set up")

# Set player names
if(len(sys.argv) > 1 and sys.argv[1] == "-n"):
    if len(sys.argv) != 3:
        print("USAGE: python3 trainer.py -n <your SC2 player name>")
    else:
        name = sys.argv[2]
        with open("player_name", "w+") as f:
            f.write(name)
        print("Set player name successfully")

# Enumerate replays
if(len(sys.argv) > 1 and sys.argv[1] == "-e"):
    if len(sys.argv) != 3:
        print("USAGE: python3 trainer.py -e <build order name>")
    else:
        build_name = sys.argv[2]

        build_order_names = []
        with open("info", "r+") as f:
            build_order_names = f.readlines()

        if len(build_order_names) == 0:
            print("ERROR: no build orders found. Please specify a build order with \"python trainer.py -b\"")
            sys.exit()

        found = False
        for i in range(0, len(build_order_names)):
            if(build_order_names[i].rstrip() == build_name):
                found = True

        if not found:
            print("ERROR: No build with the name " + build_name + " was found. Terminating...")

        replays = []
        replay_strs = None

        open("enumerated_replays", "a+")

        with open("enumerated_replays", "r") as f:
            replay_strs = f.readlines()

        print(len(replay_strs))
        for i in range(0, len(replay_strs)):
            replay_strs[i] = replay_strs[i].split(":")
            replays.append(Replay(replay_strs[i][0], replay_strs[i][1],
            replay_strs[i][2], replay_strs[i][3], replay_strs[i][4]))

        replay_path = None
        open("replay_path", "a+")
        with open("replay_path", "r") as f:
            content = f.readlines()
            if len(content) == 0:
                print("ERROR: no replay directory found. Please specify the directory of your SC2 replay files with \"python trainer.py -r\"")
                sys.exit()
            else:
                replay_path = content[0]

        if not os.path.exists(replay_path):
            print("ERROR: " + replay_path + " is not a valid directory. Set this to a valid directory with \"python3 trainer -r\". Terminating...")
            sys.exit()

        player_name = None
        with open("player_name", "r+") as f:
            content = f.readlines()
            if len(content) == 0:
                print("ERROR: no player name specified. Please specify your SC2 user name with \"python trainer.py -n\"")
                sys.exit()
            else:
                player_name = content[0]

        for root, dirs, files in os.walk(replay_path):
            for i in range(0, len(files)):
                filename = files[i]
                print(filename)
                found = False
                for i in range(0, len(replays)):
                    if filename == replays[i].replay_name:
                        found = True
                if not found:
                    while True:    # input loop
                        n = input("Found new replay: " + filename + " . Would you like to add it to your statistics? (Y/N)")
                        if n == "y" or n == "Y":
                            replay = analyze_replay(replay_path + "/" + filename, player_name, build_name)
                            match_datetime_str = str(replay.match_datetime.year)
                            match_datetime_str += "." + str(replay.match_datetime.month)
                            match_datetime_str += "." + str(replay.match_datetime.day)
                            match_datetime_str += "." + str(replay.match_datetime.hour)
                            match_datetime_str += "." + str(replay.match_datetime.minute)
                            match_datetime_str += "." + str(replay.match_datetime.second)
                            with open("enumerated_replays", "a+") as f:
                                f.write(replay.replay_name + ":" + replay.player_name + ":" +  replay.build_name
                                + ":" + match_datetime_str + ":" + str(replay.macro_score) + "\n")
                            print("Final macro score was: " + str(replay.macro_score))
                            break
                        elif n == "n" or n == "N":
                            break
