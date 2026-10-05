#!/usr/bin/env python3
"""Mechanical facts for the cpp-architecture-audit skill.

Lists and aggregates, without interpretation: C/C++ files, build files, targets and options,
examples, tooling and embedded markers, #include / import directives, conditional
compilation, TODO markers, git history.
It is neither a linter nor a static analyzer.

  python arch_facts.py inventory [--root R] [--depth 2] [--exclude X]... [--out F]
  python arch_facts.py graph [--root R] [--partition F] [--module NAME=PATH[,PATH]]...
                             [--depth 1] [--exclude X]... [--tests-module tests]
                             [--big-module-kb 250] [--churn-months 12]
                             [--examples 1] [--top 5] [--todo-examples 5] [--out F]

--exclude      : folder or file name pattern (e.g. third_party, *.pb.h)
                 or path relative to the root (e.g. src/legacy).
--partition    : one line per module, "name: path, path" (# = comment).
                 Without a partition, a module = a folder at depth --depth.
--tests-module : module whose includes are kept out of the graph and reported separately.
"""

import argparse
import bisect
import collections
import datetime
import fnmatch
import itertools
import os
import posixpath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

INTERFACE_EXT = {".h", ".hh", ".hpp", ".hxx", ".h++", ".inl", ".ipp", ".tpp", ".tcc", ".txx",
                 ".ixx", ".cppm", ".ccm", ".cxxm", ".c++m", ".mpp", ".cuh"}
IMPL_EXT = {".c", ".cc", ".cpp", ".cxx", ".c++", ".cp", ".mm", ".cu"}

# Lowercase pattern: case-insensitive; pattern with uppercase letters: case-sensitive.
GENERATED_FILES = ["moc_*", "*.moc", "ui_*.h", "qrc_*", "*.pb.h", "*.pb.cc", "*.grpc.pb.h",
                   "*.grpc.pb.cc", "*_generated.h", "*.capnp.h", "*.capnp.c++"]

# Walk without git: folders always skipped, and folders skipped only if they contain build
# artifacts (a "debug" or "win32" folder may contain source code).
ALWAYS_SKIPPED_DIRS = [".git", ".svn", ".hg", ".vs", ".vscode", ".idea", ".cache", ".ccls-cache",
                       ".clangd", ".architecture-audit", "node_modules", "__pycache__", "venv",
                       ".venv", "cmake-build-*", "_deps", "cmakefiles", "*_autogen",
                       "vcpkg_installed", "ipch"]
BUILD_OUTPUT_DIRS = ["build", "build-*", "build_*", "builds", "_build", "out", "bin", "obj",
                     "debug", "release", "relwithdebinfo", "minsizerel", "x64", "x86", "win32",
                     "arm64"]
BUILD_MARKERS = ["cmakecache.txt", "build.ninja", ".ninja_log", ".ninja_deps", ".qmake.stash",
                 "cmakefiles", "*.o", "*.obj", "*.pdb", "*.ilk", "*.tlog", "*.lastbuildstate",
                 "*.idb", "*.pch", "*.gch"]

BUILD_SYSTEMS = [
    ("CMake", ["cmakelists.txt", "*.cmake", "cmakepresets.json", "cmakeuserpresets.json"]),
    ("qmake", ["*.pro", "*.pri", "*.prf"]),
    ("Qbs", ["*.qbs"]),
    ("MSBuild / Visual Studio", ["*.sln", "*.slnx", "*.vcxproj", "*.vcxitems", "*.props",
                                 "*.targets", "*.vcproj"]),
    ("Meson", ["meson.build", "meson_options.txt", "meson.options"]),
    ("Bazel", ["BUILD", "BUILD.bazel", "WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel", "*.bzl"]),
    ("Make / Autotools", ["makefile", "gnumakefile", "*.mk", "*.mak", "makefile.am",
                          "makefile.in", "configure.ac", "configure.in"]),
    ("SCons", ["sconstruct", "sconscript"]),
    ("Premake", ["premake*.lua"]),
    ("xmake", ["xmake.lua"]),
    ("Boost.Build (b2)", ["jamroot", "jamfile", "jamroot.jam", "jamfile.jam", "jamfile.v2"]),
    ("waf", ["wscript"]),
    ("build2", ["buildfile"]),
    ("Ninja (versioned)", ["*.ninja"]),
    ("Code::Blocks", ["*.cbp"]),
    ("IDE / embedded toolchains", ["*.ewp", "*.eww", "*.uvprojx", "*.uvproj", ".cproject",
                                   "*.cproj", "*.atsln", "platformio.ini", "*.ioc"]),
    ("Linker scripts", ["*.ld", "*.lds", "*.icf", "*.sct", "*.scf"]),
]
DEPENDENCY_MANAGERS = [
    ("vcpkg", ["vcpkg.json", "vcpkg-configuration.json"]),
    ("Conan", ["conanfile.txt", "conanfile.py"]),
    ("Git submodules", [".gitmodules"]),
    ("NuGet", ["packages.config"]),
    ("CPM", ["cpm.cmake", "get_cpm.cmake"]),
]
CONTRACTS = [("Protobuf", ["*.proto"]), ("FlatBuffers", ["*.fbs"]), ("IDL", ["*.idl"]),
             ("Cap'n Proto", ["*.capnp"]), ("Thrift", ["*.thrift"]),
             ("Qt Designer", ["*.ui"]), ("QML", ["*.qml"]), ("Qt resources", ["*.qrc"])]
CI_FILES = [".gitlab-ci.yml", "jenkinsfile", "azure-pipelines.yml", ".travis.yml",
            "appveyor.yml", "bitbucket-pipelines.yml", ".drone.yml"]
CI_DIRS = [".github/workflows/", ".circleci/", ".gitlab/"]
DOC_DIRS = {"doc", "docs", "documentation", "adr", "adrs", "architecture", "design"}
DOC_FILES = ["readme*", "architecture*", "contributing*", "design*", "doxyfile*"]
TEST_DIRS = {"test", "tests", "testing", "unittest", "unittests", "unit_tests", "unit-tests", "tst"}
EXAMPLE_DIRS = {"example", "examples", "sample", "samples", "demo", "demos", "tutorial", "tutorials"}
TOOLING = [("Formatting", [".clang-format", "_clang-format", ".editorconfig", ".cmake-format*", ".gersemirc"]),
           ("Lint and static checks", [".clang-tidy", ".cppcheck*", ".pre-commit-config.yaml"]),
           ("Coverage", ["codecov.yml", ".codecov.yml", "gcovr.cfg", ".gcovr.cfg", "*coverage*.cmake"]),
           ("API documentation", ["doxyfile*", "mkdocs.yml", "conf.py", "conf.py.in"]),
           ("Diagram sources", ["*.puml", "*.plantuml", "*.uml", "*.mmd", "*.drawio"]),
           ("Contribution", ["contributing*", "codeowners", "pull_request_template*",
                             "merge_request_template*"])]
SCRIPT_FILES = ["*.sh", "*.bash", "*.bat", "*.cmd", "*.ps1", "*.py"]
SCRIPT_DIRS = {"script", "scripts", "tools", "ci", "build-scripts", "build_scripts"}
EMBEDDED_MARKERS = [("Startup code", ["startup*.s", "startup*.asm"]),
                    ("RTOS configuration", ["freertosconfig.h", "prj.conf", "rtconfig.h", "tx_user.h",
                                            "chconf.h", "rtx_config.h"]),
                    ("Device description", ["*.svd", "*.dts", "*.dtsi"]),
                    ("Interrupt handler files", ["*_it.c", "*_it.cpp", "*_isr.c", "*_isr.cpp"])]
