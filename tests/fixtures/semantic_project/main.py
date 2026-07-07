import os

from pkg.app import run
from pkg.sibling.worker import Worker


def main():
    worker = Worker()
    worker.run()
    return run()
