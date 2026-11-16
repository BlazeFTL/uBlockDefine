import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
TOUCHED_JS = []

# Run order: apply_patches.py, patch.py, patch2.py.


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


STATIC_JS = 'src/js/codemirror/ubo-static-filtering.js'

# ---------------------------------------------------------------------------
# 1. About page: show fork name + version.
# ---------------------------------------------------------------------------

apply(
    'about fork name',
    'src/js/about.js',
    "'uBlockOrigin Define '",
    [(
        "dom.text('#aboutNameVer', appData.name + ' ' + appData.version);",
        "dom.text('#aboutNameVer', 'uBlockOrigin Define ' + appData.version);",
    )],
)

# Also visible in the browser's add-on manager.
apply(
    'manifest fork name',
    'platform/firefox/manifest.json',
    '"name": "uBlockOrigin Define"',
    [('"name": "uBlock Origin",', '"name": "uBlockOrigin Define",')],
)

# ---------------------------------------------------------------------------
# 2. !#Collapse macro: fold helper + label widget.
# ---------------------------------------------------------------------------

COLLAPSE_HELPERS = r"""// Collapse macro: `!#Collapse`, `!#Col` or `!#Collapsed`, optionally followed
// by a label. The lines right below it, up to the next empty line, can be
// folded like an `!#if` block. A folded block shows the typed label, or else
// the domain found in the first `!` comment (or filter) of the block.

const reCollapseMacro = /^[ \t]*!#col(?:lapsed?)?(?![\w-])(?:[ \t]+(.*?))?[ \t]*$/i;
const reCollapseUrlHost = /\bhttps?:\/\/(?:www\.)?([^\/\s:?#]+)/i;
const reCollapseFilterHost = /^~?(?:\|\|)?((?:[a-z0-9][a-z0-9-]*\.)+(?:\*|[a-z0-9-]+))(?=[,#$^|\/:]|$)/i;

const collapseBodyRange = (cm, startLineNo) => {
    const lastLineNo = cm.lastLine();
    let endLineNo = startLineNo;
    while ( endLineNo < lastLineNo ) {
        if ( cm.getLine(endLineNo + 1).trim() === '' ) { break; }
        endLineNo += 1;
    }
    if ( endLineNo === startLineNo ) { return; }
    return {
        from: CodeMirror.Pos(startLineNo, cm.getLine(startLineNo).length),
        to: CodeMirror.Pos(endLineNo, cm.getLine(endLineNo).length),
    };
};

const collapseAutoLabel = (cm, startLineNo) => {
    const range = collapseBodyRange(cm, startLineNo);
    if ( range === undefined ) { return ''; }
    let fallback = '';
    for ( let lineNo = startLineNo + 1; lineNo <= range.to.line; lineNo++ ) {
        const text = cm.getLine(lineNo).trim();
        if ( text.startsWith('!') ) {
            const match = reCollapseUrlHost.exec(text);
            if ( match !== null ) { return match[1]; }
        } else if ( fallback === '' ) {
            const match = reCollapseFilterHost.exec(text);
            if ( match !== null ) { fallback = match[1]; }
        }
    }
    return fallback || `${range.to.line - startLineNo} lines`;
};

const makeFoldWidget = (cm, from) => {
    const widget = document.createElement('span');
    widget.className = 'CodeMirror-foldmarker';
    let label = '';
    const match = reCollapseMacro.exec(cm.getLine(from.line));
    if ( match !== null && (match[1] || '') === '' ) {
        label = collapseAutoLabel(cm, from.line);
    }
    widget.textContent = label !== ''
        ? `\u00A0(${label})\u00A0\u22EF\u00A0`
        : '\u00A0\u22EF\u00A0';
    return widget;
};

"""

FOLD_HELPER_HEAD = "CodeMirror.registerHelper('fold', 'ubo-static-filtering', (( ) => {"

FOLD_HELPER_OLD = """        if ( startLine.startsWith('!#include ') ) {
            return foldInclude(startLineNo, startLine, cm);
        }
"""

