"""showyml.py - read .yml and dump as json.

Usage:
  python showym.py [file ...]

  It no input files a provided, use tests.yml
"""

import json
import sys
import yaml


def show_expanded(path):
  with open(path, mode='r') as f:
    yml = yaml.load(f, Loader=yaml.FullLoader)
    print(json.dumps(yml, indent=2, sort_keys=True))


if __name__ == '__main__':
  if len(sys.argv) < 2:
    show_expanded('tests.yml')
  else:
    for f in sys.argv[1:]:
      show_expanded(f)
