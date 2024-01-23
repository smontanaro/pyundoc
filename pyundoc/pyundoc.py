#!/usr/bin/env python3

"""Compare module contents with doc items.

This script attempts to answer a very simple question. For any module M, which
of the globally visible attributes don't appear as references of some kind
(references in the Sphinx sense) in the module's documentation?

1. Extract list of modules from local htmllive server.
2. Load Sphinx inventory and reorganize slightly.
3. Compare module globals with extracted refs and note any globals which appear
to be missing from the doc file.
"""

import argparse
from dataclasses import dataclass, astuple
import importlib
import inspect
import os
import re
import sys
import textwrap

import requests
from sphobjinv.cli.load import import_infile

IGNORE_MODULE = set()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--docurl", dest="docurl",
                        default="http://127.0.0.1:8000/",
                        help="server from which to fetch module index")
    parser.add_argument("-d", "--docbase", dest="docbase", default="Doc",
                        help="documentation base")
    # TODO: should be "append" to allow multiple instances
    parser.add_argument("-m", "--module", dest="module", default="",
                        help="single module to check")
    parser.add_argument("-s", "--sort", dest="sorted", action="store_true",
                        default=False, help="sort output")
    parser.add_argument("-i", "--ignore-missing", dest="use_missing",
                        action="store_false", default=True,
                        help="ignore OK_MISSING dict")
    args = parser.parse_args()

    if not args.module:
        modindex = requests.get(f"{args.docurl}py-modindex.html", timeout=4).text
        mnames = find_modules(modindex, args.docbase)
    else:
        # not perfect, but good enough for now
        mname = args.module
        mnames = [mname]

    if args.sorted:
        mnames.sort()

    invfile = os.path.join(args.docbase, "build", "html", "objects.inv")
    if not os.path.exists(invfile):
        print(f"Inventory file {invfile} doesn't exist.", file=sys.stderr)
        return 1
    invdict = load_inventory(invfile)

    print("# Possibly Undocumented Module Attributes")
    print()

    for mname in mnames:
        search_missing(mname, invdict, args.use_missing)
    return 0

def search_missing(mname, invdict, use_missing):
    missing = set()
    try:
        mod_obj = importlib.import_module(mname)
    except ImportError:
        return
    if use_missing and OK_MISSING.get(mname) is IGNORE_MODULE:
        # perhaps a module like tkinter which isn't documented at this
        # level
        return

    all_names = get_symbol_patterns(mname)
    for name in all_names:
        match = None
        full_name = f"{mname}.{name}"
        for record in invdict.get(name, set()):
            if record.name == full_name:
                match = record

        if match is None:
            # probably too aggressive, as it will skip submodules of
            # mod_obj, not just global modules like sys or os.
            if inspect.ismodule(getattr(mod_obj, name, False)):
                continue
            missing.add(name)
    if use_missing:
        missing -= OK_MISSING.get(mname, set())
    if missing:
        para = (f"**{mname}** ({len(missing)}):"
            f"`{', '.join(sorted(missing))}`")
        print("*", textwrap.fill(para, subsequent_indent="  "))

def load_inventory(invfile):
    "Load Sphinx inventory and massage into a more useful format."
    inventory = import_infile(invfile)

    invdict = {}
    for obj in inventory.objects:
        name = obj.name.split(".")[-1]
        if name not in invdict:
            invdict[name] = set()
        invdict[name].add(SOIData(obj.name, obj.domain, obj.role,
                                  obj.priority, obj.uri, obj.dispname))
    return invdict

def find_modules(modindex, docbase):
    "get module names and rst files from module index"
    mnames = set()
    for line in modindex.split("\n"):
        if "#module-" in line:
            pre, post, *_rest = line.strip().split("><")
            html = re.search('href="([^"]+)', pre).group(1).split("#")[0]
            rst = os.path.join(docbase, html.replace(".html", ".rst"))
            file_base = os.path.splitext(os.path.basename(rst))[0]
            mname = re.search('>([^<]+)<', post).group(1)
            if mname[0] == "_" or file_base != mname:
                continue
            mnames.add(mname)
    return list(mnames)

