import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
lines = open(sys.argv[1], encoding="utf-8").readlines()
start, end = int(sys.argv[2]), int(sys.argv[3])
for i, l in enumerate(lines[start - 1 : end], start):
    print(f"{i:4d}|{l}", end="")
