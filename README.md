# pyundoc

This script attempts to answer a very simple question. For any module
M, which of the globally visible attributes don't appear as references
of some kind (references in the Sphinx sense) in the module's
documentation?

1. Extract list of modules from local htmllive server.
2. Load Sphinx inventory and reorganize slightly.
3. Compare module globals with extracted refs and note any globals
   which appear to be missing from the doc file.

Note that while it fetches the module index from a server, it really
will only work if that server is local, so you can read the
`objects.inv` file.
