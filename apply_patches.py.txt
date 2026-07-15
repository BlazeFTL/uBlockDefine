import sys, pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent

def replace_exact(path, old, new, label):
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print(f"FAIL [{label}]: target string not found in {path}", file=sys.stderr)
        sys.exit(1)
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print(f"OK   [{label}]")

# ── 1. Red directive ink ──────────────────────────────────────────────────────
replace_exact(
    ROOT / 'src/css/themes/default.css',
    '    --sf-directive-ink: var(--ink-1);',
    '    --sf-directive-ink: #cc0000;',
    'red directive ink',
)

# ── 2. Add !#define to preparse regex ────────────────────────────────────────
replace_exact(
    ROOT / 'src/js/static-filtering-parser.js',
    'this.rePreparseDirectiveAny = /^!#(?:else|endif|if |include )/;',
    'this.rePreparseDirectiveAny = /^!#(?:define |else|endif|if |include )/;',
    'preparse regex',
)

# ── 3. expandDefines static method ───────────────────────────────────────────
EXPAND_DEFINES = '''        static expandDefines(content) {
            const defines = new Map();
            const reDefine = /^!#define\\s+(\\S+)\\s+\\(([^)]+)\\)[^\\n\\r]*(?:[\\n\\r]+|$)/gm;
            const cleaned = content.replace(reDefine, (match, name, domains) => {
                defines.set(name, domains.split(',').map(d => d.trim()).filter(Boolean));
                return '';
            });
            if ( defines.size === 0 ) { return content; }
            const lines = cleaned.split(/\\r?\\n/);
            const out = [];
            for ( let line of lines ) {
                let lineExpanded = false;
                for ( const [ name, domains ] of defines ) {
                    if ( line.startsWith(name) ) {
                        let rest = line.slice(name.length);
                        for ( const [ n2, d2 ] of defines ) {
                            if ( rest.includes(n2) ) {
                                rest = rest.split(n2).join(d2.join('|'));
                            }
                        }
                        for ( const domain of domains ) {
                            out.push(domain + rest);
                        }
                        lineExpanded = true;
                        break;
                    }
                }
                if ( lineExpanded ) { continue; }
                for ( const [ name, domains ] of defines ) {
                    if ( line.includes(name) ) {
                        line = line.split(name).join(domains.join('|'));
                    }
                }
                out.push(line);
            }
            return out.join('\\n');
        }

        static prune(content, env) {'''

text = (ROOT / 'src/js/static-filtering-parser.js').read_text(encoding='utf-8')
anchor = '        static prune(content, env) {'
if anchor not in text:
    print(f"FAIL [expandDefines anchor]: '{anchor}' not found", file=sys.stderr)
    sys.exit(1)
if 'expandDefines' not in text:
    (ROOT / 'src/js/static-filtering-parser.js').write_text(
        text.replace(anchor, EXPAND_DEFINES, 1), encoding='utf-8')
    print("OK   [expandDefines method]")
else:
    print("SKIP [expandDefines method]: already present")

# ── 4. defineNameCache + syncDefineRenames ────────────────────────────────────
DEFINE_CACHE_BLOCK = '''    // Auto-rename macro usages when !#define name is edited
    const defineNameCache = new Map();
    const syncDefineRenames = (cm, changes) => {
        const doc = cm.getDoc();
        for ( const change of changes ) {
            const lineNo = change.from.line;
            const newText = doc.getLine(lineNo) || '';
            const newMatch = /^!#define\\s+(\\S+)\\s+\\(/.exec(newText);
            const oldName = defineNameCache.get(lineNo);
            if ( newMatch ) {
                const newName = newMatch[1];
                if ( oldName && oldName !== newName ) {
                    const cursor = doc.getCursor();
                    cm.operation(() => {
                    doc.eachLine((lineHandle) => {
                        const lineNum = doc.getLineNumber(lineHandle);
                        if ( lineNum === lineNo ) { return; }
                        const text = lineHandle.text;
                        if ( !text.includes(oldName) ) { return; }
                        const escaped = oldName.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
                        const re = new RegExp(`(?<![\\\\w./#])${escaped}(?![\\\\w./])`, 'g');
                        const replaced = text.replace(re, newName);
                        if ( replaced === text ) { return; }
                        doc.replaceRange(
                            replaced,
                            { line: lineNum, ch: 0 },
                            { line: lineNum, ch: text.length }
                        );
                    });
                    });
                    doc.setCursor(cursor);
                }
                defineNameCache.set(lineNo, newName);
            } else if ( oldName ) {
                defineNameCache.delete(lineNo);
            }
        }
    };

    const onChanges = (cm, changes) => {'''

