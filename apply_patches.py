import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
TOUCHED_JS = []


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
                fail(label, f"regex matched {found}x in {path}: {old.pattern}")
            text = old.sub(new, text, count=1)
        else:
            found = text.count(old)
            if found != 1:
                fail(label, f"anchor matched {found}x in {path}: {old.strip()[:80]!r}")
            text = text.replace(old, new, 1)
    path.write_text(text + append, encoding='utf-8')
    print(f"OK   [{label}]")


SEP = '/******************************************************************************/'

apply(
    'red directive ink',
    'src/css/themes/default.css',
    '--sf-directive-ink: #cc0000',
    [('    --sf-directive-ink: var(--ink-1);', '    --sf-directive-ink: #cc0000;')],
    append='\n:root.dark {\n    --sf-directive-ink: #ff6b6b;\n}\n',
)

apply(
    'preparse regex',
    'src/js/static-filtering-parser.js',
    '!#(?:define |else',
    [(
        'this.rePreparseDirectiveAny = /^!#(?:else|endif|if |include )/;',
        'this.rePreparseDirectiveAny = /^!#(?:define |else|endif|if |include )/;',
    )],
)

PRUNE_HEAD = '        static prune(content, env) {'

PRUNE_TAIL = r'''            return out.join('\n');
        }

        static getHints() {'''

PRUNE_TAIL_NEW = r'''            return this.expandDefines(out.join('\n'));
        }

        static getHints() {'''

PARSER_METHODS = r"""        static macroSegments(line) {
            if ( line.charCodeAt(0) === 0x21 ) {
                const head = /^!#define[ \t]+\S+[ \t]+\(/.exec(line);
                if ( head === null ) { return []; }
                const end = line.indexOf(')', head[0].length);
                return end === -1 ? [] : [ { beg: head[0].length, end, sep: ',' } ];
            }
            const anchor = /#@?(?:\$\?|[$?%])?#/.exec(line);
            if ( anchor !== null && /^[^\s/$^|]*$/.test(line.slice(0, anchor.index)) ) {
                return [ { beg: 0, end: anchor.index, sep: ',' } ];
            }
            const dollar = line.lastIndexOf('$');
            const segs = [ { beg: 0, end: dollar === -1 ? line.length : dollar, lead: true } ];
            if ( dollar === -1 ) { return segs; }
            const reOpt = /(?:^|,)(?:domain|from|to|denyallow)=([^,]*)/g;
            const opts = line.slice(dollar + 1);
            let match;
            while ( (match = reOpt.exec(opts)) !== null ) {
                const beg = dollar + 1 + match.index + match[0].length - match[1].length;
                segs.push({ beg, end: beg + match[1].length, sep: '|' });
            }
            return segs;
        }

        static renameDefine(line, from, to) {
            if ( line.includes(from) === false ) { return line; }
            const segs = this.macroSegments(line);
            if ( segs.length === 0 ) { return line; }
            const esc = from.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const reAny = new RegExp(`(?<![\\w.*%-])(~?)${esc}(?![\\w.*%-])`, 'g');
            const reLead = new RegExp(`^${esc}(?![\\w.*%-])`);
            for ( let i = segs.length - 1; i >= 0; i-- ) {
                const { beg, end, lead } = segs[i];
                const text = line.slice(beg, end);
                const replaced = lead
                    ? text.replace(reLead, ( ) => to)
                    : text.replace(reAny, (m, neg) => neg + to);
                line = line.slice(0, beg) + replaced + line.slice(end);
            }
            return line;
        }

        static expandDefines(content) {
            const reDefine = /^!#define[ \t]+(\S+)[ \t]+\(([^)\n\r]*)\)[^\n\r]*(?:\r\n|[\n\r]|$)/gm;
            const raw = new Map();
            const cleaned = content.replace(reDefine, (match, name, list) => {
                raw.set(name, list.split(',').map(s => s.trim()).filter(Boolean));
                return '';
            });
            if ( raw.size === 0 ) { return content; }
            const resolved = new Map();
            const resolve = (name, trail) => {
                if ( resolved.has(name) ) { return resolved.get(name); }
                if ( trail.has(name) ) { return []; }
                trail.add(name);
                const out = new Set();
                for ( const token of raw.get(name) ) {
                    if ( raw.has(token) ) {
                        for ( const d of resolve(token, trail) ) { out.add(d); }
                    } else {
                        out.add(token);
                    }
                }
                trail.delete(name);
                const list = Array.from(out);
                resolved.set(name, list);
                return list;
            };
            for ( const name of raw.keys() ) { resolve(name, new Set()); }
            const names = Array.from(raw.keys())
                .filter(name => resolved.get(name).length !== 0)
                .sort((a, b) => b.length - a.length);
            if ( names.length === 0 ) { return cleaned; }
            const alt = names.map(n => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
            const reAny = new RegExp(`(?<![\\w.*%-])(~?)(${alt})(?![\\w.*%-])`, 'g');
            const reLead = new RegExp(`^(${alt})(?![\\w.*%-])`);
            const expandLine = line => {
                if ( line.length === 0 || line.charCodeAt(0) === 0x21 ) { return [ line ]; }
                const segs = this.macroSegments(line);
                let lead;
                for ( let i = segs.length - 1; i >= 0; i-- ) {
                    const seg = segs[i];
                    if ( seg.lead ) { lead = seg; continue; }
                    const text = line.slice(seg.beg, seg.end).replace(
                        reAny,
                        (m, neg, name) => resolved.get(name).map(d => neg + d).join(seg.sep)
                    );
                    line = line.slice(0, seg.beg) + text + line.slice(seg.end);
                }
                if ( lead !== undefined ) {
                    const match = reLead.exec(line);
                    if ( match !== null ) {
                        const rest = line.slice(match[0].length);
                        return resolved.get(match[1]).map(d => d + rest);
                    }
                }
                return [ line ];
            };
            const out = [];
            for ( const line of cleaned.split(/\r?\n/) ) {
                for ( const expanded of expandLine(line) ) { out.push(expanded); }
            }
            return out.join('\n');
        }

"""

