import datetime
import matplotlib.pyplot
import numpy
import os.path
import sys
from os import walk

import analytics
from data_structs import ReplayData
from data_structs import ScoreTimePair

# Discover all replays in the replay folder. If they have not been added before,
# add them to the player's statistics for the chosen build order
def get_replays_for_build(build_name):

    # Check if build order name exists

    build_order_names = []
    with open("info", "r+") as f:
        build_order_names = f.readlines()

    if len(build_order_names) == 0:
        print("ERROR: no build orders found. Please specify a build order with \"python sc2trainer.py -b\"")
        sys.exit()

    found = False
    for i in range(0, len(build_order_names)):
        if(build_order_names[i].rstrip() == build_name):
            found = True

    if not found:
        print("ERROR: No build with the name " + build_name + " was found. Terminating...")

    replays = []
    replay_strs = None

    # Read replay data

    open("enumerated_replays", "a+")

    with open("enumerated_replays", "r") as f:
        replay_strs = f.readlines()

    for i in range(0, len(replay_strs)):
        replay_strs[i] = replay_strs[i].split(":")
        replays.append(ReplayData(replay_strs[i][0], replay_strs[i][1],
        replay_strs[i][2], replay_strs[i][3], replay_strs[i][4]))

    return replays

# Read the user's SC2 player name from file
def get_player_name():
    with open("player_name", "r+") as f:
        content = f.readlines()
        if len(content) == 0:
            print("ERROR: no player name specified. Please specify your SC2 user name with \"python sc2trainer.py -n\"")
            sys.exit()
        else:
            player_name = content[0]


### Main program ###

# Set build order name
# First argument: <string>: build order name
if(len(sys.argv) > 1 and sys.argv[1] == "-b"):
    if len(sys.argv) != 3:
        print("USAGE: python3 sc2trainer.py -b <build order name>")
    else:
        # Open info file
        build_name = sys.argv[2]
        open("info", "a+")
        content = None
        with open("info", "r") as f:
            content = f.readlines()
        # Check if the name already exists
        build_found = False
        for i in range(0, len(content)):
            if(content[i].rstrip() == build_name):
                build_found = True
                break
        if build_found:
            print("ERROR: Build with that name was already found. Terminating...")
        else:
            # Write build order name to info file and a separate file for editing
            if not os.path.exists("builds"):
                os.makedirs("builds")
            open("builds/" + build_name, "a+")
            with open("info", "a") as f:
                f.write(build_name + "\n")
            print("Build order created successfully")

# Set replay folder
# First argument: <string>: directory with SC2 replay files
if(len(sys.argv) > 1 and sys.argv[1] == "-r"):
    if len(sys.argv) != 3:
        print("USAGE: python3 sc2trainer.py -r <path to SC2 replay folder>")
    else:
        replay_path = sys.argv[2]
        content = None
        if not os.path.exists(replay_path):
            print("ERROR: " + replay_path + " is not a valid directory. Terminating...")
        else:
            # Append trailing slash (/)
            if replay_path[len(replay_path)-1] != "/":
                replay_path = replay_path + "/"
            # Write the replay directory to file
            with open("replay_path", "w+") as f:
                f.write(replay_path)
            print("Replay path successfully set up")

# Set the user's SC2 player/profile name
# First argument: <string>: profile name
if(len(sys.argv) > 1 and sys.argv[1] == "-n"):
    if len(sys.argv) != 3:
        print("USAGE: python3 sc2trainer.py -n <your SC2 player name>")
    else:
        name = sys.argv[2]
        # Write name to file
        with open("player_name", "w+") as f:
            f.write(name)
        print("Set player name successfully")

# Analyze a single replay file. Print a score and a match report,
# but do not add any data to the player's statistics
# First argument: <string>: replay file name (full path)
# First argument: <string>: build order name
if(len(sys.argv) > 1 and sys.argv[1] == "-a"):
    if len(sys.argv) != 4:
        print("USAGE: python3 sc2trainer.py -a <replay file> <build order name>")
    else:
        file_name = sys.argv[2]
        build_name = sys.argv[3]

        # Get player name
        player_name = None
        with open("player_name", "r+") as f:
            content = f.readlines()
            if len(content) == 0:
                print("ERROR: no player name specified. Please specify your SC2 user name with \"python sc2trainer.py -n\"")
                sys.exit()
            else:
                player_name = content[0]

        # Analyze the replay file
        replay = analytics.analyze_replay(file_name, player_name, build_name)

        # Output score
        print("Final macro score was: " + str(replay.macro_score))

