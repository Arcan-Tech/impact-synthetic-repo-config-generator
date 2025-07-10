import logging
import argparse
import os
from pathlib import Path
import yaml
from src.generator import *

TMP_DIR = "tmp"
PATH_TO_CONFIG = "./configs/config.yaml"
PATH_TO_MARKOV = "./output/markov.yaml"
SEED = 42

def main(args):

    if not os.path.isdir(Path(args.tmp)):
        os.mkdir(Path(args.tmp))
    
    path_to_output = Path(args.output)
    out_dir = path_to_output.parent
    if not os.path.isdir(out_dir):
        os.mkdirs(out_dir)

    markov_config = generate_markov(Path(args.input), seed=args.seed)

    with open(path_to_output, 'w') as f:
        f.write(yaml.dump(markov_config, sort_keys=False).replace("'", ""))

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Impact synthetic repo-generator config generator.")
    parser.add_argument("-i", "--input", type=str, help=f"path to input configuration yaml file. Default {PATH_TO_CONFIG}", default=PATH_TO_CONFIG)
    parser.add_argument("-o", "--output", type=str, help=f"path to output generator config file. Default {PATH_TO_MARKOV}", default=PATH_TO_MARKOV)
    parser.add_argument("--tmp", type=str, help=f"path to tmp directory. Default {TMP_DIR}", default=TMP_DIR)
    parser.add_argument("--seed", type=int, help="seed", default=None)
    
    main(parser.parse_args())