apply(
    'define expansion',
    'src/js/static-filtering-parser.js',
    'static expandDefines',
    [
        (PRUNE_HEAD, PARSER_METHODS + PRUNE_HEAD),
        (PRUNE_TAIL, PRUNE_TAIL_NEW),
    ],
)

CM_BLOCK = r"""    const defineNameCache = new Map();
    const reDefineHead = /^!#define[ \t]+(\S+)[ \t]+\(/;
    const syncDefineRenames = (cm, changes) => {
        const doc = cm.getDoc();
        const cache = new Map(defineNameCache);
        defineNameCache.clear();
        for ( const change of changes ) {
            const { origin } = change;
            if ( origin === undefined || origin === 'setValue' ) { continue; }
            if ( origin === 'undo' || origin === 'redo' ) { continue; }
            if ( change.from.line !== change.to.line ) { continue; }
            if ( change.text.length !== 1 ) { continue; }
            const lineNo = change.from.line;
            const oldName = cache.get(lineNo);
            if ( oldName === undefined ) { continue; }
            const match = reDefineHead.exec(doc.getLine(lineNo) || '');
            if ( match === null || match[1] === oldName ) { continue; }
            const newName = match[1];
            const edits = [];
            doc.eachLine(lineHandle => {
                const n = doc.getLineNumber(lineHandle);
                if ( n === lineNo ) { return; }
                const text = lineHandle.text;
                const replaced = sfp.utils.preparser.renameDefine(text, oldName, newName);
                if ( replaced !== text ) { edits.push({ n, text, replaced }); }
            });
            if ( edits.length === 0 ) { continue; }
            cm.operation(( ) => {
                for ( const { n, text, replaced } of edits ) {
                    doc.replaceRange(
                        replaced,
                        { line: n, ch: 0 },
                        { line: n, ch: text.length }
                    );
                }
            });
        }
    };

    const onChanges = (cm, changes) => {"""

