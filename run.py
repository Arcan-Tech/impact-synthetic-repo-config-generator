import logging
import sys
import os
import yaml
from src.generator import *

path_to_config = "./configs/config.yaml"
path_to_markov = "./output/markov.yaml"

def main():

    # TODO: argparser

    if not os.path.isdir(os.path.join(os.getcwd(), "tmp")):
        os.mkdir(os.path.join(os.getcwd(), "tmp"))
    
    x, y, z = generate_data(path_to_config)
    assert ((x.iloc[:,:-2].sum(axis=1) + x.iloc[:,-1]) == 1).all, "files transitions do not sum up to 1!"

    markov = generate_markov(x, y, z)

    with open(path_to_markov, "w") as f:
        yaml.dump(markov, f, sort_keys=False)


if __name__=="__main__":
    main()