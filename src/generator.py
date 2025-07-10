import logging
import yaml
from typing import Optional, Annotated, Tuple
import numpy as np
import pandas as pd

from src.tags import *

GENERATOR_ROUND = 9
OUTPUT_ROUNDING = 6

def get_random_num(lam:float=1.5) -> int:
    """
    returns a random integer != 0
    """
    while True:
        n = np.random.poisson(lam=lam)
        if n:
            return n


def check_probability(x:np.array) -> bool:
    return np.round(np.sum(x), OUTPUT_ROUNDING) == 1.0


def generate_files(n_files:int, prefix:str, groups:dict) -> dict:
    """
    Generates a list of files on arbitrary lenght and assign a given numer of them
    """

    c = n_files
    filelist = []
    
    while c > 0:
        c -= 1
        filelist.append(f"{prefix}_{c}")
        

    assert len(filelist), "at least one file is needed."

    filegroups = {}
    
    for i in range(groups["number"]):
        if groups["random"]:
            n = get_random_num(lam=groups["lenght"])
            p = np.random.normal(loc=groups["p"], scale=0.01)
        else:
            n = groups["lenght"]
            p = groups["p"]

        group_files = []
        for j in range(n):
            idx = filelist.index(np.random.choice(filelist))
            group_files.append(filelist.pop(idx))
            if not len(filelist):
                break
    
        filegroups.update({f"FileGroup{i}":{"FileNames":group_files, "p":p}})
        if not len(filelist):
            break

    filegroups.update({"Ungrouped":{"FileNames":filelist, "p":.0}})

    return filegroups


def generate_modules(n_mods:int, prefix:str, lam:float, rand:bool) -> list:
    """
    Generates a list of modules of arbitrary lenght. If rand=True randomly generate
    a value of lambda, else use the given one.
    """
    modules = []
    for i in range(n_mods):
        if rand:
            n = get_random_num(lam=lam)
        else:
            n = n_mods
        modules.append({"id":f"{prefix}_{i}", "lambda":n})
        
    return modules


def generate_authors(n_authors:int, prefix:str, contribution:str) -> list:
    """
    Generates a list of authors of arbitrary lenght.
    """
    authors = []
    if contribution == "equal":
        p = [1 / n_authors] * n_authors
    elif contribution == "random":
        p = list(np.random.dirichlet([1.] * n_authors, 1).reshape(-1,))
    
    assert check_probability(p) == 1.0

    for i in range(n_authors):
        authors.append({"name":f"{prefix}_{i}", "p":p[i]})
        
    return authors


def parse_config(path_to_config:str) -> Tuple[
    Annotated[dict, "config"], 
    Annotated[dict, "files"],
    Annotated[list, "modules"],
    Annotated[dict, "authors"],
]:
    """
    Parses configuration file and returns configuration file content and 
    """
    
    with open(path_to_config, "r") as f:
        config = yaml.safe_load(f)

    files = generate_files(
        config["Files"]["number"],
        config["Files"]["prefix"],
        config["Files"]["filegroups"],
    )

    modules = generate_modules(
        config["Modules"]["number"],
        config["Modules"]["prefix"],
        config["Modules"]["lambda"],
        config["Modules"]["random"]
    )

    authors = generate_authors(
        config["Authors"]["number"],
        config["Authors"]["prefix"],
        config["Authors"]["contribution"],
    )

    return config, files, modules, authors


def generate_file_matrix(files:dict, authors:list) -> Tuple[
    Annotated[pd.DataFrame, "filematrix"],
    Annotated[pd.DataFrame, "fileauthors"],
    Annotated[list, "all_files"]
]:
    """
    Generate file dependancies matrix and author transitions for each file
    """
    all_files = []
    m = 0
    for group in files:
        all_files.extend(files[str(group)]["FileNames"])

    n_files = len(all_files)

    FileMatrix = np.zeros((n_files, n_files), dtype=float)

    all_authors = [author["name"] for author in authors]
    authors_sampling_p = [author["p"] for author in authors]
    authors_by_name = []
    authors_transition = []

    for group in files:
        group_files = files[str(group)]["FileNames"]
        p = files[str(group)]["p"]
        n = len(group_files)
        if group != "Ungrouped":
            assert p > .0, "p must be > 0"
            assert p < 1., "p must be < 1"
            q = 1 - p
            # file group dependancy matrix
            a = np.empty(n_files)
            a.fill(0.001)
            for file in group_files:
                a[all_files.index(file)] = p
            FileMatrix[m:m+n, m:m+n] = np.random.dirichlet(a, n)[:, m:m+n]      # modified from FileMatrix[m:m+n, m:m+n] = np.round(np.random.dirichlet(a, n)[:, m:m+n], 4)
            m += n

            authors_by_name.extend([str(np.random.choice(all_authors, p=authors_sampling_p))]*n)
        else:
            authors_by_name.extend([str(np.random.choice(all_authors, p=authors_sampling_p)) for _ in range(n)])

    for i in range(n_files):
        authors_transition.append(1 - FileMatrix[i,:].sum())                    # generate the 
        assert authors_transition[-1] > 0
        assert np.round(FileMatrix[i,:].sum() + authors_transition[-1], OUTPUT_ROUNDING) == 1 # the sum of all the transition probabilities must sum up to 1
    
    filematrix = pd.DataFrame(FileMatrix, columns=all_files, index=all_files)
    fileauthors = pd.DataFrame(
        {
            "AuthorName": authors_by_name,
            "AuthorProb": authors_transition
        },
        index=all_files
    )
    filematrix.to_csv("./tmp/filematrix.csv")
    fileauthors.to_csv("./tmp/fileauthors.csv")

    return filematrix, fileauthors, all_files


