from src.generator import generate_files, generate_modules, generate_authors

N_GROUPS = 12


groups = {
    "FileGroups":{
        "number": N_GROUPS,
        "random": True,
        "lenght": 4,
        "p": 0.9
    }
}

files = generate_files(20, "File", groups["FileGroups"])

modules = generate_modules(5, "Module", 5.0, rand=True)

equal_authors = generate_authors(4, "Author", contribution="equal")

rand_authors = generate_authors(4, "Author", contribution="random")

exit(0)