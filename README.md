# impact-synthetic-repo-config-generator
Generator of yaml configuration files for impact-repo-generator. This script is configurable and it allows to quickly generate synthetic projects comprised of 1 or more repositories with file groups and modules. It also generates randomly a given number of issues targeting randomly chosen modules.

## File matrix
Each row of the file matrix represents the dependancy link between a file and each other as the possible transitions in the markov model with their probability.
Data about the transitions from file to author at each step of the chain are saved in the file-authors matrix. The probability values in each row sum to 1. 
Once generated the file matrix can be accessed from `./tmp/filematrix_<repo-ID>.csv`, the author-file link can be accessed from `./tmp/fileauthors_<repo-ID>.csv`.

## Modules matrix
Each row of the modules matrix represents the probability that a file is impacted as part of a logical dependency of a module. Modules represent features and/or functions that are directly targeted by issues. Each column of the module matrix sums to 1.
Once generated the modules matrix can be accessed from `./tmp/modulesmatrix_<repo-ID>.csv`

## Issues matrix
Each row of the issues matrix represents the probability of a module of being targeted by an issue. Each column (modules targeted by an issue) sums to 1.
Once generated the issues matrix can be accessed from `./tmp/issuesmatrix_<repo-ID>.csv`

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
Files:                    # Files configures the generation of the file matrix
  prefix: File            # Prefix of the file name e.g. File_23
  number: 6000            # Number of files to be generated
  filegroups:             # a file froup represents a set of interdependent files
    number: 500           # number of file groups to be randomly created
    lenght: 5             # average number of files in a file group
    random: true          # number of files selected at random, if "false" the program selects exactly "lenght" files
    p: 0.97               # average sum probability of all files transitions between files in a group

Modules:                  # list of modules. Modules represents logical dependancies between files
  prefix: Module          # Prefix of the module name e.g. Module_2
  number: 200             # total amount of modules to configure
  lambda: 50              # lambda parameter for number of files
  random: true            # number of files selected at random, if "false" the program selects exactly "lambda" files

Authors:                  # authors are assigned based on groups and the probability of the transition is defined ad 1 - p
  prefix: Author          # author id prefix e.g. Author_1
  number: 10              # number of authors
  contribution: random    # weight of author contribution is generated at "random", if "equal" probability of each author to be selected is equal

Issues:                   # issues are identified by numbered ids. To each issue a certain number of modules are assigned randomly.
  prefix: issue           # prefix of the issue id  "issue_42".
  number: 500             # the number of issue to be generated.
  n_modules: 2            # average number of modules touched by an issue
  lambda: 5               # lambda parameter for the number of consecutive commits in an isue.
  random: true            # number of modules and consecutive commits selected at random, if "false" the program selects exactly "n_modules"/"lambda" modules/commits
```
Run the script

```sh
python3 run.py - -i </path/to/config/file> -o </path/to/output/dir> -s <number-of-repositories>
```