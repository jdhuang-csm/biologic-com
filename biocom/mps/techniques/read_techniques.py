# import pandas as pd
# One-time script for processing technique codes from documentation

with open('technique_codes.txt', 'r') as f:
    text = f.read()
    
    
def parse_line(line):
    if len(line) > 0:
        ls = line.split(' ')
        index = ls[0]
        code = ls[1]
        name = ' '.join(ls[2:])
        return index, code, name
    return line


lines = text.split('\n')
print(lines[:5])
body = [','.join(parse_line(l)) for l in lines]
header = 'ID,Code,Name'
output = '\n'.join([header] + body)

with open('technique_codes.csv', 'w') as f:
    f.write(output)