def get_symbol_patterns(mname, pattern=None):
    "Return a set of attribute names in module mname which match pattern."
    try:
        mod = importlib.import_module(mname)
        if pattern is None:
            try:
                attrs = getattr(mod, "__all__")
            except AttributeError:
                attrs = [attr for attr in dir(mod) if attr[0] != "_"]
        else:
            pat = re.compile(pattern)
            attrs = [attr for attr in dir(mod) if pat.match(attr) is not None]
        return set(attrs)
    except ImportError:
        return set()

@dataclass
class SOIData:
    "Hashable mimic of sphobjinv.DataObjStr."
    # It seems silly that I need to create this class. There's probably a
    # better way to do this, maybe add a hash method to DataObjStr?
    name: str
    domain: str
    role: str
    priority: str
    uri: str
    dispname: str

    def __hash__(self):
        return hash(astuple(self))

OK_MISSING = {
    "builtins": IGNORE_MODULE,
    "ast": {
        # These are all deprecated, according to comments in ast.py.
        'slice', 'Index', 'ExtSlice', 'Slice', 'AugLoad', 'AugStore',
        'Param', 'Suite',
        # Imported from elsewhere
        'IntEnum', 'auto', 'contextmanager', 'nullcontext',
    },
    # should be imported from os?
    # "io": {'SEEK_CUR', 'SEEK_END', 'SEEK_SET',},
    "pickle": {'ADDITEMS', 'APPEND', 'APPENDS', 'BINBYTES', 'BINBYTES8',
               'BINFLOAT', 'BINGET', 'BININT', 'BININT1', 'BININT2',
               'BINPERSID', 'BINPUT', 'BINSTRING', 'BINUNICODE',
               'BINUNICODE8', 'BUILD', 'BYTEARRAY8', 'DICT', 'DUP',
               'EMPTY_DICT', 'EMPTY_LIST', 'EMPTY_SET', 'EMPTY_TUPLE',
               'EXT1', 'EXT2', 'EXT4', 'FALSE', 'FLOAT', 'FRAME',
               'FROZENSET', 'GET', 'GLOBAL', 'INST', 'INT', 'LIST',
               'LONG', 'LONG1', 'LONG4', 'LONG_BINGET', 'LONG_BINPUT',
               'MARK', 'MEMOIZE', 'NEWFALSE', 'NEWOBJ', 'NEWOBJ_EX',
               'NEWTRUE', 'NEXT_BUFFER', 'NONE', 'OBJ', 'PERSID', 'POP',
               'POP_MARK', 'PROTO', 'PUT', 'READONLY_BUFFER', 'REDUCE',
               'SETITEM', 'SETITEMS', 'SHORT_BINBYTES', 'SHORT_BINSTRING',
               'SHORT_BINUNICODE', 'STACK_GLOBAL', 'STOP', 'STRING',
               'TRUE', 'TUPLE', 'TUPLE1', 'TUPLE2', 'TUPLE3', 'UNICODE',},
    "ssl": {"create_connection", "SO_TYPE", "SOL_SOCKET",},
    "syslog": {'LOG_UPTO', 'LOG_MASK',},
    "termios": {'CRTSCTS', 'CSIZE', 'TIOCSCTTY', 'VINTR', 'B4800', 'ECHOKE',
                'FLUSHO', 'TIOCM_DSR', 'CQUIT', 'B150', 'ISTRIP', 'TIOCSPGRP',
                'TIOCSSIZE', 'VWERASE', 'TIOCMSET', 'TIOCM_CTS', 'CRDLY',
                'ECHOE', 'TCIOFLUSH', 'TAB2', 'VTIME', 'CSTOPB', 'IXANY',
                'VKILL', 'B200', 'TIOCSTI', 'FFDLY', 'CWERASE', 'VREPRINT',
                'INPCK', 'TIOCM_SR', 'VSUSP', 'CSTART', 'B57600', 'NLDLY',
                'TCOOFF', 'ONLCR', 'B9600', 'BSDLY', 'CR3', 'B1200', 'CS5',
                'VT1', 'TABDLY', 'CEOF', 'TIOCM_ST', 'VQUIT', 'IXOFF', 'FF1',
                'OFDEL', 'B2400', 'TIOCM_RI', 'ECHOK', 'TIOCM_CD',
                'TIOCPKT_START', 'CRPRNT', 'CR2', 'HUPCL', 'IGNCR', 'OCRNL',
                'B230400', 'CS6', 'NL0', 'CLNEXT', 'ECHO', 'VEOL', 'VDISCARD',
                'B38400', 'FIONCLEX', 'TAB3', 'TCION', 'IMAXBEL', 'FIONBIO',
                'B115200', 'TIOCM_DTR', 'IEXTEN', 'NCCS', 'TIOCGSIZE',
                'TIOCCONS', 'TIOCPKT_STOP', 'CFLUSH', 'ICANON', 'CINTR', 'B75',
                'IGNPAR', 'ECHOCTL', 'TCOON', 'FF0', 'IGNBRK', 'PENDIN',
                'OPOST', 'TIOCPKT_NOSTOP', 'B300', 'CLOCAL', 'PARENB', 'CEOT',
                'TIOCEXCL', 'ONLRET', 'FIOASYNC', 'VERASE', 'TIOCM_RTS',
                'IXON', 'CR0', 'PARMRK', 'TIOCPKT_FLUSHREAD', 'TIOCM_RNG',
                'ECHOPRT', 'TIOCNOTTY', 'CKILL', 'CDSUSP', 'CR1', 'TIOCGPGRP',
                'CSTOP', 'VMIN', 'CSUSP', 'TOSTOP', 'CS8', 'B0', 'VEOL2',
                'ISIG', 'B50', 'PARODD', 'BS0', 'TIOCSWINSZ', 'TCIOFF',
                'TIOCOUTQ', 'VSTOP', 'NOFLSH', 'CEOL', 'B19200', 'TIOCMBIC',
                'TIOCNXCL', 'B600', 'BRKINT', 'CERASE', 'TIOCMGET', 'OFILL',
                'NL1', 'B1800', 'CREAD', 'EXTA', 'TAB0', 'TIOCSETD', 'VEOF',
                'TIOCM_CAR', 'FIONREAD', 'TCIFLUSH', 'TCSASOFT', 'ECHONL',
                'TCOFLUSH', 'TIOCPKT_DOSTOP', 'VLNEXT', 'VSTART', 'B134',
                'BS1', 'FIOCLEX', 'ICRNL', 'B110', 'TIOCPKT_FLUSHWRITE',
                'TIOCPKT_DATA', 'CS7', 'TAB1', 'TIOCMBIS', 'TIOCGETD',
                'INLCR', 'TIOCGWINSZ', 'EXTB', 'TIOCM_LE', 'ONOCR', 'VTDLY',
                'TIOCPKT', 'VT0',},
    # Relies heavily on Tk docs, so most stuff isn't supposed to be documented here.
    "tkinter": IGNORE_MODULE,

    # Known aliases
    "logging": {"FATAL", "WARN", "fatal",}
    }

