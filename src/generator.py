import logging
import yaml
from typing import Optional
import numpy as np
import pandas as pd

from src.tags import *

def get_random_num(lam:float=1.5) -> int:
    while True:
        n = np.random.poisson(lam=lam)
        if n:
            return n

def generate_data(path_to_config:str, seed:Optional[int]=None):
    
    with open(path_to_config, "r") as f:
        config = yaml.safe_load(f)

    if seed is not None:
        np.random.seed(seed)

    # Generate file dependancies matrix
    all_files = []
    for group in config["Files"]:
        files = config["Files"][str(group)]["FileNames"]
        all_files.extend(files)

    FileMatrix = np.zeros((len(all_files), len(all_files)), dtype=float)
    m = 0

    all_authors = config["Authors"]

    authors_by_name = []
    authors = []

    for group in config["Files"]:
        files = config["Files"][str(group)]["FileNames"]
        p = config["Files"][str(group)]["p"]
        assert p > 0, "p must be > 0"
        assert p < 1.0, "p must be < 1"
        q = 1 - p
        n = len(files)

        # file group dependancy matrix
        a = np.empty(len(all_files))
        a.fill(0.01)
        for file in files:
            a[all_files.index(file)] = 0.99

        FileMatrix[m:m+n, m:m+n] = np.round(np.random.dirichlet(a, n)[:, m:m+n], 4)
        m += n

        author = [str(np.random.choice(all_authors))]*len(files)
        authors_by_name.extend(author)

    for i in range(len(all_files)):
        # authors[i] = FileMatrix[i,i]
        FileMatrix[i,i] = .0
        authors.append(np.round(1 - FileMatrix[i,:].sum(), 4))
        assert round(FileMatrix[i,:].sum() + authors[-1], 4) == 1

    x = pd.DataFrame(FileMatrix, columns=all_files, index=all_files)
    x["AuthorName"] = authors_by_name
    x["AuthorProb"] = authors
    x.to_csv("./tmp/filematrix.csv")

    # Generate modules and module files

    all_mods = {}
    for i, module in enumerate(config["Modules"]):
        
        # select a number of files 
        mod_name = module[i]["id"]
        # N = np.random.poisson(lam=module[i]["lambda"])
        module_files = np.random.choice(all_files, size=module[i]["lambda"], replace=True)

        a = np.empty(module[i]["lambda"])
        a.fill(1.0)
        A = np.round(np.random.dirichlet(a), 4)
        all_mods.update({str(mod_name):{}})

        for file, p in zip(module_files, A):
            if not str(file) in all_mods[str(mod_name)]:
                all_mods[str(mod_name)].update({str(file):float(p)})
            else:
                all_mods[str(mod_name)].update({str(file):all_mods[str(mod_name)][str(file)] + float(p)})

    y = pd.DataFrame(all_mods).fillna(.0)
    y.to_csv("./tmp/modulesmatrix.csv")

    # generate issues:
    all_issues = {}
    for issue_id, n in zip(
        [f"{config["Issues"]["prefix"]}{i}" for i in range(config["Issues"]["number"])], 
        [get_random_num() for _ in range(config["Issues"]["number"])]
    ):
        modules = np.random.choice(list(all_mods.keys()), size=n, replace=False)
        a = np.empty(n)
        a.fill(1.0)
        while True:
            A = np.round(np.random.dirichlet(a), 4)
            if A.sum() == 1:
                break
        all_issues.update({str(issue_id):{k:v for k, v in zip(modules, A)}})

    z = pd.DataFrame(all_issues).fillna(.0)
    z.to_csv("./tmp/issuesmatrix.csv")

    return x, y, z


def generate_markov(fmatrix:pd.DataFrame, mmatrix:pd.DataFrame, imatrix:pd.DataFrame):

    markov = {}

    # add issue sequence
    issues_ids = imatrix.columns.tolist()    
    issues = []
    for issue_id in issues_ids:

        issue = Issue(issue_id)
        issue_modules = imatrix.index[imatrix.loc[:,issue_id] > 0].values.tolist()
        issue_modules_p = imatrix.loc[issue_modules, issue_id].values
        assert round(sum(issue_modules_p), 3) == 1, f"transitions for {str(issue)} do not sum to 1"
        
        for m, p in zip(issue_modules, issue_modules_p):
            issue.to = Module(m)
            issue.p = p

        issue.average_consecutive_commits = get_random_num(lam=6)
        issues.append(issue)

    # add modules
    modules_ids = mmatrix.columns.tolist()
    modules = []
    for module_id in modules_ids:

        module = Module(module_id)
        module_files = mmatrix.index[mmatrix.loc[:,module_id] > 0].values.tolist()
        module_files_p = imatrix.loc[issue_modules, issue_id].values.tolist()
        assert round(sum(module_files_p), 3) == 1, f"transitions for {str(module)} do not sum to 1"

        for f, p in zip(module_files, module_files_p):
            module.to = File(f)
            module.p = p

        modules.append(module)

    # add files
    files_ids = fmatrix.index.tolist()
    files = []
    for file_id in files_ids:

        file = File(file_id)
        file_files = fmatrix.index[fmatrix.loc[file_id,files_ids] > 0].values.tolist()
        file_files_p = fmatrix.loc[file_id, file_files].tolist()
        # assert round(sum(file_files_p), 4) == 1, f"transitions for {str(file)} do not sum to 1"
    
        for f, p in zip(file_files, file_files_p):
            file.to = File(f)
            file.p = p

        file.to = Author(fmatrix.loc[file_id, "AuthorName"])
        file.p = fmatrix.loc[file_id, "AuthorProb"]

        files.append(file)

    # add authors
    autors_ids = fmatrix.loc[:, "AuthorName"].unique().tolist()
    authors = []
    for author_id in autors_ids:

        author = Author(author_id)
        author.to = Commit()
        author.p = 1.

        authors.append(author)

    average_consecutive_commits = {str(i):float(i.average_consecutive_commits) for i in issues}
    issue_sequence = { 
        "average_consecutive_commits":average_consecutive_commits
    }
    
    a = np.empty(len(issues))
    a.fill(1.)
    issues_p = np.random.dirichlet(a)

    initial = [{"to":str(i), "p":float(p)} for i, p in zip(issues, issues_p)]
    matrix = {str(Initial(" ")):initial}

    for issue in issues:
        matrix.update({str(issue):[{"to":str(to), "p":float(p)} for to, p in zip(issue.to, issue.p)]})

    for file in files:
        matrix.update({str(file):[{"to":str(to), "p":float(p)} for to, p in zip(file.to, file.p)]})

    for module in modules:
        matrix.update({str(module):[{"to":str(to), "p":float(p)} for to, p in zip(module.to, module.p)]})

    for author in authors:
        matrix.update({str(author):[{"to":str(to), "p":float(p)} for to, p in zip(author.to, author.p)]})

    transitions = {"matrix":matrix}
    markov = {"issue_sequence":issue_sequence, "transitions":transitions}
    
    return markov