CM_CALL_OLD = '        if ( changes.length === 0 ) { return; }\n        const doc = cm.getDoc();'
CM_CALL_NEW = '        if ( changes.length === 0 ) { return; }\n        syncDefineRenames(cm, changes);\n        const doc = cm.getDoc();'

CM_BEFORE_OLD = "        cm.on('beforeChange', onBeforeChanges);"
CM_BEFORE_NEW = r"""        cm.on('beforeChange', (cm, change) => {
            const lineNo = change.from.line;
            const match = reDefineHead.exec(cm.getDoc().getLine(lineNo) || '');
            if ( match !== null ) { defineNameCache.set(lineNo, match[1]); }
            onBeforeChanges(cm, change);
        });"""

apply(
    'define auto-rename',
    'src/js/codemirror/ubo-static-filtering.js',
    'syncDefineRenames',
    [
        ('    const onChanges = (cm, changes) => {', CM_BLOCK),
        (CM_CALL_OLD, CM_CALL_NEW),
        (CM_BEFORE_OLD, CM_BEFORE_NEW),
    ],
)

EPICKER_CSS = r"""
#defineSearchContainer {
    padding: 8px;
    border-top: 1px solid var(--border-2);
    background-color: var(--surface-1);
}

#defineSearchInput {
    width: 100%;
    box-sizing: border-box;
    padding: 8px;
    border: 1px solid var(--border-3);
    border-radius: 4px;
    background-color: var(--surface-0);
    color: var(--ink-1);
    font-size: var(--font-size-smaller);
    outline: none;
}

#defineSearchInput:focus {
    border-color: var(--blue-50);
}

#defineSearchResults {
    margin: 4px 0 0 0;
    padding: 0;
    list-style: none;
    max-height: 120px;
    overflow-y: auto;
    touch-action: pan-y;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
    border: 1px solid var(--border-3);
    border-radius: 4px;
    background-color: var(--surface-0);
}

#defineSearchResults.hide {
    display: none;
}

#defineSearchResults li {
    padding: 0 8px;
    height: 40px;
    box-sizing: border-box;
    cursor: pointer;
    font-family: monospace;
    font-size: 11px;
    border-bottom: 1px solid var(--border-3);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

#defineSearchResults li:last-child {
    border-bottom: none;
}

#defineSearchResults li:hover {
    background-color: var(--surface-2);
}

#defineSearchResults li .add-btn {
    background-color: var(--button-preferred-surface);
    color: var(--button-preferred-ink);
    border: none;
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 10px;
    cursor: pointer;
}
"""

apply('epicker defineSearch CSS', 'src/css/epicker-ui.css', '#defineSearchContainer', [], append=EPICKER_CSS)

EPICKER_HTML_OLD = '    </div>\n</section>\n<ul id="candidateFilters">'
EPICKER_HTML_NEW = r'''    </div>
</section>
<div id="defineSearchContainer">
    <input type="text" id="defineSearchInput" placeholder="Search !#define lists...">
    <ul id="defineSearchResults" class="hide"></ul>
</div>
<ul id="candidateFilters">'''

apply(
    'epicker defineSearch HTML',
    'src/web_accessible_resources/epicker-ui.html',
    'defineSearchContainer',
    [(EPICKER_HTML_OLD, EPICKER_HTML_NEW)],
)

apply(
    'epicker userFilters var',
    'src/js/epicker-ui.js',
    'let userFiltersContent',
    [(
        "const NoPaths = 'M0 0';\n\nconst reCosmeticAnchor",
        "const NoPaths = 'M0 0';\n\nlet userFiltersContent = '';\n\nconst reCosmeticAnchor",
    )],
)

