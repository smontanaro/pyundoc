#!/usr/bin/env python3

"""Compare module contents with doc items.

1. Extract list of modules from local htmllive server.
2. Open corresponding .rst doc file and extract relevant refs (.. function, etc).
3. Compare module globals with extracted refs and note any globals which appear to
   be missing from the doc file.
"""

import argparse
import importlib
import os
import random
import re
import sys
import types

import requests

IGNORE_MODULE = ()

def main():
    return 0

if __name__ == "__main__":
    sys.exit(main())
