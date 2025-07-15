import logging
import os
from pathlib import Path
import yaml
from typing import Optional, Annotated, Tuple
import numpy as np
import pandas as pd

from src.tags import *

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


def generate_file_matrix(files:dict, repo:dict, authors:list) -> Tuple[
    Annotated[pd.DataFrame, "filematrix"],
    Annotated[pd.DataFrame, "fileauthors"],
    Annotated[list, "repo_files"]
]:
    """
    Generate file dependancies matrix and author transitions for each file
    """
    all_files = []
    _ = [all_files.extend(repo[str(group)]["FileNames"]) for group in repo]
    n_files = len(all_files)
    FileMatrix = np.zeros((n_files, n_files), dtype=float)
    all_authors = [author["name"] for author in authors]
    authors_sampling_p = [author["p"] for author in authors]
    authors_by_name = []
    authors_transition = []
    m = 0
    for group in repo:
        group_files = repo[str(group)]["FileNames"]
        p = files[str(group)]["p"]
        n = len(group_files)
        if group != "Ungrouped":
            assert p > .0, "p must be > 0"
            assert p < 1., "p must be < 1"
            q = 1 - p
            x = [q/n]*n
            while True:
                A = np.random.dirichlet(np.ones(n), n) - x
                if (A > 0.).all():
                    FileMatrix[m:m+n, m:m+n] = A
                    m += n
                    authors_by_name.extend([str(np.random.choice(all_authors, p=authors_sampling_p))]*n)
                    authors_transition.extend([q]*n)
                    break
        else:
            x = [0.05/n]*n
            A = np.random.dirichlet(np.ones(n), n) - x
            A[A < 0] = 0.0
            FileMatrix[m:m+n, m:m+n] = A
            m += n
            authors_by_name.extend([str(np.random.choice(all_authors, p=authors_sampling_p)) for _ in range(n)])
            _ = [authors_transition.extend([1 - A[i].sum()]) for i in range(n)]


    assert len(authors_by_name) == n_files
    assert m == n_files

    for i in range(n_files):              # generate the 
        assert np.round(FileMatrix[i,:].sum() + authors_transition[i], OUTPUT_ROUNDING) == 1 # the sum of all the transition probabilities must sum up to 1
    
    filematrix = pd.DataFrame(FileMatrix, columns=all_files, index=all_files)
    fileauthors = pd.DataFrame(
        {
            "AuthorName": authors_by_name,
            "AuthorProb": authors_transition
        },
        index=all_files
    )

    return filematrix, fileauthors, all_files


def select_module_files(modules:dict, all_files:list) -> Tuple[Annotated[dict, "modules"]]:

    """
    Generate modules dependancies matrix.
    """
    all_mods = {}
    for module in modules:
        # select a number of files 
        mod_name = module["id"]
        module_files = np.random.choice(all_files, size=module["lambda"], replace=True)

        all_mods.update({str(mod_name):module_files})

    return all_mods


def generate_module_matrix(all_mods:dict, repo:dict) -> Tuple[
    Annotated[pd.DataFrame, "modulematrix"],
    Annotated[list, "modules_list"]
]:
    repo_files = []
    _ = [repo_files.extend(files["FileNames"]) for group, files in repo.items()]
    
    ModuleMatrix = {}
    for module_id, mod_files in all_mods.items():
        ModuleMatrix.update({str(module_id):{}})
        repo_mod_files = [f for f in mod_files if f in repo_files]
        n = len(repo_mod_files)
        if n:
            a = np.empty(n)
            a.fill(1.)
            A = np.random.dirichlet(a)
            for file, p in zip(repo_mod_files, A):
                if not str(file) in ModuleMatrix[str(module_id)]:
                    ModuleMatrix[str(module_id)].update({str(file):float(p)})
                else:
                    ModuleMatrix[str(module_id)].update({str(file):ModuleMatrix[str(module_id)][str(file)] + float(p)})
    
    modulematrix = pd.DataFrame(ModuleMatrix).fillna(.0)

    return modulematrix, list(ModuleMatrix.keys())


def select_issue_modules(issues_config:dict, all_modules:list) -> Tuple[Annotated[dict, "issues"]]:

    all_issues = {}
    for i in range(issues_config["number"]):
        n = get_random_num(issues_config["n_modules"])
        issue_id = f"{issues_config["prefix"]}{i}"
        modules = np.random.choice(list(all_modules.keys()), size=n, replace=False)
        all_issues.update({str(issue_id):modules})

    return all_issues


def generate_issue_matrix(all_issues:dict, repo_modules:list) -> Annotated[pd.DataFrame, "issuematrix"]:
    """
    Generate issues impact matrix.
    """
    IssueMatix = {}
    for issue_id, issue_mods in all_issues.items():
        IssueMatix.update({str(issue_id):{}})
        repo_issue_modules = [m for m in issue_mods if m in repo_modules]
        n = len(repo_issue_modules)
        if n:
            a = np.empty(n)
            a.fill(1.)
            while True:
                A = np.random.dirichlet(a)
                if A.sum() == 1.0:
                    break
            IssueMatix.update({str(issue_id):{k:v for k, v in zip(repo_issue_modules, A)}})

    issuematrix = pd.DataFrame(IssueMatix).fillna(.0)   

    return issuematrix