MAX_OPTIONS = 60
VENDOR_DIRS = {"third_party", "thirdparty", "third-party", "3rdparty", "3rd_party", "3rd-party",
               "external", "externals", "extern", "vendor", "vendors", "deps", "contrib",
               "submodules"}

STD_HEADERS = set("""algorithm any array atomic barrier bit bitset charconv chrono codecvt compare
complex concepts condition_variable contracts coroutine debugging deque exception execution
expected filesystem flat_map flat_set format forward_list fstream functional future generator
hazard_pointer hive initializer_list inplace_vector iomanip ios iosfwd iostream istream iterator
latch limits linalg list locale map mdspan memory memory_resource meta mutex new numbers numeric
optional ostream print queue random ranges ratio rcu regex scoped_allocator semaphore set
shared_mutex simd source_location span spanstream sstream stack stacktrace stdexcept stdfloat
stop_token streambuf string string_view strstream syncstream system_error text_encoding thread
tuple type_traits typeindex typeinfo unordered_map unordered_set utility valarray variant vector
version cassert ccomplex cctype cerrno cfenv cfloat cinttypes ciso646 climits clocale cmath
csetjmp csignal cstdalign cstdarg cstdbool cstddef cstdint cstdio cstdlib cstring ctgmath ctime
cuchar cwchar cwctype assert.h complex.h ctype.h errno.h fenv.h float.h inttypes.h iso646.h
limits.h locale.h math.h setjmp.h signal.h stdalign.h stdarg.h stdatomic.h stdbit.h stdbool.h
stdckdint.h stddef.h stdint.h stdio.h stdlib.h stdnoreturn.h string.h tgmath.h threads.h time.h
uchar.h wchar.h wctype.h""".split())
SYSTEM_HEADERS = set("""windows.h windef.h winbase.h winuser.h winsock.h winsock2.h ws2tcpip.h
winerror.h winioctl.h tchar.h shlobj.h shlwapi.h objbase.h comdef.h atlbase.h crtdbg.h sal.h
process.h io.h direct.h conio.h malloc.h mmsystem.h setupapi.h intrin.h immintrin.h xmmintrin.h
emmintrin.h pmmintrin.h smmintrin.h nmmintrin.h arm_neon.h unistd.h pthread.h fcntl.h dlfcn.h
poll.h termios.h dirent.h semaphore.h syslog.h netdb.h sched.h strings.h libgen.h pwd.h grp.h
glob.h fnmatch.h spawn.h""".split())
STD_OR_SYSTEM_HEADERS = STD_HEADERS | SYSTEM_HEADERS
SYSTEM_PREFIXES = {"sys", "arpa", "netinet", "net", "linux", "asm", "mach", "machine", "bits"}
COND_IGNORED = {"defined", "__has_include", "__has_include_next", "__has_cpp_attribute",
                "__has_builtin", "__has_feature", "__has_attribute", "true", "false", "and", "or",
                "not", "bitand", "bitor", "xor", "compl", "not_eq"}
COND_NOISE = {"__cplusplus"}  # C / C++ switch, unrelated to variability

INCLUDE_RE = re.compile(r'^\s*#\s*include(?:_next)?\s*([<"])([^>"\r\n]+)[>"]')
MODULE_DECL_RE = re.compile(r'^\s*(export\s+)?module\s+([A-Za-z_][\w.]*)\s*(?::\s*([A-Za-z_][\w.]*))?\s*;')
IMPORT_HEADER_RE = re.compile(r'^\s*(?:export\s+)?import\s*([<"])([^>"\r\n]+)[>"]\s*;')
IMPORT_RE = re.compile(r'^\s*(?:export\s+)?import\s+([A-Za-z_][\w.]*)?\s*(?::\s*([A-Za-z_][\w.]*))?\s*;')
COND_RE = re.compile(r'^\s*#\s*(ifdef|ifndef|if|elifdef|elifndef|elif)\b(.*)')
DEFINE_RE = re.compile(r'^\s*#\s*define\s+([A-Za-z_]\w*)')
GUARD_IF_RE = re.compile(r'^!\s*defined\s*\(?\s*([A-Za-z_]\w*)\s*\)?$')
GUARD_NAME_RE = re.compile(r'_(?:H|HH|HPP|HXX|INL|INCLUDED)_*$', re.IGNORECASE)
TODO_RE = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b')
IDENT_RE = re.compile(r'(?<![\w.])[A-Za-z_]\w*')  # excludes 0x1F, 1UL…

CMAKE_TARGET_COMMANDS = {"add_library": "lib", "add_executable": "exe", "qt_add_library": "lib",
                         "qt6_add_library": "lib", "qt_add_executable": "exe",
                         "qt6_add_executable": "exe", "qt_add_plugin": "plugin",
                         "qt6_add_plugin": "plugin", "cuda_add_library": "lib",
                         "cuda_add_executable": "exe"}
CMAKE_LIBRARY_TYPES = {"STATIC": "static library", "SHARED": "shared library",
                       "MODULE": "loadable module", "OBJECT": "object library",
                       "INTERFACE": "header-only library (INTERFACE)"}
CMAKE_VISIBILITY = {"PUBLIC": "PUBLIC", "PRIVATE": "PRIVATE", "INTERFACE": "INTERFACE",
                    "LINK_PUBLIC": "PUBLIC", "LINK_PRIVATE": "PRIVATE",
                    "LINK_INTERFACE_LIBRARIES": "INTERFACE"}
CMAKE_LEX_RE = re.compile(r'"(?:\\.|[^"\\])*"|#\[(=*)\[.*?\]\1\]|#[^\n]*', re.S)
CMAKE_COMMAND_RE = re.compile(r'\b([A-Za-z_]\w*)\s*\(')
CMAKE_ARG_RE = re.compile(r'"(?:\\.|[^"\\])*"|[^\s"()]+')
MSBUILD_TYPES = {"Application": "executable", "DynamicLibrary": "shared library",
                 "StaticLibrary": "static library", "Utility": "utility",
                 "Makefile": "Makefile project"}
MSBUILD_DEFAULT_LIBS = set("""kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib
advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib""".split())
QMAKE_RE = re.compile(r'^\s*(?:[\w!:|.*+-]+\s*:\s*)?(TEMPLATE|TARGET|CONFIG|QT|LIBS|SUBDIRS)'
                      r'\s*([-+*~]?=)\s*(.*)$')
MAX_TARGETS = 150

UNASSIGNED = "(outside partition)"
# Default pathspecs: "*" also matches "/", so the reports are excluded at any depth.
AUDIT_FILES = [":(exclude).architecture-audit", ":(exclude)*architecture-analysis*.md",
               ":(exclude)*architecture-prioritized-issues*.md"]


# --- utilities -------------------------------------------------------------------------------

_COMPILED = {}


def match_any(name, patterns):
    key = tuple(patterns)
    regexes = _COMPILED.get(key)
    if regexes is None:
        insensitive = [fnmatch.translate(p) for p in patterns if p == p.lower()]
        sensitive = [fnmatch.translate(p) for p in patterns if p != p.lower()]
        regexes = _COMPILED[key] = tuple(re.compile("|".join(r)) if r else None
                                         for r in (insensitive, sensitive))
    insensitive, sensitive = regexes
    return bool((insensitive and insensitive.match(name.lower())) or (sensitive and sensitive.match(name)))


