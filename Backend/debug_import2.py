import importlib.util, sys, os, traceback

modname = "src.parsers.doc_extractor"
print("CWD:", os.getcwd())
spec = importlib.util.find_spec(modname)
print("spec:", spec)
if spec is None:
    print("spec is None (module not found via find_spec).")
else:
    print("spec.origin:", spec.origin)
    print("spec.loader:", spec.loader)
    origin = spec.origin
    try:
        with open(origin, "rb") as fh:
            data = fh.read()
        print("file exists:", os.path.exists(origin))
        print("file size bytes:", len(data))
        print("first 120 bytes:", list(data[:120]))
        nulls = sum(1 for b in data if b == 0)
        print("null byte count:", nulls)
    except Exception as e:
        print("failed to open/read origin:", e)
        traceback.print_exc()
