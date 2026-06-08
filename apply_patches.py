import re, sys, pathlib

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
        }

        static restructureHostnameList('''

text = (ROOT / 'src/js/static-filtering-parser.js').read_text(encoding='utf-8')
anchor = '        static restructureHostnameList('
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
                    doc.eachLine((lineHandle) => {
                        const lineNum = doc.getLineNumber(lineHandle);
                        if ( lineNum === lineNo ) { return; }
                        const text = lineHandle.text;
                        if ( !text.includes(oldName) ) { return; }
                        const escaped = oldName.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
                        const re = new RegExp(`(?<![\\\\w.])${escaped}(?![\\\\w])`, 'g');
                        const replaced = text.replace(re, newName);
                        if ( replaced === text ) { return; }
                        doc.replaceRange(
                            replaced,
                            { line: lineNum, ch: 0 },
                            { line: lineNum, ch: text.length }
                        );
                    });
                }
                defineNameCache.set(lineNo, newName);
            } else if ( oldName ) {
                defineNameCache.delete(lineNo);
            }
        }
    };

    const onChanges = (cm, changes) => {'''

ANCHOR_ONCHANGES = '    const onChanges = (cm, changes) => {'
ANCHOR_CALL      = '        if ( changes.length === 0 ) { return; }\n        const doc = cm.getDoc();'
NEW_CALL         = '        if ( changes.length === 0 ) { return; }\n        syncDefineRenames(cm, changes);\n        const doc = cm.getDoc();'
ANCHOR_BEFORE    = "        cm.on('beforeChange', onBeforeChanges);"
NEW_BEFORE       = """        cm.on('beforeChange', (cm, change) => {
            const doc = cm.getDoc();
            const lineNo = change.from.line;
            const text = doc.getLine(lineNo) || '';
            const m = /^!#define\\s+(\\S+)\\s+\\(/.exec(text);
            if ( m ) { defineNameCache.set(lineNo, m[1]); }
            onBeforeChanges(cm, change);
        });"""

text = (ROOT / 'src/js/codemirror/ubo-static-filtering.js').read_text(encoding='utf-8')
if 'syncDefineRenames' not in text:
    if ANCHOR_ONCHANGES not in text:
        print(f"FAIL [defineNameCache anchor]: '{ANCHOR_ONCHANGES}' not found", file=sys.stderr)
        sys.exit(1)
    text = text.replace(ANCHOR_ONCHANGES, DEFINE_CACHE_BLOCK, 1)
    text = text.replace(ANCHOR_CALL, NEW_CALL, 1)
    text = text.replace(ANCHOR_BEFORE, NEW_BEFORE, 1)
    (ROOT / 'src/js/codemirror/ubo-static-filtering.js').write_text(text, encoding='utf-8')
    print("OK   [defineNameCache + syncDefineRenames]")
else:
    print("SKIP [defineNameCache + syncDefineRenames]: already present")

print("\nAll patches applied.")