# Enumerate all replays in the replays directory. If a replay has not been
# previously enumerated, analyze it and add the resulting data to the player's
# statistics
# First argument: <string>: build order name
if(len(sys.argv) > 1 and sys.argv[1] == "-e"):
    if len(sys.argv) != 3:
        print("USAGE: python3 sc2trainer.py -e <build order name>")
    else:
        build_name = sys.argv[2]

        # Load previous replay data where this build order was followed
        replays = get_replays_for_build(build_name)

        # Read the path of the replay folder from file
        replay_path = None
        open("replay_path", "a+")
        with open("replay_path", "r") as f:
            content = f.readlines()
            if len(content) == 0:
                print("ERROR: no replay directory found. Please specify the directory of your SC2 replay files with \"python sc2trainer.py -r\"")
                sys.exit()
            else:
                replay_path = content[0]

        if not os.path.exists(replay_path):
            print("ERROR: " + replay_path + " is not a valid directory. Set this to a valid directory with \"python3 trainer -r\". Terminating...")
            sys.exit()

        # Get player name
        player_name = get_player_name()

        # Load new replays from the replay folder
        for root, dirs, files in os.walk(replay_path):
            for i in range(0, len(files)):
                filename = files[i]
                print(filename)
                found = False
                for i in range(0, len(replays)):
                    if filename == replays[i].replay_name:
                        found = True
                if not found:
                    # For each new replay, ask the user to either analyze or skip it
                    while True:
                        n = input("Found new replay: " + filename + " . Would you like to add it to your statistics? (Y/N)")
                        if n == "y" or n == "Y":
                            replay = analytics.analyze_replay(replay_path + "/" + filename, player_name, build_name)
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

# Plot progress, score vs time.
# First argument: <string>: build order name
if(len(sys.argv) > 1 and sys.argv[1] == "-p"):
    if len(sys.argv) != 3:
        print("USAGE: python3 sc2trainer.py -p <build order name>")
    else:
        build_name = sys.argv[2]
        player_name = get_player_name()
        replays = get_replays_for_build(build_name)

        scores_date_pairs = []

        for i in range(0, len(replays)):
            replay = replays[i]
            if replay.player_name != player_name or replay.build_name != build_name:
                dt_strs = replays[i].match_datetime.split(".")
                dt = datetime.datetime(int(dt_strs[0]), int(dt_strs[1]), int(dt_strs[2]), int(dt_strs[3]), int(dt_strs[4]), int(dt_strs[5]))

                print(replays[i].macro_score)

                scores_date_pairs.append(ScoreTimePair(int(round(float(replays[i].macro_score))), dt))

        scores_date_pairs.sort(key=lambda x: x.time, reverse=True)

        datetimes = []
        scores = []

        for i in range(0, len(scores_date_pairs)):
            datetimes.append(scores_date_pairs[i].time)
            scores.append(scores_date_pairs[i].score)

        dates = matplotlib.dates.date2num(datetimes)

        matplotlib.pyplot.gcf().autofmt_xdate()
        matplotlib.pyplot.plot_date(dates, scores, linestyle='dashed')
        matplotlib.pyplot.show()

# Help section
if(len(sys.argv) == 1 or (len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"))):
    print("Usage: python3 sc2trainer.py <options>"
    + "\n"
    + "\nIMPORTANT: before discovering and analyzing replays, run the following sequence to set up your SC2 player name, replay directory and a name for your build order."
    + "\n python3 sc2trainer.py -n <your SC2 profile name>"
    + "\n python3 sc2trainer.py -b <your build order name>"
    + "\n python3 sc2trainer.py -r <path to SC2 replay folder>"
    + "\n"
    + "\nAllowed options:"
    + "\n -e <build order name>\t\t\tDiscover all new replays in the replay folder and add them to your statistics."
    + "\n -p <build order name>\t\t\tPlot your progress with the selected build order."
    + "\n -a <replay file> <build order name>\tAnalyze a single replay file. Generates a score and a match report, but does not add anything to your statistics."
    + "\n"
    + "\n -n <string>\t\t\t\tSet your SC2 profile name. Do not include you clan tag or bnet tag."
    + "\n -r <string>\t\t\t\tSet the path to your replay folder. On windows, this is usually something like C:\Documents\StarCraft II\Accounts\[number]\[other]\Replays"
    + "\n -b <string>\t\t\t\tSet the name of your build order. This will generate a file in the ./builds folder which you can edit."
    )