FOLD_HELPER_NEW = FOLD_HELPER_OLD + """        if ( reCollapseMacro.test(startLine) ) {
            return collapseBodyRange(cm, startLineNo);
        }
"""

apply(
    'collapse helpers',
    STATIC_JS,
    'const reCollapseMacro',
    [
        (FOLD_HELPER_HEAD, COLLAPSE_HELPERS + FOLD_HELPER_HEAD),
        (FOLD_HELPER_OLD, FOLD_HELPER_NEW),
    ],
)

# ---------------------------------------------------------------------------
# 3. !#Collapse macro: gutter marker, fold range, fold events.
# ---------------------------------------------------------------------------

_static_text = (ROOT / STATIC_JS).read_text(encoding='utf-8')
if '<span class="CodeMirror-lintmarker"' in _static_text:
    COLLAPSE_TEMPLATE = """        'collapse-start': {
            node: null,
            html: [
                '<span class="CodeMirror-lintmarker" data-lint="collapse" data-fold="start" data-state="">',
                  '<svg viewBox="0 0 100 100">',
                    '<polygon points="0,0 100,0 50,100" />',
                  '</svg>',
                '</span>',
            ],
        },
"""
else:
    COLLAPSE_TEMPLATE = """        'collapse-start': {
            node: null,
            html: [
                '<div class="CodeMirror-lintmarker" data-lint="collapse" data-fold="start" data-state="">&nbsp;',
                  '<svg viewBox="0 0 100 100">',
                    '<polygon points="0,0 100,0 50,100" />',
                  '</svg>',
                '</div>',
            ],
        },
"""

TEMPLATES_HEAD = """    const markerTemplates = {
        'error': {"""

DETAILS_OLD = """        if ( astParser.astTypeFlavor !== sfp.AST_TYPE_COMMENT_PREPARSER ) {
            if ( astParser.raw.startsWith('! <<<<<<<< ') === false ) { return; }
"""

DETAILS_NEW = """        if ( astParser.astTypeFlavor !== sfp.AST_TYPE_COMMENT_PREPARSER ) {
            if ( reCollapseMacro.test(astParser.raw) ) {
                return { lint: 'collapse-start' };
            }
            if ( astParser.raw.startsWith('! <<<<<<<< ') === false ) { return; }
"""

RANGE_OLD = """        if ( marker.dataset.fold === undefined ) { return; }
        const foldName = marker.dataset.lint;
"""

RANGE_NEW = """        if ( marker.dataset.fold === undefined ) { return; }
        if ( marker.dataset.lint === 'collapse' ) {
            return collapseBodyRange(cm, lineNo);
        }
        const foldName = marker.dataset.lint;
"""

CLICK_OLD = r"""                widget: '\u00A0\u22EF\u00A0',
"""

CLICK_NEW = """                widget: from => makeFoldWidget(cm, from),
"""

EVENTS_OLD = """        cm.on('fold', function(cm, from) {
            const doc = cm.getDoc();
            const lineHandle = doc.getLineHandle(from.line);
            const marker = extractMarker(lineHandle);
            dom.cl.add(marker, 'folded');
        });
        cm.on('unfold', function(cm, from) {
            const doc = cm.getDoc();
            const lineHandle = doc.getLineHandle(from.line);
            const marker = extractMarker(lineHandle);
            dom.cl.remove(marker, 'folded');
        });
"""

EVENTS_NEW = """        cm.setOption('foldOptions', {
            widget: from => makeFoldWidget(cm, from),
        });
        cm.on('fold', function(cm, from) {
            const lineHandle = cm.getDoc().getLineHandle(from.line);
            const marker = lineHandle ? extractMarker(lineHandle) : null;
            if ( marker !== null ) { dom.cl.add(marker, 'folded'); }
        });
        cm.on('unfold', function(cm, from) {
            const lineHandle = cm.getDoc().getLineHandle(from.line);
            const marker = lineHandle ? extractMarker(lineHandle) : null;
            if ( marker !== null ) { dom.cl.remove(marker, 'folded'); }
        });
"""