def norm_rel(path):
    p = path.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    p = p.strip("/")
    return "" if p == "." else p


def basename(rel):
    return rel.rsplit("/", 1)[-1]


def cpp_kind(rel):
    name = basename(rel)
    dot = name.rfind(".")
    if dot <= 0:
        return None
    ext = name[dot:].lower()
    if ext in INTERFACE_EXT:
        return "I"
    if ext in IMPL_EXT:
        return "C"
    return None


def is_generated(name):
    return match_any(name, GENERATED_FILES)


def under(rel, roots):
    return any(rel == r or rel.startswith(r + "/") for r in roots)


def shorten(items, limit):
    items = list(items)
    text = ", ".join(items[:limit])
    return text + (" …(+%d)" % (len(items) - limit) if len(items) > limit else "")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def kb(size):
    return int(round(size / 1024.0))


def strip_comment(text):
    return text.split("//", 1)[0].split("/*", 1)[0].strip()


def run_git(root, args, timeout=300):
    try:
        res = subprocess.run(["git", "-C", root] + args, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    return res.stdout.decode("utf-8", errors="replace")


def git_state(root):
    sha = run_git(root, ["rev-parse", "HEAD"])
    if sha is None:
        return "unversioned repository"
    status = run_git(root, ["--no-optional-locks", "status", "--porcelain", "--", "."] + AUDIT_FILES) or ""
    lines = [l for l in status.splitlines() if l.strip()]
    untracked = sum(1 for l in lines if l.startswith("??"))
    branch = (run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "?").strip()
    if lines:
        tree = "modified (%d tracked, %d untracked, audit files excluded)" % (len(lines) - untracked, untracked)
    else:
        tree = "clean"
    return "commit %s, branch %s, tree %s" % (sha.strip(), branch, tree)


def list_files(root, excludes):
    out = run_git(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if out is not None:
        files = sorted(set(f for f in out.split("\0") if f))
        origin = "git ls-files (tracked or not ignored files)"
    else:
        files = walk_files(root)
        origin = "disk walk (build folders skipped)"
    return [f for f in files if not is_excluded(f, excludes)], origin


def is_excluded(rel, excludes):
    low = rel.lower()
    parts = rel.split("/")
    for ex in excludes:
        if "/" in ex:
            e = ex.lower()
            if low == e or low.startswith(e + "/"):
                return True
        elif any(match_any(part, [ex]) for part in parts):
            return True
    return False


def has_build_markers(path, depth=1):
    try:
        entries = list(os.scandir(path))
    except OSError:
        return False
    if any(match_any(e.name, BUILD_MARKERS) for e in entries):
        return True
    return depth > 0 and any(e.is_dir(follow_symlinks=False) and has_build_markers(e.path, depth - 1)
                             for e in entries)


def walk_files(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        kept = []
        for d in dirnames:
            if match_any(d, ALWAYS_SKIPPED_DIRS):
                continue
            if match_any(d, BUILD_OUTPUT_DIRS) and has_build_markers(os.path.join(dirpath, d)):
                continue
            kept.append(d)
        dirnames[:] = kept
        rel = os.path.relpath(dirpath, root).replace(os.sep, "/")
        prefix = "" if rel == "." else rel + "/"
        files.extend(prefix + f for f in filenames)
    return sorted(files)


def emit(lines, out, summary):
    text = "\n".join(lines) + "\n"
    if not out:
        sys.stdout.write(text)
        return
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("Written: %s — %s" % (out, summary))


# --- build targets ---------------------------------------------------------------------------

def cmake_commands(text, wanted):
    """(name, arguments, line) of the requested CMake commands, comments removed."""
    text = CMAKE_LEX_RE.sub(lambda m: m.group(0) if m.group(0).startswith('"')
                            else re.sub(r"[^\n]", " ", m.group(0)), text)
    newlines = [m.start() for m in re.finditer("\n", text)]
    for m in CMAKE_COMMAND_RE.finditer(text):
        name = m.group(1).lower()
        if name not in wanted:
            continue
        depth, i, quoted = 1, m.end(), False
        while i < len(text) and depth:
            c = text[i]
            if quoted:
                if c == "\\":
                    i += 1
                elif c == '"':
                    quoted = False
            elif c == '"':
                quoted = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        args = [a.strip('"') for a in CMAKE_ARG_RE.findall(text[m.end():i - 1])]
        yield name, args, bisect.bisect_left(newlines, m.start()) + 1


def cmake_targets(root, files):
    paths = sorted((f for f in files if basename(f).lower() == "cmakelists.txt" or f.lower().endswith(".cmake")),
                   key=lambda f: (f.count("/"), f))
    wanted = set(CMAKE_TARGET_COMMANDS) | {"project", "target_link_libraries"}
    parsed, projects = [], {}
    for f in paths:
        text = read_text(os.path.join(root, f))
        if text is None:
            continue
        folder = f.rsplit("/", 1)[0] if "/" in f else ""
        commands = list(cmake_commands(text, wanted))
        parsed.append((f, folder, commands))
        for name, args, _ in commands:
            if name == "project" and args:
                projects.setdefault(folder, args[0])

    def resolve(value, folder):
        if "${" not in value:
            return value
        while folder not in projects and folder:
            folder = folder.rsplit("/", 1)[0] if "/" in folder else ""
        if folder in projects:
            value = value.replace("${PROJECT_NAME}", projects[folder])
        return value.replace("${CMAKE_PROJECT_NAME}", projects.get("", "${CMAKE_PROJECT_NAME}"))

    targets, links, aliases, imported = [], collections.defaultdict(dict), [], []
    for f, folder, commands in parsed:
        for name, args, line in commands:
            if not args or name == "project":
                continue
            target = resolve(args[0], folder)
            if name == "target_link_libraries":
                visibility = "no visibility"
                for a in args[1:]:
                    if a in CMAKE_VISIBILITY:
                        visibility = CMAKE_VISIBILITY[a]
                    elif a not in ("debug", "optimized", "general"):
                        links[target].setdefault(visibility, []).append(resolve(a, folder))
                continue
            flags = [a.upper() for a in args[1:4]]
            if "ALIAS" in flags:
                k = flags.index("ALIAS") + 2
                aliases.append("%s -> %s" % (target, resolve(args[k], folder) if k < len(args) else "?"))
            elif "IMPORTED" in flags:
                imported.append(target)
            else:
                kind = CMAKE_TARGET_COMMANDS[name]
                label = {"exe": "executable", "plugin": "Qt plugin"}.get(kind) or next(
                    (CMAKE_LIBRARY_TYPES[a] for a in flags if a in CMAKE_LIBRARY_TYPES),
                    "library (static or shared per BUILD_SHARED_LIBS)")
                targets.append((target, label, "%s:%d" % (f, line)))

    lines = []
    for target, label, where in targets[:MAX_TARGETS]:
        deps = "; ".join("%s: %s" % (v, shorten(dict.fromkeys(items), 10))
                         for v, items in links.get(target, {}).items())
        lines.append("- %s — %s — %s%s" % (target, label, where, "; " + deps if deps else ""))
    if len(targets) > MAX_TARGETS:
        lines.append("- … %d more targets" % (len(targets) - MAX_TARGETS))
    declared = {t for t, _, _ in targets}
    orphans = sorted(t for t in links if t not in declared)
    if aliases:
        lines.append("- Aliases: " + shorten(aliases, 15))
    if imported:
        lines.append("- Imported (external) targets: " + shorten(dict.fromkeys(imported), 15))
    if orphans:
        lines.append("- target_link_libraries on targets not declared here (function, macro or variable?): "
                     + shorten(orphans, 15))
    return lines


def msbuild_targets(root, files):
    lines = []
    for f in sorted(x for x in files if x.lower().endswith(".vcxproj"))[:MAX_TARGETS]:
        try:
            elements = list(ET.parse(os.path.join(root, f)).getroot().iter())
        except (ET.ParseError, OSError):
            lines.append("- %s — unreadable" % f)
            continue
        name, types, refs, libs = None, [], [], []
        for el in elements:
            tag, text = el.tag.rsplit("}", 1)[-1], (el.text or "").strip()
            if tag == "ProjectName" and text:
                name = text
            elif tag == "ConfigurationType" and text:
                types.append(MSBUILD_TYPES.get(text, text))
            elif tag == "ProjectReference" and el.get("Include"):
                refs.append(basename(el.get("Include").replace("\\", "/")).rsplit(".", 1)[0])
            elif tag == "AdditionalDependencies" and text:
                libs += [x.strip() for x in text.split(";") if x.strip() and not x.strip().startswith("%(")
                         and x.strip().lower() not in MSBUILD_DEFAULT_LIBS]
        details = "".join("; %s: %s" % (k, shorten(dict.fromkeys(v), 10))
                          for k, v in (("references", refs), ("libraries", libs)) if v)
        lines.append("- %s — %s — %s%s" % (name or basename(f).rsplit(".", 1)[0],
                                            " / ".join(dict.fromkeys(types)) or "type not declared", f, details))
    return lines


def qmake_targets(root, files):
    lines = []
    for f in sorted(x for x in files if x.lower().endswith(".pro"))[:MAX_TARGETS]:
        text = read_text(os.path.join(root, f))
        if text is None:
            continue
        values = collections.defaultdict(list)
        for line in re.sub(r"\\[ \t]*\r?\n", " ", text).splitlines():
            m = QMAKE_RE.match(line.split("#", 1)[0])
            if not m:
                continue
            var, op, items = m.group(1), m.group(2), m.group(3).split()
            if op == "=":
                values[var] = items
            elif op in ("+=", "*="):
                values[var] += items
            elif op == "-=":
                values[var] = [x for x in values[var] if x not in items]
        template = (values["TEMPLATE"] or ["app"])[0]
        config = set(values["CONFIG"])
        if template == "lib":
            label = ("plugin" if "plugin" in config else
                     "static library" if config & {"staticlib", "static"} else "shared library")
        else:
            label = {"app": "executable", "subdirs": "aggregating project (subdirs)"}.get(template, template)
        name = (values["TARGET"] or [basename(f).rsplit(".", 1)[0]])[0]
        details = "".join("; %s: %s" % (k, shorten(dict.fromkeys(values[k]), 10))
                          for k in ("QT", "LIBS", "SUBDIRS") if values[k])
        lines.append("- %s — %s — %s%s" % (name, label, f, details))
    return lines


def build_targets(root, files):
    return cmake_targets(root, files) + msbuild_targets(root, files) + qmake_targets(root, files)


def cmake_options(root, files):
    """Build options (option, cmake_dependent_option: name, default, help, location) and
    documentation generation declared in CMake (doxygen_add_docs, find_package(Doxygen|Sphinx))."""
    paths = sorted((f for f in files if basename(f).lower() == "cmakelists.txt" or f.lower().endswith(".cmake")),
                   key=lambda f: (f.count("/"), f))
    wanted = {"option", "cmake_dependent_option", "doxygen_add_docs", "find_package"}
    options, docs = [], []
    for f in paths:
        text = read_text(os.path.join(root, f))
        if text is None:
            continue
        for name, args, line in cmake_commands(text, wanted):
            if not args:
                continue
            if name == "doxygen_add_docs" or (name == "find_package" and args[0].lower() in ("doxygen", "sphinx")):
                docs.append("%s(%s) — %s:%d" % (name, args[0], f, line))
            elif name != "find_package":
                # A literal empty string is shown as "": option(X OFF "") swaps help and default.
                shown = [a or '""' for a in args]
                default = shown[2] if len(args) > 2 else "OFF"
                if name == "cmake_dependent_option" and len(args) > 4:
                    default += " if %s, otherwise forced to %s" % (shown[3], shown[4])
                options.append("- %s = %s — %s — %s:%d" % (args[0], default, shown[1] if len(args) > 1 else "",
                                                             f, line))
    if len(options) > MAX_OPTIONS:
        options = options[:MAX_OPTIONS] + ["- … %d more options" % (len(options) - MAX_OPTIONS)]
    return options, docs


# --- inventory -------------------------------------------------------------------------------

def read_submodules(root):
    paths = []
    text = read_text(os.path.join(root, ".gitmodules"))
    for line in (text or "").splitlines():
        m = re.match(r"\s*path\s*=\s*(.+?)\s*$", line)
        if m:
            paths.append(norm_rel(m.group(1)))
    return paths


def dirs_named(files, names):
    """Folders whose name belongs to names, with the number of files they contain."""
    found = collections.Counter()
    for f in files:
        parts = f.split("/")
        for i, part in enumerate(parts[:-1]):
            if part.lower() in names:
                found["/".join(parts[:i + 1])] += 1
                break
    return found


def inventory(args):
    root = os.path.abspath(args.root)
    excludes = [norm_rel(e) for e in args.exclude]
    files, origin = list_files(root, excludes)
    submodules = read_submodules(root)
    vendor = dict(dirs_named(files, VENDOR_DIRS))
    for s in submodules:
        vendor.setdefault(s, 0)
    vendor_roots = list(vendor)

    cpp = [(f, cpp_kind(f)) for f in files if cpp_kind(f)]
    generated = [f for f, _ in cpp if is_generated(basename(f))]
    own = [(f, k) for f, k in cpp if not is_generated(basename(f)) and not under(f, vendor_roots)]
    n_int = sum(1 for _, k in own if k == "I")

    lines = ["# Inventory — %s" % root, "",
             "- Git: %s" % git_state(root),
             "- Date: %s" % datetime.date.today().isoformat(),
             "- Files listed via: %s" % origin]
    if excludes:
        lines.append("- Requested exclusions: %s" % ", ".join(excludes))

    per_dir = collections.defaultdict(lambda: [0, 0, 0])  # interfaces, implementations, interface bytes
    for f, k in own:
        parts = f.split("/")
        entry = per_dir["/".join(parts[:min(args.depth, len(parts) - 1)]) or "."]
        if k == "I":
            entry[0] += 1
            entry[2] += file_size(os.path.join(root, f))
        else:
            entry[1] += 1
    lines += ["", "## Project C/C++ files (excluding candidate third-party and generated code)",
              "Total: %d (interfaces %d, %d KB; implementations %d)"
              % (len(own), n_int, kb(sum(v[2] for v in per_dir.values())), len(own) - n_int), ""]
    rows = sorted(per_dir.items())
    hidden = []
    if len(rows) > 80:
        biggest = set(k for k, _ in sorted(rows, key=lambda r: -(r[1][0] + r[1][1]))[:80])
        hidden = [r for r in rows if r[0] not in biggest]
        rows = [r for r in rows if r[0] in biggest]
    lines += ["| Folder (depth %d) | Interfaces | Interface KB | Implementations |" % args.depth,
              "|---|---|---|---|"]
    lines += ["| %s | %d | %d | %d |" % (k, i, kb(b), c) for k, (i, c, b) in rows]
    if hidden:
        lines.append("… %d other folders (%d files)" % (len(hidden), sum(v[0] + v[1] for _, v in hidden)))

    def section(title, groups, pool):
        out = []
        for name, patterns in groups:
            hits = sorted((f for f in pool if match_any(basename(f), patterns)),
                          key=lambda f: (f.count("/"), f))
            if hits:
                out.append("- %s: %d file(s) — %s" % (name, len(hits), shorten(hits, 8)))
        return ["", "## " + title] + (out or ["- none"])

    project_files = [f for f in files if not under(f, vendor_roots)]
    lines += section("Build files", BUILD_SYSTEMS, project_files)
    lines += ["", "## Build targets (mechanical extraction: CMake, MSBuild, qmake)"]
    lines += build_targets(root, project_files) or ["- none: other build system, read its files"]
    options, doc_generation = cmake_options(root, project_files)
    lines += ["", "## Build options (CMake option / cmake_dependent_option: name = default — help — location)"]
    lines += options or ["- none"]
    lines += section("Dependency management", DEPENDENCY_MANAGERS, files)

    lines += ["", "## Third-party code (candidates: submodules and folders with a typical name)"]
    if vendor:
        for v in sorted(vendor):
            n = sum(1 for f, _ in cpp if under(f, [v]))
            tag = " (submodule)" if v in submodules else ""
            lines.append("- %s%s: %d C/C++ file(s)%s" % (
                v, tag, n, " — content not listed by git" if tag and n == 0 else ""))
    else:
        lines.append("- none")

    lines += ["", "## Generated code in the source tree",
              "- %d file(s)%s" % (len(generated), (" — " + shorten(generated, 5)) if generated else "")]
    lines += section("Contracts and declarative interfaces", CONTRACTS, project_files)

    tests = dirs_named(project_files, TEST_DIRS)
    lines += ["", "## Tests (candidate folders)"]
    lines += ["- %s: %d file(s)" % (d, n) for d, n in sorted(tests.items())[:15]] or ["- none"]

    examples = dirs_named(project_files, EXAMPLE_DIRS)
    lines += ["", "## Examples and samples (candidate folders)"]
    lines += ["- %s: %d file(s)" % (d, n) for d, n in sorted(examples.items())[:15]] or ["- none"]

    lines += ["", "## Documentation and CI"]
    docs = dirs_named(project_files, DOC_DIRS)
    lines += ["- %s/: %d file(s)" % (d, n) for d, n in sorted(docs.items())[:10]]
    root_docs = [f for f in project_files if "/" not in f and match_any(f, DOC_FILES)]
    root_md = [f for f in project_files if "/" not in f and f.lower().endswith(".md")]
    lines.append("- Root: %s; %d .md file(s)" % (shorten(root_docs, 8) or "no typical document", len(root_md)))
    ci = [f for f in project_files if match_any(basename(f), CI_FILES) or any(f.startswith(d) for d in CI_DIRS)]
    lines.append("- CI: %s" % (shorten(ci, 8) if ci else "no recognized file"))

    lines += section("Conventions and tooling", TOOLING, project_files)
    if doc_generation:
        lines.append("- Documentation generation in CMake: %s" % shorten(doc_generation, 6))
    scripts =[f for f in project_files if match_any(basename(f), SCRIPT_FILES)
               and ("/" not in f or (f.count("/") == 1 and f.split("/")[0].lower() in SCRIPT_DIRS))]
    lines.append("- Scripts (root and script folders): %s" % (shorten(scripts, 10) if scripts else "none"))
    lines += section("Embedded markers (with the linker scripts above)", EMBEDDED_MARKERS, project_files)

    emit(lines, args.out, "%d project C/C++ files" % len(own))


# --- graph -----------------------------------------------------------------------------------

def load_partition(args):
    entries = []
    specs = []
    if args.partition:
        with open(args.partition, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.split("#", 1)[0].strip()
                if line:
                    specs.append((line, ":"))
    specs += [(m, "=") for m in args.module]
    for spec, sep in specs:
        name, found, paths = spec.partition(sep)
        if not found or not name.strip():
            sys.exit("Invalid module (expected 'name%s path, path'): %s" % (sep, spec))
        entries.append((name.strip(), [norm_rel(p) for p in paths.split(",") if p.strip()]))
    return entries


class ModuleMap:
    def __init__(self, entries, depth):
        self.prefixes = sorted(((p.lower(), name) for name, paths in entries for p in paths),
                               key=lambda x: -len(x[0]))
        self.order = list(dict.fromkeys(name for name, _ in entries))
        self.depth = depth
        self.cache = {}

    def __call__(self, rel):
        m = self.cache.get(rel)
        if m is None:
            m = self.cache[rel] = self._compute(rel)
        return m

    def _compute(self, rel):
        if self.prefixes:
            low = rel.lower()
            for p, name in self.prefixes:
                if p == "" or low == p or low.startswith(p + "/"):
                    return name
            return UNASSIGNED
        parts = rel.split("/")
        return "/".join(parts[:min(self.depth, len(parts) - 1)]) or "(root)"


def parse_file(path):
    text = read_text(path)
    if text is None:
        return None
    res = {"includes": [], "imports": [], "import_headers": [], "decl": None,
           "ncond": 0, "conds": collections.Counter(), "todos": []}
    pending_guard = None
    seen_cond = False
    for no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        if pending_guard is not None and not s.startswith(("//", "/*", "*")):
            m = DEFINE_RE.match(s)
            # Include guard: the next line defines the macro, without a value unless it is named like a guard.
            if not (m and m.group(1) == pending_guard
                    and (not strip_comment(s[m.end():]) or GUARD_NAME_RE.search(pending_guard))):
                res["ncond"] += 1
                res["conds"][pending_guard] += 1
            pending_guard = None
        if s.startswith("#"):
            m = INCLUDE_RE.match(s)
            if m:
                res["includes"].append((m.group(1), m.group(2).strip(), no))
            else:
                m = COND_RE.match(s)
                if m:
                    kind, rest = m.group(1), strip_comment(m.group(2))
                    ids = [x for x in IDENT_RE.findall(rest) if x not in COND_IGNORED]
                    guard = None
                    if not seen_cond:  # an include guard can only be the file's first condition
                        if kind == "ifndef" and len(ids) == 1:
                            guard = ids[0]
                        elif kind == "if":
                            g = GUARD_IF_RE.match(rest)
                            guard = g.group(1) if g else None
                    seen_cond = True
                    if guard:
                        pending_guard = guard
                    elif not (ids and set(ids) <= COND_NOISE):
                        res["ncond"] += 1
                        for x in set(ids):
                            res["conds"][x] += 1
        elif s.startswith(("import", "export", "module")):
            m = IMPORT_HEADER_RE.match(s)
            if m:
                res["import_headers"].append((m.group(1), m.group(2).strip(), no))
            else:
                m = MODULE_DECL_RE.match(s)
                if m:
                    if res["decl"] is None:
                        res["decl"] = (bool(m.group(1)), m.group(2), m.group(3), no)
                else:
                    m = IMPORT_RE.match(s)
                    if m and (m.group(1) or m.group(2)):
                        res["imports"].append((m.group(1), m.group(2), no))
        if "TODO" in s or "FIXME" in s or "HACK" in s or "XXX" in s:
            m = TODO_RE.search(s)
            if m:
                res["todos"].append((m.group(1), no, s[:110]))
    if pending_guard is not None:
        res["ncond"] += 1
        res["conds"][pending_guard] += 1
    return res


def common_prefix(a, b):
    n = 0
    for x, y in zip(a.split("/"), b.split("/")):
        if x != y:
            break
        n += 1
    return n


class Resolver:
    """Resolves an include to a repository file: relative to the includer, then by path suffix."""

    def __init__(self, files):
        self.by_lower = {f.lower(): f for f in files}
        self.by_base = collections.defaultdict(list)
        for f in files:
            self.by_base[basename(f).lower()].append(f)

    def resolve(self, src, form, target, modmap):
        t = target.replace("\\", "/").strip()
        while t.startswith("./"):
            t = t[2:]
        if form == "<" and t.lower() in STD_OR_SYSTEM_HEADERS:
            return None, None  # <time.h> never resolves to a project's time.h
        if form == '"':
            d = src.rsplit("/", 1)[0] if "/" in src else ""
            hit = self.by_lower.get(posixpath.normpath(posixpath.join(d, t) if d else t).lower())
            if hit:
                return hit, None
        low = t.lower()
        while low.startswith("../"):
            low = low[3:]
        pool = [f for f in self.by_base.get(basename(low), ())
                if f.lower() == low or f.lower().endswith("/" + low)]
        if not pool:
            return None, None
        if len(pool) == 1:
            return pool[0], None
        same = [f for f in pool if modmap(f) == modmap(src)]
        if len(same) == 1:
            return same[0], None
        pool = sorted(same or pool)
        best = max(pool, key=lambda f: common_prefix(f, src))
        return best, (pool if len({modmap(f) for f in pool}) > 1 else None)


def external_root(target):
    t = target.replace("\\", "/")
    low = t.lower()
    if is_generated(basename(t)):
        return "<generated>"
    if low in STD_HEADERS:
        return "<std>"
    first = t.split("/", 1)[0]
    if low in SYSTEM_HEADERS or ("/" in t and first.lower() in SYSTEM_PREFIXES):
        return "<system>"
    if "/" in t:
        return "Qt" if first.startswith("Qt") or first == "qpa" else first
    if re.match(r"^Q[A-Z]\w*$", t) or re.match(r"^Qt[A-Z]\w*$", t):
        return "Qt"
    stem = t.rsplit(".", 1)[0] if "." in t else t
    m = re.match(r"^[a-z]+\d*", stem) or re.match(r"^[A-Z]+\d*", stem)
    return m.group(0) if m and len(m.group(0)) >= 2 else stem


def tarjan(nodes, succ):
    """Strongly connected components, emitted in reverse topological order (sinks first)."""
    index, low, on_stack, stack, comps = {}, {}, set(), [], []
    counter = 0
    for v in nodes:
        if v in index:
            continue
        index[v] = low[v] = counter
        counter += 1
        stack.append(v)
        on_stack.add(v)
        work = [(v, iter(succ.get(v, ())))]
        while work:
            node, it = work[-1]
            descended = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(succ.get(w, ()))))
                    descended = True
                    break
                if w in on_stack:
                    low[node] = min(low[node], index[w])
            if descended:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                comps.append(comp)
    return comps


def cycle_path(comp, succ):
    nodes = set(comp)
    start = min(comp)
    parent = {}
    queue = collections.deque()
    for w in succ.get(start, ()):
        if w in nodes and w not in parent:
            parent[w] = start
            queue.append(w)
    while queue and start not in parent:
        v = queue.popleft()
        for w in succ.get(v, ()):
            if w in nodes and w not in parent:
                parent[w] = v
                queue.append(w)
    if start not in parent:
        return [start]
    path = [start]
    v = parent[start]
    while v != start:
        path.append(v)
        v = parent[v]
    path.append(start)
    return list(reversed(path))


def churn_lines(root, months, modmap, n_modules, top):
    lines = ["", "## Git history (last %d months, merges excluded)" % months]
    prefix = run_git(root, ["rev-parse", "--show-prefix"])
    log = None if prefix is None else run_git(root, [
        "-c", "core.quotepath=off", "log", "--no-merges", "--since=%d.months.ago" % months,
        "--name-only", "--format=@@@%H", "--", "."])
    if log is None:
        return lines + ["- history unavailable (unversioned repository or git missing)"]
    prefix = prefix.strip()
    commits = []
    for line in log.splitlines():
        if line.startswith("@@@"):
            commits.append([])
        elif line.strip() and commits:
            p = line.strip()
            commits[-1].append(p[len(prefix):] if prefix and p.startswith(prefix) else p)
    max_modules = max(3, n_modules // 2)
    kept, wide = [], 0
    for files in commits:
        mods = {modmap(f) for f in files} - {UNASSIGNED}
        if len(files) > 50 or (n_modules >= 4 and len(mods) > max_modules):
            wide += 1
        else:
            kept.append((files, mods))
    lines.append("- Commits: %d analyzed, %d discarded as too wide (> 50 files or > %d modules)"
                 % (len(kept), wide, max_modules))
    if not kept:
        return lines
    per_commits = collections.Counter()
    per_files = collections.defaultdict(set)
    hot = collections.Counter()
    pairs = collections.Counter()
    for files, mods in kept:
        per_commits.update(mods)
        for f in files:
            m = modmap(f)
            if m != UNASSIGNED:
                per_files[m].add(f)
            if cpp_kind(f):
                hot[f] += 1
        pairs.update(itertools.combinations(sorted(mods), 2))
    lines += ["", "| Module | Commits | Modified files |", "|---|---|---|"]
    lines += ["| %s | %d | %d |" % (m, n, len(per_files[m])) for m, n in per_commits.most_common()]
    if hot:
        lines.append("")
        lines.append("Most modified C/C++ files: " + ", ".join(
            "%s (%d, %s%s)" % (f, n, modmap(f), "" if os.path.exists(os.path.join(root, f)) else ", deleted")
            for f, n in hot.most_common(top * 3)))
    if pairs:
        lines.append("")
        lines.append("Co-changes (shared commits; share of the commits of the less modified module):")
        for (a, b), n in pairs.most_common(10):
            lines.append("- %s + %s: %d (%d %%)" % (a, b, n, round(100 * n / min(per_commits[a], per_commits[b]))))
    return lines


def graph(args):
    root = os.path.abspath(args.root)
    excludes = [norm_rel(e) for e in args.exclude]
    entries = load_partition(args)
    modmap = ModuleMap(entries, args.depth)
    tests_mod = args.tests_module
    files, origin = list_files(root, excludes)
    generated_names = {basename(f).lower() for f in files if cpp_kind(f) and is_generated(basename(f))}
    cfiles = [f for f in files if cpp_kind(f) and not is_generated(basename(f))
              and os.path.isfile(os.path.join(root, f))]
    sizes = {f: file_size(os.path.join(root, f)) for f in cfiles}
    resolver = Resolver(cfiles)
    parsed = {f: parse_file(os.path.join(root, f)) for f in cfiles}

    exported = {}
    for f, p in parsed.items():
        if p and p["decl"] and p["decl"][0]:
            exported.setdefault(p["decl"][1] + (":" + p["decl"][2] if p["decl"][2] else ""), f)

    file_succ = collections.defaultdict(dict)
    mod_edges = collections.Counter()
    from_interfaces = collections.Counter()
    internal = collections.Counter()
    test_includes = collections.defaultdict(collections.Counter)
    mod_examples = collections.defaultdict(list)
    ext_includers = collections.defaultdict(set)
    external = collections.defaultdict(collections.Counter)
    external_samples = collections.defaultdict(list)
    unresolved_quote = collections.defaultdict(collections.Counter)
    pending_quote = []
    angle_roots = set()
    ambiguous = []

    def add_internal(src, dst, line):
        if dst == src:
            return
        file_succ[src].setdefault(dst, line)
        ms, md = modmap(src), modmap(dst)
        if ms == md:
            internal[ms] += 1
        elif ms == tests_mod:
            test_includes[md][dst] += 1
        else:
            ext_includers[dst].add(src)
            mod_edges[(ms, md)] += 1
            if cpp_kind(src) == "I":
                from_interfaces[(ms, md)] += 1
            if len(mod_examples[(ms, md)]) < args.examples:
                mod_examples[(ms, md)].append("%s:%d -> %s" % (src, line, dst))

    def add_external(root_name, module, sample):
        external[root_name][module] += 1
        if sample not in external_samples[root_name] and len(external_samples[root_name]) < 3:
            external_samples[root_name].append(sample)

    def handle_include(src, form, target, line):
        dst, amb = resolver.resolve(src, form, target, modmap)
        if dst:
            add_internal(src, dst, line)
            if amb:
                ambiguous.append((src, line, target, amb, dst))
            return
        name = basename(target.replace("\\", "/")).lower()
        root_name = "<generated>" if name in generated_names else external_root(target)
        if form == "<":
            angle_roots.add(root_name)
            add_external(root_name, modmap(src), target)
        else:
            pending_quote.append((modmap(src), target, root_name))

    for src in cfiles:
        p = parsed[src]
        if p is None:
            continue
        for form, target, line in p["includes"] + p["import_headers"]:
            handle_include(src, form, target, line)
        decl = p["decl"]
        if decl and not decl[0] and not decl[2] and decl[1] in exported:
            add_internal(src, exported[decl[1]], decl[3])  # "module X;" implementation unit
        for name, part, line in p["imports"]:
            key = ((decl[1] if decl else "") + ":" + part) if name is None else name + (":" + part if part else "")
            if key in exported:
                add_internal(src, exported[key], line)
            else:
                add_external("<std>" if key in ("std", "std.compat") else key.split(":")[0].split(".")[0],
                             modmap(src), "import " + key)

    known = angle_roots | {"<std>", "<system>", "Qt", "<generated>"}
    for module, target, root_name in pending_quote:
        if root_name in known:
            add_external(root_name, module, target)
        else:
            unresolved_quote[target.replace("\\", "/")][module] += 1

    counts = collections.defaultdict(lambda: [0, 0, 0])  # interfaces, implementations, interface bytes
    for f in cfiles:
        entry = counts[modmap(f)]
        if cpp_kind(f) == "I":
            entry[0] += 1
            entry[2] += sizes[f]
        else:
            entry[1] += 1
    modules = [m for m in modmap.order if m in counts] + sorted(m for m in counts if m not in modmap.order)
    graph_modules = [m for m in modules if m != tests_mod]
    by_module = collections.defaultdict(list)
    for f in cfiles:
        by_module[modmap(f)].append(f)

    succ_mod = collections.defaultdict(set)
    fan_in, fan_out = collections.defaultdict(set), collections.defaultdict(set)
    inc_in, inc_out = collections.Counter(), collections.Counter()
    for (a, b), n in mod_edges.items():
        succ_mod[a].add(b)
        fan_out[a].add(b)
        fan_in[b].add(a)
        inc_out[a] += n
        inc_in[b] += n
    sccs = tarjan(graph_modules, succ_mod)
    comp_of = {m: i for i, comp in enumerate(sccs) for m in comp}
    level = {}
    for i, comp in enumerate(sccs):
        deps = {comp_of[d] for m in comp for d in succ_mod[m]} - {i}
        level[i] = 1 + max(level[d] for d in deps) if deps else 0
    file_nodes = sorted(set(file_succ) | {d for s in file_succ.values() for d in s})
    file_cycles = sorted((c for c in tarjan(file_nodes, file_succ) if len(c) > 1), key=lambda c: (-len(c), min(c)))

    lines = ["# Mechanical facts — %s" % root, "",
             "- Git: %s" % git_state(root),
             "- Date: %s" % datetime.date.today().isoformat(),
             "- Files listed via: %s; %d C/C++ files analyzed" % (origin, len(cfiles)),
             "- Method: #include directives (<…> and \"…\" forms) and C++20 imports, resolved against the "
             "repository's files (path relative to the includer, then path suffix; a <…> naming a standard "
             "or system header is never resolved to a project file). External roots grouped heuristically. "
             "No interpretation."]
    if excludes:
        lines.append("- Exclusions: %s" % ", ".join(excludes))

    lines += ["", "## Modules", "| Module | Interfaces | Interface KB | Implementations |", "|---|---|---|---|"]
    lines += ["| %s | %d | %d | %d |" % (m, counts[m][0], kb(counts[m][2]), counts[m][1]) for m in modules]
    missing = [p for _, paths in entries for p in paths if p and not os.path.exists(os.path.join(root, p))]
    if missing:
        lines.append("Partition paths not found: " + ", ".join(missing))
    empty = [name for name in modmap.order if name not in counts]
    if empty:
        lines.append("Modules without C/C++ files: " + ", ".join(empty))
    if UNASSIGNED in counts:
        dirs = collections.Counter("/".join(f.split("/")[:2]) for f in by_module[UNASSIGNED])
        lines.append("Files outside the partition, by folder: " + ", ".join("%s (%d)" % d for d in dirs.most_common(10)))

    lines += ["", "## Internal dependencies (module -> module: includes, of which from interface files; example)"]
    if mod_edges:
        ordered = sorted(mod_edges.items(), key=lambda e: (modules.index(e[0][0]), -e[1]))
        for (a, b), n in ordered[:150]:
            lines.append("- %s -> %s: %d (interfaces %d); e.g. %s"
                         % (a, b, n, from_interfaces[(a, b)], " | ".join(mod_examples[(a, b)])))
        if len(ordered) > 150:
            lines.append("- … %d more edges (partition too fine?)" % (len(ordered) - 150))
    else:
        lines.append("- none")

    lines += ["", "## Levels (0 = depends on no other internal module; {…} = modules in a cycle)"]
    by_level = collections.defaultdict(list)
    for i, comp in enumerate(sccs):
        by_level[level[i]].append(("{%s}" % ", ".join(sorted(comp))) if len(comp) > 1 else comp[0])
    lines += ["- L%d: %s" % (lv, ", ".join(sorted(by_level[lv]))) for lv in sorted(by_level)]

    lines += ["", "## Fan-in / fan-out",
              "| Module | Fan-in (modules) | Fan-out (modules) | Incoming includes | Outgoing includes "
              "| Internal includes |", "|---|---|---|---|---|---|"]
    lines += ["| %s | %d | %d | %d | %d | %d |" % (m, len(fan_in[m]), len(fan_out[m]), inc_in[m], inc_out[m],
                                                  internal[m]) for m in graph_modules]

    lines += ["", "## Cycles between modules"]
    module_cycles = [c for c in sccs if len(c) > 1]
    if not module_cycles:
        lines.append("- none")
    for comp in module_cycles:
        members = set(comp)
        edges = ["%s -> %s: %d (e.g. %s)" % (a, b, n, mod_examples[(a, b)][0] if mod_examples[(a, b)] else "?")
                 for (a, b), n in sorted(mod_edges.items()) if a in members and b in members]
        lines.append("- {%s}: %s" % (", ".join(sorted(comp)), "; ".join(edges)))

    lines += ["", "## Cycles between files"]
    if not file_cycles:
        lines.append("- none")
    else:
        lines.append("- %d cyclic component(s)%s:" % (len(file_cycles), " (10 largest)" if len(file_cycles) > 10 else ""))
        for comp in file_cycles[:10]:
            mods = sorted({modmap(f) for f in comp})
            lines.append("  - %d files, modules %s: %s" % (len(comp), ", ".join(mods), " -> ".join(cycle_path(comp, file_succ))))

    lines += ["", "## Effective interface (headers included from other modules; number of including files; "
              "full list above %d KB of interfaces)" % args.big_module_kb]
    for m in graph_modules:
        headers = [f for f in by_module[m] if cpp_kind(f) == "I"]
        if not headers:
            continue
        exposed = sorted((f for f in headers if ext_includers[f]), key=lambda f: (-len(ext_includers[f]), f))
        limit = len(exposed) if counts[m][2] > args.big_module_kb * 1024 else args.top
        rest = len(headers) - len(exposed)
        shown = ", ".join("%s (%d)" % (f, len(ext_includers[f])) for f in exposed[:limit])
        more = " …(+%d)" % (len(exposed) - limit) if len(exposed) > limit else ""
        lines.append("- %s: %s%s; %d header(s) included only from within the module or by no file of the repository"
                     % (m, shown or "none", more, rest))

    lines += ["", "## Includes from the `%s` module (kept out of the sections above)" % tests_mod]
    if tests_mod not in counts:
        lines.append("- no `%s` module in the partition" % tests_mod)
    else:
        for m in graph_modules:
            headers = test_includes.get(m)
            if headers:
                lines.append("- %s: %d include(s) of %d header(s); e.g. %s" % (
                    m, sum(headers.values()), len(headers),
                    shorten(sorted(headers, key=lambda h: (-headers[h], h)), 3)))
        never = [m for m in graph_modules if m not in test_includes and m != UNASSIGNED]
        lines.append("- Modules no test includes: %s" % (", ".join(never) or "none"))

    lines += ["", "## External dependencies (root: modules that include it; examples)"]
    roots = sorted(external, key=lambda r: (-len(external[r]), -sum(external[r].values()), r))
    for r in roots[:60]:
        users = external[r]
        detail = ", ".join("%s %d" % (m, n) for m, n in users.most_common(8))
        if len(users) > 8:
            detail += " …(+%d modules)" % (len(users) - 8)
        lines.append("- %s (%d): %s; e.g. %s" % (r, sum(users.values()), detail, ", ".join(external_samples[r])))
    if len(roots) > 60:
        lines.append("- … %d more roots" % (len(roots) - 60))
    if not roots:
        lines.append("- none")
    if unresolved_quote:
        lines.append("")
        lines.append("Unresolved \"…\" includes (generated, outside the tree or non-standard include paths):")
        for target, users in sorted(unresolved_quote.items(), key=lambda e: -sum(e[1].values()))[:20]:
            lines.append("- %s (%d): %s" % (target, sum(users.values()), ", ".join("%s %d" % u for u in users.most_common(5))))
    if ambiguous:
        lines.append("")
        lines.append("Ambiguous resolutions between modules (chosen file = closest path): %d; examples:" % len(ambiguous))
        for src, line, target, pool, dst in ambiguous[:10]:
            lines.append("- %s:%d \"%s\" -> %s; candidates: %s" % (src, line, target, dst, ", ".join(pool)))

    lines += ["", "## Conditional compilation (excluding include guards and __cplusplus; most tested macros)"]
    any_cond = False
    for m in modules:
        n = sum(parsed[f]["ncond"] for f in by_module[m] if parsed[f])
        if not n:
            continue
        any_cond = True
        macros = collections.Counter()
        for f in by_module[m]:
            if parsed[f]:
                macros.update(parsed[f]["conds"])
        lines.append("- %s: %d directive(s); %s" % (m, n, ", ".join("%s (%d)" % x for x in macros.most_common(6)) or "no macro"))
    if not any_cond:
        lines.append("- none")

    lines += ["", "## TODO / FIXME / HACK / XXX markers"]
    any_todo = False
    budget = 60
    for m in modules:
        todos = [(f, t) for f in by_module[m] if parsed[f] for t in parsed[f]["todos"]]
        if not todos:
            continue
        any_todo = True
        kinds = collections.Counter(t[0] for _, t in todos)
        lines.append("- %s: %s" % (m, ", ".join("%s %d" % k for k in kinds.most_common())))
        shown = todos[:min(args.todo_examples, budget)]
        budget -= len(shown)
        lines += ["  - %s:%d \"%s\"" % (f, t[1], t[2]) for f, t in shown]
    if not any_todo:
        lines.append("- none")

    if args.churn_months > 0:
        lines += churn_lines(root, args.churn_months, modmap, len([m for m in modules if m != UNASSIGNED]), args.top)

    emit(lines, args.out, "%d files, %d modules, %d edges, %d module cycle(s), %d file cycle(s)"
         % (len(cfiles), len(modules), len(mod_edges), len(module_cycles), len(file_cycles)))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Mechanical facts for the C/C++ architecture audit.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="audited folder (default: current folder)")
    common.add_argument("--exclude", action="append", default=[], help="name pattern or relative path to exclude")
    common.add_argument("--out", help="output file (default: standard output)")
    inv = sub.add_parser("inventory", parents=[common], help="repository inventory")
    inv.add_argument("--depth", type=int, default=2, help="depth of the per-folder count")
    gra = sub.add_parser("graph", parents=[common], help="dependencies, cycles, history")
    gra.add_argument("--partition", help="file of 'name: path, path' lines (one per module)")
    gra.add_argument("--module", action="append", default=[], help="NAME=PATH[,PATH]")
    gra.add_argument("--depth", type=int, default=1, help="without a partition: depth of a module")
    gra.add_argument("--tests-module", default="tests", help="test module, kept out of the graph (default: tests)")
    gra.add_argument("--big-module-kb", type=int, default=250,
                     help="above this interface volume, the effective interface is listed in full")
    gra.add_argument("--churn-months", type=int, default=12, help="git history period (0 = disabled)")
    gra.add_argument("--examples", type=int, default=1, help="examples per module -> module edge")
    gra.add_argument("--top", type=int, default=5, help="headers listed per module")
    gra.add_argument("--todo-examples", type=int, default=5, help="markers quoted per module")
    args = parser.parse_args()
    inventory(args) if args.cmd == "inventory" else graph(args)


if __name__ == "__main__":
    main()
