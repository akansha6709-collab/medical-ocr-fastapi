import sys, os
mod = "src.parsers.doc_extractor"
parts = mod.split(".")
candidates = []
for p in sys.path:
    if not p:
        p = os.getcwd()
    # build candidate filesystem paths for module/package import rules
    base = os.path.join(p, *parts) + ".py"
    package_init = os.path.join(p, *parts, "__init__.py")
    pkg_parent = os.path.join(p, *parts[:-1])
    candidates.append(base)
    candidates.append(package_init)
    # Also check parent package __init__ files
    for i in range(1, len(parts)):
        candidates.append(os.path.join(p, *parts[:i], "__init__.py"))
candidates = list(dict.fromkeys(candidates))  # uniq preserve order

print("CWD:", os.getcwd())
print("Checking", len(candidates), "candidate files from sys.path (first 6 shown):", sys.path[:6])
print()

bad = []
for path in candidates:
    try:
        if os.path.exists(path):
            b = open(path, "rb").read()
            nulls = sum(1 for x in b if x==0)
            print(f"FOUND: {path}  size={len(b)}  null_bytes={nulls}")
            if nulls>0:
                bad.append((path, len(b), nulls, list(b[:120])))
        # else: print(f"MISS: {path}")
    except Exception as e:
        print("ERR reading", path, ":", type(e), e)
print()
if bad:
    print("=== PROBLEM FILES (first 10) ===")
    for p,s,n,first in bad[:10]:
        print(p)
        print(" size:", s, " nulls:", n)
        print(" first bytes:", first)
        print()
else:
    print("No candidate file contained null bytes.")