apply(
    'collapse linter marker',
    STATIC_JS,
    "lint: 'collapse-start'",
    [
        (TEMPLATES_HEAD, TEMPLATES_HEAD.replace("{\n        'error': {", "{\n" + COLLAPSE_TEMPLATE + "        'error': {")),
        (DETAILS_OLD, DETAILS_NEW),
        (RANGE_OLD, RANGE_NEW),
        (CLICK_OLD, CLICK_NEW),
        (EVENTS_OLD, EVENTS_NEW),
    ],
)

# ---------------------------------------------------------------------------
# 4. Fold memory (!#if and !#Collapse) + unfold while searching.
# ---------------------------------------------------------------------------

FOLD_MEMORY = r"""
/******************************************************************************/

// Fold memory: remember which `!#if` and `!#Collapse` blocks are folded
// across sessions. While a search is active everything is unfolded, and the
// remembered state is put back once the search ends.
// A block is identified by its first two lines plus its rank among identical
// blocks. `!#Collapse` blocks never seen before start folded, `!#if` blocks
// start unfolded.

{
    const hashString = s => {
        let h = 0x811c9dc5;
        for ( let i = 0; i < s.length; i++ ) {
            h ^= s.charCodeAt(i);
            h = Math.imul(h, 0x01000193);
        }
        return (h >>> 0).toString(36);
    };

    const classify = text => {
        if ( text.startsWith('!#if ') ) { return 'if'; }
        return reCollapseMacro.test(text) ? 'collapse' : '';
    };

    const collectBlocks = cm => {
        const blocks = [];
        const seen = new Map();
        const lastLineNo = cm.lastLine();
        cm.getDoc().eachLine(lineHandle => {
            const text = lineHandle.text;
            const kind = classify(text);
            if ( kind === '' ) { return; }
            const lineNo = lineHandle.lineNo();
            const next = lineNo < lastLineNo ? cm.getLine(lineNo + 1) : '';
            const base = `${kind}\n${text.trim()}\n${next.trim()}`;
            const rank = seen.get(base) || 0;
            seen.set(base, rank + 1);
            blocks.push({ lineNo, kind, key: `${hashString(base)}.${rank}` });
        });
        return blocks;
    };

    const foldMarkAt = (cm, lineNo) => {
        const pos = CodeMirror.Pos(lineNo, cm.getLine(lineNo).length);
        for ( const mark of cm.findMarksAt(pos) ) {
            if ( mark.__isFold !== true ) { continue; }
            const range = mark.find();
            if ( range && range.from.line === lineNo ) { return mark; }
        }
        return null;
    };

    const takeSnapshot = cm => {
        const snap = {};
        for ( const { lineNo, key } of collectBlocks(cm) ) {
            snap[key] = foldMarkAt(cm, lineNo) !== null ? 1 : 0;
        }
        return snap;
    };

    const unfoldAll = cm => {
        cm.operation(( ) => {
            for ( const mark of cm.getAllMarks() ) {
                if ( mark.__isFold === true ) { mark.clear(); }
            }
        });
    };

    const applySnapshot = (cm, snap) => {
        const info = cm.getScrollInfo();
        const topLine = cm.lineAtHeight(info.top, 'local');
        const topOffset = info.top - cm.heightAtLine(topLine, 'local');
        cm.operation(( ) => {
            for ( const { lineNo, kind, key } of collectBlocks(cm) ) {
                const wanted = snap[key] !== undefined
                    ? snap[key] === 1
                    : kind === 'collapse';
                const mark = foldMarkAt(cm, lineNo);
                if ( wanted === (mark !== null) ) { continue; }
                if ( mark !== null ) {
                    mark.clear();
                } else {
                    cm.foldCode(lineNo, {
                        rangeFinder: CodeMirror.fold['ubo-static-filtering'],
                    }, 'fold');
                }
            }
        });
        // Keep the same content under the viewport top.
        cm.scrollTo(null, Math.max(0, cm.heightAtLine(topLine, 'local') + topOffset));
        // Never leave the cursor inside hidden text.
        const cursor = cm.getCursor();
        for ( const mark of cm.findMarksAt(cursor) ) {
            if ( mark.__isFold !== true ) { continue; }
            const range = mark.find();
            if ( range && cursor.line > range.from.line ) {
                cm.setCursor(range.from);
                break;
            }
        }
    };

    CodeMirror.defineExtension('uboRememberFolds', function(storageKey) {
        const cm = this;
        let saved = null;
        let pendingRestore = true;
        let linterReady = false;
        let searching = false;
        let beforeSearch = null;

        const persist = ( ) => {
            saved = takeSnapshot(cm);
            vAPI.localStorage.setItem(storageKey, JSON.stringify(saved));
        };

        const saveTimer = vAPI.defer.create(( ) => {
            if ( searching || pendingRestore ) { return; }
            persist();
        });

        const scheduleSave = ( ) => {
            if ( searching || pendingRestore ) { return; }
            saveTimer.offon(503);
        };

        // Restore once the stored state is loaded and the linter has built
        // the gutter markers for the current content.
        const tryRestore = ( ) => {
            if ( pendingRestore === false ) { return; }
            if ( linterReady === false || saved === null ) { return; }
            pendingRestore = false;
            if ( searching ) { return; }
            applySnapshot(cm, saved);
            scheduleSave();
        };

        vAPI.localStorage.getItemAsync(storageKey).then(raw => {
            let snap;
            try {
                snap = typeof raw === 'string' ? JSON.parse(raw) : raw;
            } catch {
            }
            saved = snap instanceof Object ? snap : {};
            tryRestore();
        }).catch(( ) => {
            saved = {};
            tryRestore();
        });

        // The whole content is being replaced (reload from storage, revert,
        // trust toggle): folds are lost, so remember them and restore later.
        cm.on('beforeChange', (cm, change) => {
            const whole = change.origin === 'setValue' || (
                change.from.line === 0 && change.from.ch === 0 &&
                change.to.line > change.from.line &&
                change.to.line >= cm.lastLine()
            );
            if ( whole === false ) { return; }
            if ( searching === false && pendingRestore === false ) {
                persist();
            }
            saveTimer.off();
            pendingRestore = true;
            linterReady = false;
        });

        cm.on('fold', scheduleSave);
        cm.on('unfold', scheduleSave);
        cm.on('changes', scheduleSave);

        cm.on('linterDone', ( ) => {
            linterReady = true;
            tryRestore();
        });

        cm.on('searchstart', ( ) => {
            if ( searching === false ) {
                beforeSearch = pendingRestore ? (saved || {}) : takeSnapshot(cm);
                saveTimer.off();
                searching = true;
            }
            unfoldAll(cm);
        });

        cm.on('searchend', ( ) => {
            if ( searching === false ) { return; }
            searching = false;
            const snap = beforeSearch || {};
            beforeSearch = null;
            if ( pendingRestore ) { return; }
            applySnapshot(cm, snap);
        });
    });
}
"""

