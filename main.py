"""Point d'entrée : python main.py [--training] [--room N]   (--room 5 : directement au 1er boss)"""
import sys

from src.game import Game

if __name__ == "__main__":
    room = int(sys.argv[sys.argv.index("--room") + 1]) if "--room" in sys.argv else 1
    Game(training="--training" in sys.argv, room=room).run()