ANCHOR_CALL   = '        if ( changes.length === 0 ) { return; }\n        const doc = cm.getDoc();'
NEW_CALL      = '        if ( changes.length === 0 ) { return; }\n        syncDefineRenames(cm, changes);\n        const doc = cm.getDoc();'
ANCHOR_BEFORE = "        cm.on('beforeChange', onBeforeChanges);"
NEW_BEFORE    = """        cm.on('beforeChange', (cm, change) => {
            const doc = cm.getDoc();
            const lineNo = change.from.line;
            const text = doc.getLine(lineNo) || '';
            const m = /^!#define\\s+(\\S+)\\s+\\(/.exec(text);
            if ( m ) { defineNameCache.set(lineNo, m[1]); }
            onBeforeChanges(cm, change);
        });"""

text = (ROOT / 'src/js/codemirror/ubo-static-filtering.js').read_text(encoding='utf-8')
if 'syncDefineRenames' not in text:
    anchor = '    const onChanges = (cm, changes) => {'
    if anchor not in text:
        print(f"FAIL [defineNameCache anchor]: '{anchor}' not found", file=sys.stderr)
        sys.exit(1)
    text = text.replace(anchor, DEFINE_CACHE_BLOCK, 1)
    text = text.replace(ANCHOR_CALL, NEW_CALL, 1)
    text = text.replace(ANCHOR_BEFORE, NEW_BEFORE, 1)
    (ROOT / 'src/js/codemirror/ubo-static-filtering.js').write_text(text, encoding='utf-8')
    print("OK   [defineNameCache + syncDefineRenames]")
else:
    print("SKIP [defineNameCache + syncDefineRenames]: already present")

# ── 5. Wire expandDefines into prune() ───────────────────────────────────────
replace_exact(
    ROOT / 'src/js/static-filtering-parser.js',
    '        static prune(content, env) {\n            const parts = this.splitter(content, env);',
    '        static prune(content, env) {\n            content = this.expandDefines(content);\n            const parts = this.splitter(content, env);',
    'prune calls expandDefines',
)

# ── 6. Element Picker: defineSearch CSS ──────────────────────────────────────
EPICKER_CSS = """
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
    overflow-y: scroll;
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

css_path = ROOT / 'src/css/epicker-ui.css'
css_text = css_path.read_text(encoding='utf-8')
if '#defineSearchContainer' not in css_text:
    css_path.write_text(css_text + EPICKER_CSS, encoding='utf-8')
    print("OK   [epicker defineSearch CSS]")
else:
    print("SKIP [epicker defineSearch CSS]: already present")

# ── 7. Element Picker: defineSearch HTML ─────────────────────────────────────
EPICKER_HTML_OLD = '    </div>\n</section>\n<ul id="candidateFilters">'
EPICKER_HTML_NEW = '    </div>\n</section>\n<div id="defineSearchContainer">\n    <input type="text" id="defineSearchInput" placeholder="Search !#define lists...">\n    <ul id="defineSearchResults" class="hide"></ul>\n</div>\n<ul id="candidateFilters">'

html_path = ROOT / 'src/web_accessible_resources/epicker-ui.html'
html_text = html_path.read_text(encoding='utf-8')
if '#defineSearchContainer' not in html_text:
    if EPICKER_HTML_OLD not in html_text:
        print("FAIL [epicker defineSearch HTML]: anchor not found", file=sys.stderr)
        sys.exit(1)
    html_path.write_text(html_text.replace(EPICKER_HTML_OLD, EPICKER_HTML_NEW, 1), encoding='utf-8')
    print("OK   [epicker defineSearch HTML]")
else:
    print("SKIP [epicker defineSearch HTML]: already present")

# ── 8. Element Picker: userFilters state vars ─────────────────────────────────
replace_exact(
    ROOT / 'src/js/epicker-ui.js',
    "const NoPaths = 'M0 0';\n\nconst reCosmeticAnchor",
    "const NoPaths = 'M0 0';\n\nlet userFiltersContent = '';\nlet userFiltersEnabled = true;\nlet userFiltersTrusted = false;\n\nconst reCosmeticAnchor",
    'epicker userFilters vars',
)

# ── 9. Element Picker: initDefineSearch + addDomainToDefine ───────────────────
EPICKER_JS_FUNCS = """\n/******************************************************************************/

