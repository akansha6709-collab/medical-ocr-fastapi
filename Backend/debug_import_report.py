import importlib.util, importlib, sys, os, traceback
modname = "src.parsers.doc_extractor"
print("CWD:", os.getcwd())
print("sys.path (first 8):", sys.path[:8])
try:
    spec = importlib.util.find_spec(modname)
    print("find_spec ->", spec)
    if spec is None:
        print("Module not found by find_spec; will try direct import to capture error.")
    else:
        print("spec.origin:", spec.origin)
        print("spec.loader:", spec.loader)
        origin = spec.origin
        try:
            with open(origin, "rb") as fh:
                data = fh.read()
            print("file exists:", os.path.exists(origin))
            print("file size:", len(data))
            print("null byte count:", sum(1 for b in data if b==0))
            print("first 120 bytes:", list(data[:120]))
        except Exception as e:
            print("Failed to open origin:", e)
except Exception:
    print("find_spec failed, traceback follows")
    traceback.print_exc()

print("\\nAttempting import to capture exact error (if any):")
try:
    m = importlib.import_module(modname)
    print("IMPORT OK:", m)
    try:
        print("module file:", getattr(m, '__file__', None))
    except Exception:
        pass
except Exception as e:
    print("IMPORT FAILED: type:", type(e), "repr:", repr(e))
    traceback.print_exc()