# os is where the platform-specific OS stuff is documented.
OK_MISSING["posix"] = set(os.__all__)
OK_MISSING["os.path"] = set(os.__all__)

# don't expect tokenize to document all the token module constants it sucks in.
OK_MISSING["tokenize"] = get_symbol_patterns("token")

OK_MISSING["select"] = get_symbol_patterns("select", "POLL")
OK_MISSING["sqlite3"] = get_symbol_patterns("sqlite3", "SQLITE_")
OK_MISSING["socket"] = get_symbol_patterns("socket",
                         "(SO|MSG|SOL|SCM|IPPROTO|IPPORT|INADDR|IP|IPV6|AF"
                         "|EAI|AI|NI|TCP|SOL_CAN|CAN|PACKET|RDS|ALG|RCVALL|TIPC)_"
                         "|(VMADDR|SO_VM)")
OK_MISSING["socket"] |= {"SHUT_RD", "SHUT_WR", "SHUT_RDWR",
                         "SYSPROTO_CONTROL", "AddressFamily", "SocketKind",
                         "PF_SYSTEM", "dup",}
OK_MISSING["ssl"] |= get_symbol_patterns("ssl", "(ALERT_DESCRIPTION|SSL_ERROR)_")
OK_MISSING["curses"] = get_symbol_patterns("curses", "(KEY|BUTTON[1-4])_")

if __name__ == "__main__":
    sys.exit(main())
