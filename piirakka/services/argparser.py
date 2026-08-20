import argparse

parser = argparse.ArgumentParser(
    prog="piirakka",
    description="Web radio playback for social spaces",   
)

parser.add_argument("--no-mpv", action="store_true", help="Do not start an MPV subprocess")
