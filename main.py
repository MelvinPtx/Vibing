"""Point d'entrée : python main.py [--training]"""
import sys

from src.game import Game

if __name__ == "__main__":
    Game(training="--training" in sys.argv).run()
