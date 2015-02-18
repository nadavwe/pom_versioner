#! /usr/bin/python

import re
from functools import total_ordering
import itertools

DEPEND = r"""<dependency>\s*
<groupId>(?P<groupId>[\-\.\w]+)</groupId>\s*
<artifactId>(?P<artifactId>[\$\{\}\-\.\w]+)</artifactId>\s*
<version>(?P<version>[\$\{\}\.\-\w]+)</version>\s*
.*?
</dependency>""".replace("\n",'')

SIMPLE_DEPEND = r"POM\s+(?P<groupId>[\-\.\w]+)\s*;\s*(?P<artifactId>[\$\{\}\-\.\w]+)\s*;\s*(?P<version>[\$\{\}\.\-\w]+)"

PATTERNS = DEPEND, SIMPLE_DEPEND

SEPERATORS = ['.', '-']
SEP_PATTERN = re.compile("[%s]" % "".join(("\\" + sep) for sep in SEPERATORS))


class Sep(str):
    SEP_HASH = hash(object())
    def __eq__(self, other):
            return isinstance(other, Sep)
    def __hash__(self):
            return SEP_HASH
    def __repr__(self):
            return "Sep(%s)" % self

to_sep = lambda x: x if x not in SEPERATORS else Sep(x)
to_sep_seq = lambda l: [to_sep(x) for x in l] + [Sep('')]

def to_int(s):
    try:
        return int(s)
    except:
        return s

@total_ordering
class Version(object):
    def __init__(self, version):
        self.version = version
        self.exploded = tuple(to_int(x) for x in SEP_PATTERN.split(version))
    def __str__(self):
        return self.version
    __repr__ = __str__

    def __hash__(self):
        return hash(self.version)
    
    def __eq__(self, other):
        return self.version == other.version

    def __lt__(self, other):
        for myver, otherver in zip(self.exploded, other.exploded):
            if myver < otherver:
                return True
            if myver > otherver:
                return False
        return False
            


class POM(object):
    def __init__(self, group_id, artifact_id, version):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = Version(version)

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
            pos = idx+1
            if all(x==y for x,y in zip(elem1[-pos:], elem2[:pos])):
                return pos
        return 0  

    def get_version(self):
        artifact_id = self.artifact_id.partition('_')[0]

        group_id_elements = to_sep_seq(self.group_id)
        artifact_id_elements = to_sep_seq(artifact_id)    

        pos = self.find_overlap(group_id_elements, artifact_id_elements)        

        data = [self.group_id]
        artifact_part = "".join(artifact_id_elements[pos:])
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

   
def main():
    args = parseargs()
    
    from collections import defaultdict
    d = defaultdict(set)
    for f in args.files:
        data = open(f).read()
        for pattern in PATTERNS:
            for match in re.finditer(pattern, data, flags=re.DOTALL):
                pom = POM.from_match(match)
                if all(pattern not in pom.group_id for pattern in args.exclude): 
                    d[pom].add(f)
                    
    sorted_keys = sorted(d.keys(), key=str)


    if args.printfiles:
        for pom in sorted_keys:
            print pom, d[pom]

    if args.versions:    
        for pom in sorted_keys:
            print pom.get_version_property()
        print "\n"

    if args.dependencies:
        for _, poms in itertools.groupby(sorted_keys, key=lambda pom: (pom.artifact_id, pom.group_id)):
            print next(poms).get_depends()

def parseargs():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v','--property-versions', dest='versions', action='store_true',
                       default=False, help='print version properties')
    parser.add_argument('-d','--dependencies', dest='dependencies', action='store_true',
                       default=False, help='print dependency')    
    parser.add_argument('-f','--print-with-files', dest='printfiles', action='store_true',
                       default=False, help='print data with files')
    parser.add_argument('-x','--exclude-pattern', dest='exclude', action='append',
                       help='exclude a pom if the pattern appers in the pom group id')
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()
    return args
     
if __name__ == "__main__":
    main()