def select_groups(groups:list, n:int) -> Tuple[list, list]:
    m = len(groups)
    repo_groups = []
    while n > 0:
        idx = np.random.choice(range(len(groups)))
        repo_groups.append(groups.pop(idx))
        n -= 1
    assert len(groups) + len(repo_groups) == m

    return groups, repo_groups


def select_ungrouped(files:list, n:int) -> Tuple[list, list]:
    m = len(files)
    repo_ungrouped = []
    while n > 0:
        idx = np.random.choice(range(len(files)))
        repo_ungrouped.append(files.pop(idx))
        n -= 1
    assert len(files) + len(repo_ungrouped) == m
    
    return files, repo_ungrouped


def split_groups(files:dict, n_split:int, n_files:int) -> Annotated[dict, "repos"]:
    """
    split file groups and files between n_split repos.
    """
    groups = list(files.keys())
    _ = groups.pop(groups.index("Ungrouped"))
    m = len(groups)
    lam = int(m / n_split)
    ungrouped_files = files["Ungrouped"]["FileNames"]
    u_lam = int(len(ungrouped_files) / n_split)
    
    repos = {}

    assert (
        (
            sum([len(files[g]["FileNames"]) for g in groups]) 
            + len(ungrouped_files)
        ) == n_files
    )

    file_n = 0

    for i in range(n_split - 1):
        n = get_random_num(lam=lam)
        groups, repo_groups = select_groups(groups, n)
        
        assert len(groups) + n == m

        repo_files = {}
        for group in repo_groups:
            repo_files.update({group:files[group]})
        u = get_random_num(lam=u_lam)
        ungrouped_files, repo_ungrouped = select_ungrouped(ungrouped_files, u)
        repo_files.update({"Ungrouped":{"FileNames":repo_ungrouped, "p":0.0}})

        repos.update({f"Repo_{i}":repo_files})
        m -= n
        file_n += sum([len(repo_files[g]["FileNames"]) for g in repo_groups]) + len(repo_files["Ungrouped"]["FileNames"])
    
    assert len(groups) == m
    repo_files = {}
    for group in groups:
        repo_files.update({group:files[group]})
    repo_files.update({"Ungrouped":{"FileNames":ungrouped_files, "p":0.0}})
    repos.update({f"Repo_{n_split - 1}":repo_files})

    file_n += sum([len(repo_files[g]["FileNames"]) for g in groups]) + len(repo_files["Ungrouped"]["FileNames"])

    assert file_n == n_files, "missing files in repos configuration."

    return repos
    

def generate_data(path_to_config:str, n_split:int, seed:Optional[int]=None) -> Tuple[
    Annotated[dict, "config"],
    Annotated[dict, "repos"],
    Annotated[pd.DataFrame, "filematrix"],
    Annotated[pd.DataFrame, "fileauthors"],
    Annotated[pd.DataFrame, "modulematrix"],
    Annotated[pd.DataFrame, "issuematrix"]
]:
    """
    Generates the transition matrices needed to constract the markov config file.
    """
    repos_list = []
    filematrix_list = []
    fileauthors_list = []
    modulematrix_list = []
    issuematrix_list = []
    all_files = []

    if seed is not None:
        np.random.seed(seed)
    
    config, files, modules, authors = parse_config(path_to_config)
    repos = split_groups(files, n_split, config["Files"]["number"]) 
    # generate filematrix and fileauthors
    for repo_id, repo in repos.items():
        filematrix, fileauthors, repo_files = generate_file_matrix(files, repo, authors)
        filematrix.to_csv(f"./tmp/filematrix_{repo_id}.csv")
        fileauthors.to_csv(f"./tmp/fileauthors_{repo_id}.csv")
        filematrix_list.append(filematrix)
        fileauthors_list.append(fileauthors)
        all_files.extend(repo_files)
    pd.concat(filematrix_list, axis=1, ignore_index=False).fillna(0.0).to_csv("./tmp/filematrix.csv")
    pd.concat(fileauthors_list, axis=0, ignore_index=False).to_csv("./tmp/fileauthors.csv")
    
    all_modules = select_module_files(modules, all_files)
    all_issues = select_issue_modules(config["Issues"], all_modules)
    # generate modulematrix and issuematrix
    for repo_id, repo in repos.items():
        repos_list.append(repo_id)
        # generate modulematrix
        modulematrix, repo_modules = generate_module_matrix(all_modules, repo)
        modulematrix.to_csv(f"./tmp/modulematrix_{repo_id}.csv")
        modulematrix_list.append(modulematrix)
        # generate issuematrix:
        issuematrix = generate_issue_matrix(all_issues, repo_modules)
        issuematrix.to_csv(f"./tmp/issuematrix_{repo_id}.csv")
        issuematrix_list.append(issuematrix)

    return config, repos_list, filematrix_list, fileauthors_list, modulematrix_list, issuematrix_list


