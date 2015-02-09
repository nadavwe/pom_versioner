#! /usr/bin/python

import re

DEPEND = r"""<dependency>\s*
<groupId>(?P<groupId>[\-\.\w]+)</groupId>\s*
<artifactId>(?P<artifactId>[\$\{\}\-\.\w]+)</artifactId>\s*
<version>(?P<version>[\$\{\}\.\-\w]+)</version>\s*
.*?
</dependency>""".replace("\n",'')

SIMPLE_DEPEND = r"POM\s+(?P<groupId>[\-\.\w]+)\s*;\s*(?P<artifactId>[\$\{\}\-\.\w]+)\s*;\s*(?P<version>[\$\{\}\.\-\w]+)"


class POM(object):
    def __init__(self, group_id, artifact_id, version):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

    @staticmethod
    def from_string(st):
        match = re.match(DEPEND, st)
        return POM.from_match(match)
        
    @staticmethod
    def from_match(match):
        return POM(match.group("groupId"),
                   match.group("artifactId"),
                   match.group("version"))

    def __str__(self):
        return "POM('{group_id}','{artifact_id}','{version}')".format(**self.__dict__)
    __repr__ = __str__

    def find_overlap(self, elem1, elem2):
        for idx,_ in enumerate(elem2):
            if all(x==y for x,y in zip(elem1[-idx-1:], elem2[:idx+1])):
                return idx+1
        return 0

    def get_version(self):
        artifact_id = self.artifact_id.partition('_')[0]

        group_id_elements = re.split(r"[\-\.]", self.group_id)
        artifact_id_elements = artifact_id.split('-')    

        pos = self.find_overlap(group_id_elements, artifact_id_elements)        

        data = [self.group_id]
        artifact_part = "-".join(artifact_id_elements[pos:])
        if artifact_part:
            data.append(artifact_part)
        
        data.append('version')
        return ".".join(data)

    def get_depends(self):
        return """<dependency>
\t<groupId>{group_id}</groupId>
\t<artifactId>{artifact_id}</artifactId>
\t<version>${{{prop_version}}}</version>
</dependency>""".format(prop_version=self.get_version(),
                        **self.__dict__)

    def get_version_property(self):
        return "<{prop_version}>{version}</{prop_version}>".format(
            prop_version=self.get_version(), version=self.version)

    def __eq__(self, other):
        return (self.group_id == other.group_id and
                self.artifact_id == other.artifact_id and
                self.version == other.version)

    def __hash__(self):
        return hash((self.group_id, self.artifact_id, self.version))  
    

def main(data, summary=True):
    poms = []
    for match in re.finditer(DEPEND, data, flags=re.DOTALL):
        poms.append(POM.from_match(match))
    for match in re.finditer(SIMPLE_DEPEND, data):
        poms.append(POM.from_match(match))

    if summary:
        for pom in sorted(poms, key=str):
            print pom, pom.get_version()
    else:
        for pom in sorted(poms, key=str):
            print pom.get_version_property()
        print "\n"
        for pom in sorted(poms, key=str):
            print pom.get_depends()
        

def main2(files):
    pass


if __name__ == "__main__":
    import sys
    main(sys.stdin.read(), sys.argv[1] != 'detailed')