def generate_module_matrix(modules:dict, all_files:list) -> Tuple[
    Annotated[pd.DataFrame, "modulematrix"],
    Annotated[list, "all_modules"]
]:
    """
    Generate modules dependancies matrix.
    """
    all_mods = {}
    for module in modules:
        # select a number of files 
        mod_name = module["id"]
        module_files = np.random.choice(all_files, size=module["lambda"], replace=True)

        a = np.empty(module["lambda"])
        a.fill(1.)
        A = np.random.dirichlet(a)
        all_mods.update({str(mod_name):{}})

        for file, p in zip(module_files, A):
            if not str(file) in all_mods[str(mod_name)]:
                all_mods[str(mod_name)].update({str(file):float(p)})
            else:
                all_mods[str(mod_name)].update({str(file):all_mods[str(mod_name)][str(file)] + float(p)})
    modulematrix = pd.DataFrame(all_mods).fillna(.0)
    modulematrix.to_csv("./tmp/modulematrix.csv")

    return modulematrix, list(all_mods.keys())


def generate_issue_matrix(config:dict, all_modules:list) -> Annotated[pd.DataFrame, "issuematrix"]:
    """
    Generate issues impact matrix.
    """
    all_issues = {}
    for i in range(config["number"]):
        n = get_random_num(config["n_modules"])
        issue_id = f"{config["prefix"]}{i}"
        modules = np.random.choice(all_modules, size=n, replace=False)

        a = np.empty(n)
        a.fill(1.)
        while True:
            A = np.random.dirichlet(a)
            if A.sum() == 1.0:
                break
        assert modules.shape == A.shape
        all_issues.update({str(issue_id):{k:v for k, v in zip(modules, A)}})

    issuematrix = pd.DataFrame(all_issues).fillna(.0)
    issuematrix.to_csv("./tmp/issuematrix.csv")

    return issuematrix


def generate_data(path_to_config:str, seed:Optional[int]=None) -> Tuple[
    Annotated[dict, "config"],
    Annotated[pd.DataFrame, "filematrix"],
    Annotated[pd.DataFrame, "fileauthors"],
    Annotated[pd.DataFrame, "modulematrix"],
    Annotated[pd.DataFrame, "issuematrix"]
]:
    """
    Generates the transition matrices needed to constract the markov config file.
    """
    if seed is not None:
        np.random.seed(seed)
    
    config, files, modules, authors = parse_config(path_to_config)
    # generate filematrix and fileauthors
    filematrix, fileauthors, all_files = generate_file_matrix(files, authors)
    # generate modulematrix
    modulematrix, all_modules = generate_module_matrix(modules, all_files)
    # generate issuematrix:
    issuematrix = generate_issue_matrix(config["Issues"], all_modules)

    return config, filematrix, fileauthors, modulematrix, issuematrix


def generate_markov(path_to_config:str, seed:Optional[int]=None) -> Annotated[dict, "markov_config"]:
    """
    Generates the markov config file used to generate synthetic repository.
    """
    markov = {}
    config, filematrix, fileauthors, modulematrix, issuematrix = generate_data(path_to_config, seed=seed)
    assert (np.round(filematrix.iloc[:,:].sum(axis=1) + fileauthors.iloc[:,-1], OUTPUT_ROUNDING) == 1).all, "files transitions do not sum up to 1!"
    
    # add issue sequence
    issues = []
    issues_ids = issuematrix.columns.tolist()    
    for issue_id in issues_ids:
        issue = Issue(issue_id)
        issue_modules = issuematrix.index[issuematrix.loc[:,issue_id] > 0.0].values.tolist()
        issue_modules_p = issuematrix.loc[issue_modules, issue_id].values
        assert check_probability(issue_modules_p), f"transitions for {str(issue)} do not sum to 1"
        
        for m, p in zip(issue_modules, issue_modules_p):
            issue.to = Module(m)
            issue.p = p
        issue.average_consecutive_commits = get_random_num(lam=config["Issues"]["lambda"])
        issues.append(issue)

    # add modules 
    modules = []
    modules_ids = modulematrix.columns.tolist()
    for module_id in modules_ids:

        module = Module(module_id)
        module_files = modulematrix.index[modulematrix.loc[:,module_id] > 0].values.tolist()
        module_files_p = modulematrix.loc[module_files, module_id].values.tolist()
        assert check_probability(module_files_p) == 1, f"transitions for {str(module)} do not sum to 1"

        for f, p in zip(module_files, module_files_p):
            module.to = File(f)
            module.p = p
        modules.append(module)

    # add files
    files_ids = filematrix.index.tolist()
    files = []
    for file_id in files_ids:
        file = File(file_id)
        file_files = filematrix.index[filematrix.loc[file_id,:] > 0].values.tolist()
        file_files_p = filematrix.loc[file_id, file_files].tolist()
    
        for f, p in zip(file_files, file_files_p):
            file.to = File(f)
            file.p = p
        author_p = fileauthors.loc[file_id, "AuthorProb"]
        file.to = Author(fileauthors.loc[file_id, "AuthorName"])
        file.p = float(author_p)
        assert np.round(np.sum(file_files_p) + author_p, OUTPUT_ROUNDING) == 1, f"transitions for {str(file)} do not sum to 1"

        files.append(file)

    # add authors
    autors_ids = fileauthors.loc[:, "AuthorName"].unique().tolist()
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