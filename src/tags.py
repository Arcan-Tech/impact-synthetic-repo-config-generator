import yaml

class tag(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!tag'
    def __init__(self, name:str):
        self.name

    def __repr__(self):
        return f"{self.yaml_tag} {self.name}"

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


class Commit(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Commit'
    def __init__(self, name:str=" "):
        self.name = name
    def __repr__(self):
        return f"{self.yaml_tag} "


class Author(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Author'
    def __init__(self, name:str):
        self.name = name
        self.__to = []
        self.__p = []

    @property
    def to(self) -> list[Commit]:
        return self.__to
    
    @to.setter
    def to(self, commit:Commit):
        self.__to.append(commit)

    @property
    def p(self) -> list[float]:
        return self.__p

    @p.setter
    def p(self, value:float):
        self.__p.append(value)


class File(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!File'
    def __init__(self, name:str):
        self.name = name
        self.__to = []
        self.__p = []

    @property
    def to(self) -> list[tag]:
        return self.__to
    
    @to.setter
    def to(self, obj:tag):
        self.__to.append(obj)

    @property
    def p(self) -> list[float]:
        return self.__p

    @p.setter
    def p(self, value:float):
        self.__p.append(value)


class Module(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Module'
    def __init__(self, name:str):
        self.name = name
        self.__to = []
        self.__p = []

    @property
    def to(self) -> list[File]:
        return self.__to
    
    @to.setter
    def to(self, file:File):
        self.__to.append(file)

    @property
    def p(self) -> list[float]:
        return self.__p

    @p.setter
    def p(self, value:float):
        self.__p.append(value)


class Issue(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Issue'
    def __init__(self, name:str):
        self.name = name
        self.__to = []
        self.__p = []
        self.__average_consecutive_commits = 1

    @property
    def to(self) -> list[Module]:
        return self.__to
    
    @to.setter
    def to(self, module:Module):
        self.__to.append(module)

    @property
    def p(self) -> list[float]:
        return self.__p

    @p.setter
    def p(self, value:float):
        self.__p.append(value)

    @property
    def average_consecutive_commits(self) -> float:
        return self.__average_consecutive_commits

    @average_consecutive_commits.setter
    def average_consecutive_commits(self, value:float):
        self.__average_consecutive_commits = value


class Initial(tag):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Initial'
    def __init__(self, name:str):
        self.name = name
        self.__to = []
        self.__p = []
        self.__average_consecutive_commits = 1

    @property
    def to(self) -> list[Issue]:
        return self.__to
    
    @to.setter
    def to(self, issue:Issue):
        self.__to.append(issue)

    @property
    def p(self) -> list[float]:
        return self.__p

    @p.setter
    def p(self, value:float):
        self.__p.append(value)