EPICKER_JS_FUNCS = SEP.join([
    '\n',
    r"""

const initDefineSearch = function() {
    const searchInput = $id('defineSearchInput');
    const resultsList = $id('defineSearchResults');
    if ( !searchInput || !resultsList ) { return; }

    let tsY = 0;
    resultsList.addEventListener('touchstart', e => {
        tsY = e.touches[0].clientY;
        e.stopPropagation();
    }, { passive: true });
    resultsList.addEventListener('touchmove', e => {
        e.stopPropagation();
        e.preventDefault();
        const dy = tsY - e.touches[0].clientY;
        resultsList.scrollTop += dy;
        tsY = e.touches[0].clientY;
    }, { passive: false });
    resultsList.addEventListener('touchend', e => {
        e.stopPropagation();
    }, { passive: true });

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim().toLowerCase();
        resultsList.textContent = '';
        if ( query.length === 0 ) {
            resultsList.classList.add('hide');
            return;
        }
        const reDefine = /^!#define[ \t]+(\S+)[ \t]+\(([^)\n\r]*)\)/gm;
        let count = 0;
        let match;
        while ( (match = reDefine.exec(userFiltersContent)) !== null ) {
            const name = match[1];
            if ( name.toLowerCase().includes(query) === false ) { continue; }
            const li = document.createElement('li');
            const nameSpan = document.createElement('span');
            nameSpan.textContent = name;
            li.appendChild(nameSpan);
            const addBtn = document.createElement('button');
            addBtn.className = 'add-btn';
            addBtn.textContent = 'Add Current';
            addBtn.onclick = ev => {
                ev.stopPropagation();
                addDomainToDefine(name, addBtn);
            };
            li.appendChild(addBtn);
            resultsList.appendChild(li);
            count += 1;
        }
        resultsList.classList.toggle('hide', count === 0);
    });
};

const addDomainToDefine = async function(name, button) {
    if ( button.disabled ) { return; }
    button.disabled = true;
    let hn = hostnameFromURI(docURL.href);
    if ( hn.startsWith('xn--') ) {
        hn = punycode.toUnicode(hn);
    }
    const details = await vAPI.messaging.send('dashboard', { what: 'readUserFilters' });
    if ( details instanceof Object === false || details.error ) {
        button.disabled = false;
        return;
    }
    const content = details.content || '';
    const esc = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const reLine = new RegExp(`^(!#define[ \\t]+${esc}[ \\t]+\\()([^)\\n\\r]*)(\\))`, 'm');
    const match = reLine.exec(content);
    if ( match === null ) {
        button.textContent = 'Not found';
        return;
    }
    const domains = match[2].split(',').map(s => s.trim()).filter(Boolean);
    if ( domains.includes(hn) ) {
        button.textContent = 'Added';
        return;
    }
    domains.push(hn);
    const updated = content.slice(0, match.index) +
        match[1] + domains.join(',') + match[3] +
        content.slice(match.index + match[0].length);
    await vAPI.messaging.send('dashboard', {
        what: 'writeUserFilters',
        content: updated,
        enabled: details.enabled,
        trusted: details.trusted,
    });
    await vAPI.messaging.send('dashboard', { what: 'reloadAllFilters' });
    quitPicker();
};

""",
    '\n\nconst quitPicker = function() {',
])

EPICKER_QUIT_ANCHOR = '\n' + SEP + '\n\nconst quitPicker = function() {'

apply(
    'epicker initDefineSearch + addDomainToDefine',
    'src/js/epicker-ui.js',
    'const initDefineSearch',
    [(EPICKER_QUIT_ANCHOR, EPICKER_JS_FUNCS)],
)

EPICKER_START = re.compile(
    r"(\n[ \t]*)startPicker\(\);\n[ \t]*pickerContentPort\.postMessage\(\{ what: 'start' \}\);"
)


def epicker_start(m):
    i = m.group(1)[1:]
    return (
        m.group(0)
        + f"\n{i}vAPI.messaging.send('dashboard', {{ what: 'readUserFilters' }}).then(details => {{"
        + f"\n{i}    if ( details instanceof Object === false || details.error ) {{ return; }}"
        + f"\n{i}    userFiltersContent = details.content || '';"
        + f"\n{i}    initDefineSearch();"
        + f"\n{i}}}).catch(( ) => {{ }});"
    )


apply(
    'epicker initDefineSearch call',
    'src/js/epicker-ui.js',
    'initDefineSearch();',
    [(EPICKER_START, epicker_start)],
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
