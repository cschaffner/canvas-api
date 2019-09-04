
randstring = []
for i in range(10000):
  if random.uniform(0,1) <= 0.01:
    randstring.append('0')
  else:
    randstring.append('1')

with open('random.txt', 'w') as fout:
    fout.write(randstring)

