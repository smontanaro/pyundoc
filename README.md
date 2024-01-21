# pyundoc

Note possibly undocumented module attributes

Compare module contents with doc items.

1. Extract list of modules from local htmllive server.
2. Open corresponding .rst doc file and extract relevant refs
   (.. function, etc).
3. Compare module globals with Sphinx inventory and note any globals
   which appear to be missing from the doc file.
