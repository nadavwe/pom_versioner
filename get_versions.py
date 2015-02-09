#! /usr/bin/python

import re

DEPEND = r"""<dependency>\s*
<groupId>(?P<groupId>[\-\.\w]+)</groupId>\s*
<artifactId>(?P<artifactId>[\$\{\}\-\.\w]+)</artifactId>\s*
<version>(?P<version>[\$\{\}\.\-\w]+)</version>\s*
.*?
</dependency>""".replace("\n",'')


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

    def get_version(self):
        data = [self.group_id]
        artifact_id = self.artifact_id.partition('_')[0]
        if not self.group_id.endswith(artifact_id):
            data.append(artifact_id)
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

    
    

def main(data, summary=True):
    poms = []
    for match in re.finditer(DEPEND, data, flags=re.DOTALL):
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
        
    

if __name__ == "__main__":
    import sys
    main(sys.stdin.read(), sys.argv[1] != 'detailed')

