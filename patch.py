import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
TOUCHED_JS = []

# Documents up to this many lines are fully rendered in contenteditable mode.
FULL_RENDER_MAX_LINES = 5000


def fail(label, message):
    print(f"FAIL [{label}]: {message}", file=sys.stderr)
    sys.exit(1)


def apply(label, rel, marker, edits, append=''):
    path = ROOT / rel
    if not path.is_file():
        fail(label, f"file missing: {path}")
    text = path.read_text(encoding='utf-8')
    if rel.endswith('.js') and rel not in TOUCHED_JS:
        TOUCHED_JS.append(rel)
    if marker in text:
        print(f"SKIP [{label}]: already present")
        return
    for old, new in edits:
        if isinstance(old, re.Pattern):
            found = len(old.findall(text))
            if found != 1:
                fail(label, f"regex matched {found}x in {path}: {old.pattern[:80]}")
            text = old.sub(new, text, count=1)
        else:
            found = text.count(old)
            if found != 1:
                fail(label, f"anchor matched {found}x in {path}: {old.strip()[:80]!r}")
            text = text.replace(old, new, 1)
    path.write_text(text + append, encoding='utf-8')
    print(f"OK   [{label}]")


CM_JS = 'src/lib/codemirror/lib/codemirror.js'
CM_CSS = 'src/lib/codemirror/lib/codemirror.css'

# Why this exists: in contenteditable mode (CodeMirror 5 default on Android) the
# IME (Gboard) reads, selects, copies and cuts from the browser's flat text of
# the editable DOM. Gecko builds that text from every text node under the
# editable root and adds a line break before every HTML element that is not an
# inline tag. CodeMirror 5 renders each line as
#   <div wrapper><div gutter><div number>335</div></div><pre>text</pre></div>
# so the clipboard got "\n\n\n335\ntext" for every line. Fix: number rendered
# via CSS generated content (not a text node) and all per-line gutter helper
# elements become <span> (inline tag, no line break). Result: exactly one
# <pre> per line, nothing else with text.

apply(
    'cm5 line number element',
    CM_JS,
    'function lineNumberElt',
    [
        (
            '  function updateLineGutter(cm, lineView, lineN, dims) {',
            '''  function lineNumberElt(cm, n, cls, css) {
    var node = elt("span", null, cls, css);
    node.setAttribute("data-ln", lineNumberFor(cm.options, n));
    return node
  }

  function updateLineGutter(cm, lineView, lineN, dims) {''',
        ),
        (
            'elt("div", lineNumberFor(cm.options, lineN),',
            'lineNumberElt(cm, lineN,',
        ),
        (
            '''          removeChildren(lineView.lineNumber);
          lineView.lineNumber.appendChild(document.createTextNode(lineNumberFor(cm.options, lineN)));''',
            '''          lineView.lineNumber.setAttribute("data-ln", lineNumberFor(cm.options, lineN));''',
        ),
    ],
)

apply(
    'cm5 inline gutter helper elements',
    CM_JS,
    'lineView.node = elt("span"',
    [
        (
            'lineView.node = elt("div", null, null, "position: relative");',
            'lineView.node = elt("span", null, null, "position: relative; display: block");',
        ),
        (
            'wrap.insertBefore(elt("div", null, cls), wrap.firstChild);',
            'wrap.insertBefore(elt("span", null, cls), wrap.firstChild);',
        ),
        (
            'lineView.gutterBackground = elt("div", null, "CodeMirror-gutter-background "',
            'lineView.gutterBackground = elt("span", null, "CodeMirror-gutter-background "',
        ),
        (
            'var gutterWrap = lineView.gutter = elt("div", null, "CodeMirror-gutter-wrapper"',
            'var gutterWrap = lineView.gutter = elt("span", null, "CodeMirror-gutter-wrapper"',
        ),
        (
            'gutterWrap.appendChild(elt("div", [found], "CodeMirror-gutter-elt"',
            'gutterWrap.appendChild(elt("span", [found], "CodeMirror-gutter-elt"',
        ),
    ],
)

