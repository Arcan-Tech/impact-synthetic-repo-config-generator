# impact-synthetic-repo-config-generator
Generator of yaml configuration files for impact-repo-generator. This script is configurable and it allows to quickly generate synthetic repositories with file groups and modules. It also generates randomly a given number of issues targeting randomly chosen modules.

## File matrix
Each row of the file matrix represents the dependancy link between a file and each other as the possible transitions in the markov model with their probability.
A row also has two added columns representing the transitions from file to author at each step of the chain. The probability values in each row sum to 1. 
Once generated the file matrix can be accessed from `./tmp/filematrix.csv`

## Modules matrix
Each row of the modules matrix represents the probability that a file is impacted as part of a logical dependency of a module. Modules represent features and/or functions that are directly targeted by issues. Each column of the module matrix sums to 1.
Once generated the modules matrix can be accessed from `./tmp/modulesmatrix.csv`

## Issues matrix
Each row of the issues matrix represents the probability of a module of being targeted by an issue. Each column (modules targeted by an issue) sums to 1.
Once generated the issues matrix can be accessed from `./tmp/issuesmatrix.csv`

## Markov configuration file
The output of the script is a semi-random generated model file that assures that files are dependent only inside their **FileGroup** and as part of a **Module** while the probability of any other impact is set to 0. This script also assures that the transition probabilities for each node sum up to 1.

For any other info about the markov.yaml output file and its structure see Arcan-Tech/impact-repo-generator.

# Usage
Install dependancies

```sh
pip install -r requirements.txt
```

modify the `config.yaml` file found in `./configs`

```yaml
Files:          # Files configures the generation of the file matrix
  FileGroup0:   # a file froup represents a set of interdependent files
    FileNames:
      - file0   # each file is identified by a filename
      - file1
      - file2
      - file3
      - file4
      - file5
    p: 0.9      # total sum of probability is the total sum of the probabilities of each file for each other file of the group. 
  FileGroup1:
    FileNames:
      - file6
      - file7
      - file8
      - file9
    p: 0.9

Modules:        # list of modules. Modules represents logical dependancies between files
  - 0:
      id: Module0   # each module is identified by a unique id
      lambda: 4     # the lambda parameter defines the number of files that are randomly assigned to the module 
  - 1:
      id: Module1
      lambda: 3

Authors:
  - Author1         # authors are assigned based on groups and the probability of the transition is defined ad 1 - p
  - Author2

Issues:             # issues are identified by numbered ids. To each issue a certain number of modules are assigned randomly.
  prefix: "issue"   # prefix of the id  "issue{number}".
  number: 10        # the number of issue to be generated.

```
Run the script

```sh
python3 run.py
```