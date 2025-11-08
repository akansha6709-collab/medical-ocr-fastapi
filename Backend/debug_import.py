import importlib,inspect,traceback,sys,os
modname = "src.parsers.doc_extractor"
print("PYTHONPATH:", os.getcwd())
try:
    m = importlib.import_module(modname)
    print("MODULE OK:", m)
    f = inspect.getsourcefile(m) or getattr(m, "__file__", None)
    print("loaded from file:", f)
    # print first 128 bytes
    with open(f, "rb") as fh:
        b = fh.read(128)
    print("first 128 bytes (as ints):", list(b[:128]))
except Exception:
    print("IMPORT FAILED - traceback:")
    traceback.print_exc()