def generate_markov(
    path_to_config:str, n_split:int, path_to_output:str, seed:Optional[int]=None
) -> Annotated[dict, "markov_config"]:
    """
    Generates the markov config file used to generate synthetic repository.
    """
    logging.info("Generating synthetic repo configuration.")
    markov = {}
    logging.debug("Parsing configuration.")
    try:
        (config, repos_list, filematrix_list, fileauthors_list, modulematrix_list, 
            issuematrix_list) = generate_data(path_to_config, n_split, seed=seed)
    except Exception as e:
        logging.error(e)
        raise e

    logging.debug("Generating markov configuration files.")

    for repo_id, filematrix, fileauthors, modulematrix, issuematrix in zip(
        repos_list, 
        filematrix_list, 
        fileauthors_list, 
        modulematrix_list, 
        issuematrix_list
    ):
        logging.info(f"Processing repo {repo_id}")
        try:
            assert bool((np.round(filematrix.iloc[:,:].sum(axis=1) + fileauthors.iloc[:,-1], OUTPUT_ROUNDING) == 1).all()), "files transitions do not sum up to 1!"
            # add files
            files_ids = filematrix.index.tolist()
            files = []
            for file_id in files_ids:
                file = File(file_id)
                file_files = filematrix.loc[files_ids, files_ids].index[filematrix.loc[file_id,files_ids] > 0].values.tolist()
                file_files_p = filematrix.loc[file_id, file_files].tolist()

                for f, p in zip(file_files, file_files_p):
                    file.to = File(f)
                    file.p = p
                author_p = fileauthors.loc[file_id, "AuthorProb"]
                file.to = Author(fileauthors.loc[file_id, "AuthorName"])
                file.p = float(author_p)
                assert np.round(np.sum(file_files_p) + author_p, OUTPUT_ROUNDING) == 1, f"transitions for {str(file)} do not sum to 1"

                files.append(file)

                logging.info(f"Generated {len(files)} files.")
        except Exception as e:
            logging.error(e)
            raise e

        # add authors
        try:
            autors_ids = fileauthors.loc[files_ids, "AuthorName"].unique().tolist()
            authors = []
            for author_id in autors_ids:
                author = Author(author_id)
                author.to = Commit()
                author.p = 1.
                authors.append(author)
            logging.info(f"Connected {len(autors_ids)} authors.")
        except Exception as e:
            logging.error(e)
            raise e

        try:
            # add modules 
            modules = []
            modules_ids = modulematrix.columns.tolist()
            for module_id in modules_ids:
                module = Module(module_id)
                filt_modmat = modulematrix.loc[modulematrix.index.isin(files_ids)]
                module_files = filt_modmat.index[(filt_modmat.loc[:, module_id] > 0)].values.tolist()
                if len(module_files):
                    module_files_p = filt_modmat.loc[module_files, module_id].values.tolist()
                    assert check_probability(module_files_p) == 1, f"transitions for {str(module)} do not sum to 1"

                    for f, p in zip(module_files, module_files_p):
                        module.to = File(f)
                        module.p = p
                    modules.append(module)
            logging.info(f"Attached {len(modules)} modules to repo.")
        except Exception as e:
            logging.error(e)
            raise e

        try:
            # add issue sequence
            issues = []
            issues_ids = issuematrix.columns.tolist()    
            for issue_id in issues_ids:
                issue = Issue(issue_id)
                issue_modules = issuematrix.index[issuematrix.loc[:,issue_id] > 0.0].values.tolist()
                if len(issue_modules):
                    issue_modules_p = issuematrix.loc[issue_modules, issue_id].values
                    assert check_probability(issue_modules_p), f"transitions for {str(issue)} do not sum to 1"
                    
                    for m, p in zip(issue_modules, issue_modules_p):
                        issue.to = Module(m)
                        issue.p = p
                    issue.average_consecutive_commits = get_random_num(lam=config["Issues"]["lambda"])
                    issues.append(issue)

            average_consecutive_commits = {str(i):float(i.average_consecutive_commits) for i in issues}
            issue_sequence = { 
                "average_consecutive_commits":average_consecutive_commits
            }
            logging.info(f"Created {len(issues)} for current repo.")
        except Exception as e:
            logging.error(e)
            raise e
    
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

        logging.info(f"{repo_id} configuration created.")
        with open(path_to_output / f"markov_{repo_id}.yaml", 'w') as f:
            f.write(yaml.dump(markov, sort_keys=False).replace("'", ""))
        logging.info(f"Configuration file saved {path_to_output / f"markov_{repo_id}.yaml"}")