apply(
    'fold memory',
    STATIC_JS,
    'uboRememberFolds',
    [],
    append=FOLD_MEMORY,
)

apply(
    'fold memory enable in My filters',
    'src/js/1p-filters.js',
    'uboRememberFolds',
    [(
        'uBlockDashboard.patchCodeMirrorEditor(cmEditor);',
        "uBlockDashboard.patchCodeMirrorEditor(cmEditor);\ncmEditor.uboRememberFolds('myFiltersFolds');",
    )],
)

apply(
    'search signals',
    'src/js/codemirror/search.js',
    "CodeMirror.signal(cm, 'searchstart')",
    [
        (
            "    const startSearch = function(cm, state) {\n",
            "    const startSearch = function(cm, state) {\n        CodeMirror.signal(cm, 'searchstart');\n",
        ),
        (
            "            state.lines = [];\n            if ( state.overlay !== undefined ) {\n                cm.removeOverlay(state.overlay);\n                state.overlay = undefined;\n            }",
            "            state.lines = [];\n            CodeMirror.signal(cm, 'searchend');\n            if ( state.overlay !== undefined ) {\n                cm.removeOverlay(state.overlay);\n                state.overlay = undefined;\n            }",
        ),
    ],
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

print("\nAll patch2 changes applied.")