const initDefineSearch = function() {
    const searchInput = $id('defineSearchInput');
    const resultsList = $id('defineSearchResults');
    if (!searchInput || !resultsList) return;

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
        if (query.length === 0) {
            resultsList.classList.add('hide');
            return;
        }

        const defines = [];
        const reDefine = /^!#define\\s+(\\S+)\\s+\\(([^)]+)\\)/gm;
        let match;
        while ((match = reDefine.exec(userFiltersContent)) !== null) {
            const name = match[1];
            const domains = match[2];
            if (name.toLowerCase().includes(query)) {
                defines.push({ name, domains, fullMatch: match[0] });
            }
        }

        if (defines.length === 0) {
            resultsList.classList.add('hide');
            return;
        }

        resultsList.innerHTML = '';
        defines.forEach(def => {
            const li = document.createElement('li');
            const nameSpan = document.createElement('span');
            nameSpan.textContent = def.name;
            li.appendChild(nameSpan);

            const addBtn = document.createElement('button');
            addBtn.className = 'add-btn';
            addBtn.textContent = 'Add Current';
            addBtn.onclick = (ev) => {
                ev.stopPropagation();
                addDomainToDefine(def);
            };
            li.appendChild(addBtn);
            resultsList.appendChild(li);
        });
        resultsList.classList.remove('hide');
    });
};

const addDomainToDefine = function(def) {
    let hn = hostnameFromURI(docURL.href);
    if (hn.startsWith('xn--')) {
        hn = punycode.toUnicode(hn);
    }

    const currentDomains = def.domains.split(',').map(d => d.trim());
    if (currentDomains.includes(hn)) {
        alert('Domain already in list');
        return;
    }

    const newDomains = [...currentDomains, hn].join(',');
    const newDefineLine = `!#define ${def.name} (${newDomains})`;

    userFiltersContent = userFiltersContent.replace(def.fullMatch, newDefineLine);

    vAPI.messaging.send('dashboard', {
        what: 'writeUserFilters',
        content: userFiltersContent,
        enabled: userFiltersEnabled,
        trusted: userFiltersTrusted,
    }).then(() => {
        vAPI.messaging.send('dashboard', { what: 'reloadAllFilters' });
        $id('defineSearchInput').value = '';
        $id('defineSearchResults').classList.add('hide');
        quitPicker();
    });
};

/******************************************************************************/

const quitPicker = function() {"""

js_path = ROOT / 'src/js/epicker-ui.js'
js_text = js_path.read_text(encoding='utf-8')
if 'initDefineSearch' not in js_text:
    anchor = '\n/******************************************************************************/\n\nconst quitPicker = function() {'
    if anchor not in js_text:
        print("FAIL [epicker initDefineSearch]: anchor not found", file=sys.stderr)
        sys.exit(1)
    js_text = js_text.replace(anchor, EPICKER_JS_FUNCS, 1)
    js_path.write_text(js_text, encoding='utf-8')
    print("OK   [epicker initDefineSearch + addDomainToDefine]")
else:
    print("SKIP [epicker initDefineSearch + addDomainToDefine]: already present")

# ── 10. Element Picker: readUserFilters + initDefineSearch call ───────────────
replace_exact(
    ROOT / 'src/js/epicker-ui.js',
    "    startPicker();\n    pickerContentPort.postMessage({ what: 'start' });\n}, { once: true });",
    "    startPicker();\n    pickerContentPort.postMessage({ what: 'start' });\n    vAPI.messaging.send('dashboard', { what: 'readUserFilters' }).then(result => {\n        userFiltersContent = result.content || '';\n        userFiltersEnabled = result.enabled !== false;\n        userFiltersTrusted = result.trusted || false;\n        initDefineSearch();\n    });\n}, { once: true });",
    'epicker initDefineSearch call',
)

print("\nAll patches applied.")