apply(
    'cm5 foldgutter marker element',
    'src/lib/codemirror/addon/fold/foldgutter.js',
    'document.createElement("span");\n      elt.className = spec',
    [(
        'document.createElement("div");\n      elt.className = spec',
        'document.createElement("span");\n      elt.className = spec',
    )],
)

apply(
    'cm5 line number css',
    CM_CSS,
    'content: attr(data-ln)',
    [],
    append='''
/* Line numbers are generated content so they never enter the editable text. */
.CodeMirror-linenumber::before {
  content: attr(data-ln);
}
.CodeMirror-gutter-elt > span {
  display: block;
}
''',
)

# uBO lint markers: same problem (nbsp text, message text, div blocks).

LINT_BLOCK = re.compile(r'    const markerTemplates = \{\n.*?\n    \};\n', re.S)


def lint_templates(m):
    block = m.group(0)
    for needle, count in (
        ('<div class="CodeMirror-lintmarker"', 6),
        ("'</div>',", 6),
        ('&nbsp;', 6),
        ('<span class="msg">Mismatched if-endif directive</span>', 2),
    ):
        found = block.count(needle)
        if found != count:
            fail('uBO lint markers', f"expected {count}x {needle!r}, found {found}")
    block = block.replace('<div class="CodeMirror-lintmarker"', '<span class="CodeMirror-lintmarker"')
    block = block.replace("'</div>',", "'</span>',")
    block = block.replace('&nbsp;', '')
    block = block.replace(
        '<span class="msg">Mismatched if-endif directive</span>',
        '<span class="msg" data-msg="Mismatched if-endif directive"></span>',
    )
    return block


apply(
    'uBO lint markers',
    'src/js/codemirror/ubo-static-filtering.js',
    'msgElem.dataset.msg',
    [
        (LINT_BLOCK, lint_templates),
        ('msgElem.textContent = details.msg;', 'msgElem.dataset.msg = details.msg;'),
    ],
)

apply(
    'uBO lint marker css',
    'src/css/codemirror.css',
    'content: attr(data-msg)',
    [],
    append='''
.CodeMirror-lintmarker {
    display: block;
    }
.CodeMirror-lintmarker .msg::before {
    content: attr(data-msg);
    }
''',
)

# With a virtualized viewport only rendered lines exist in the DOM, so an IME
# select-all + copy/cut would only cover the visible slice. Render everything
# for reasonably small documents.

FULL_RENDER_JS = '''  // Mobile IME: render the whole document in contenteditable mode.
  var FULL_RENDER_MAX_LINES = %d;
  CodeMirror.defineInitHook(function (cm) {
    if (cm.options.inputStyle !== "contenteditable") { return }
    var baseMargin = cm.options.viewportMargin;
    var sync = function () {
      cm.setOption("viewportMargin",
                   cm.lineCount() <= FULL_RENDER_MAX_LINES ? Infinity : baseMargin);
    };
    cm.on("changes", sync);
    cm.on("swapDoc", sync);
    sync();
  });

''' % FULL_RENDER_MAX_LINES

apply(
    'cm5 full render for IME',
    CM_JS,
    'FULL_RENDER_MAX_LINES',
    [(
        re.compile(r'\n  CodeMirror\.version = '),
        lambda m: '\n' + FULL_RENDER_JS + '  CodeMirror.version = ',
    )],
)

node = shutil.which('node')
if node:
    with tempfile.TemporaryDirectory() as tmp:
        for rel in TOUCHED_JS:
            probe = pathlib.Path(tmp) / (pathlib.Path(rel).stem + '.mjs')
            shutil.copyfile(ROOT / rel, probe)
            result = subprocess.run([node, '--check', str(probe)], capture_output=True, text=True)
            if result.returncode != 0:
                fail('syntax check', f"{rel}\n{result.stderr.strip()}")
            print(f"OK   [syntax {rel}]")

print("\nAll patches applied.")
