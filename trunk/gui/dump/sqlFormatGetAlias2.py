import re

catalog = ['IVMS_STG_FLOW_LOAD', 'IVMS_STG_PID_LOAD']

foo = """SELECT *
FROM   IVMS_STG_FLOW_LOAD flow_load;

SELECT *
FROM   IVMS_STG_PID_LOAD as pid_load;"""

#foo = foo.upper()
##for i in foo.splitlines():
##    print re.split("\s", i)


regex = re.compile("|".join(("%s\s+(as)?\s?[\w\_]+" % re.escape(i) for i in catalog)),
            re.IGNORECASE)

alias = {}
for a in re.findall(regex, foo):
    a = re.split("\s|as", a, flags=re.IGNORECASE)
    print a
    alias[a[-1]] = a[0]

print alias