from pathlib import Path
import subprocess
import sys


root = Path(__file__).resolve().parents[1]
destination = root / "shopeasy" / "generated"
for source in sorted((root / "proto").glob("*.proto")):
    subprocess.run([sys.executable,"-m","grpc_tools.protoc",f"-I{root / 'proto'}",f"--python_out={destination}",f"--grpc_python_out={destination}",str(source)],check=True)
    stub = destination / (source.stem + "_pb2_grpc.py")
    module = source.stem + "_pb2"
    stub.write_text(stub.read_text(encoding="utf-8").replace(f"import {module} as",f"from . import {module} as"),encoding="utf-8")
    print(f"gRPC-Stubs aus {source.name} erzeugt.")
