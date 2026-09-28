import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("indices", nargs="*", type=int)
args = parser.parse_args()

path = Path(__file__).parents[2] / "Lab7_Forecasting_ETTh1.ipynb"
notebook = json.loads(path.read_text(encoding="utf-8"))
print(f"cells {len(notebook['cells'])}")
for index, cell in enumerate(notebook["cells"]):
    if args.indices and index not in args.indices:
        continue
    source = "".join(cell.get("source", [])).replace("\n", " ")[:180]
    outputs = cell.get("outputs", [])
    output_types = [output.get("output_type") for output in outputs]
    image_count = sum("image/png" in output.get("data", {}) for output in outputs)
    print(
        f"{index:03d} {cell['cell_type']:8s} outs={len(outputs):2d} "
        f"imgs={image_count} types={output_types} :: {source}"
    )
    if args.indices:
        print("SOURCE:")
        print("".join(cell.get("source", [])).encode("ascii", "backslashreplace").decode())
        for output_index, output in enumerate(outputs):
            print(f"OUTPUT {output_index}:")
            payload = output.get("text")
            if payload is None:
                payload = output.get("data", {}).get("text/plain", "")
            if isinstance(payload, list):
                payload = "".join(payload)
            print(str(payload).encode("ascii", "backslashreplace").decode())
