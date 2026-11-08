<h1 align="center">
<sub>
<img src="https://github.com/gorhill/uBlock/blob/master/src/img/ublock.svg" height="38" width="38">
</sub>
uBlockDefine
</h1>

A fork of [uBlock Origin](https://github.com/gorhill/uBlock) that adds `!#define` macro support for domain list expansion in filter lists.

The purpose of this fork is to implement [uBlock-issues#330](https://github.com/uBlockOrigin/uBlock-issues/issues/330#issuecomment-2110930423).

In 2018 this was a convenience request. In 2024–25 it's a countermeasure. Link shortener, file hosting and video hosting sites now buy 1–2 domains per day specifically to outpace static filter updates. The only sustainable response is a domain group you update in one place. Maintaining 20+ filter lines that each repeat a 10-domain prefix, where that list changes daily, is not a viable workflow.

<img width="702" height="306" alt="Screenshot_20260608-171910_Spark Launcher_1" src="https://github.com/user-attachments/assets/55b63da6-cd56-47d6-805d-e50e86e0a692" />

Element Picker - Add Current Domain To Define Lines Screenshot
<details><summary>Details</summary>
<p>

<img width="702" height="1560" alt="Screenshot_20260608-211723_Spark Launcher" src="https://github.com/user-attachments/assets/ea420f8d-9a87-4f57-9f58-1be642097b3f" />

</p>
</details>

---

## Features

- `!#define` domain macros, expanded at parse time
- Nested macros, with circular-reference protection
- Negation with `~Macro`
- Macros usable in cosmetic filters, network filters and filter options
- Red directive highlighting in the filter editor
- Auto-rename of macro usages when a `!#define` name is edited
- Define search panel in the element picker, with one-tap **Add Current**
- Mobile (Gboard) fixes for select-all, copy and cut in the filter editor
- Auto-updating Firefox releases
- Daily upstream sync

---

## Syntax

```adblock
!#define MacroName (domain1.com,domain2.com,domain3.*)
```

- The macro name can be anything without spaces.
- Domains are comma-separated inside `( )`.
- The definition must be on one line and must not contain `)` inside the list.
- Text after the closing `)` is ignored, so it can hold a note.
- Wildcards like `gplinks.*` are supported.
- The `!#define` line is removed from the list at parse time.
- A macro applies only inside the list that defines it.
- Names match whole tokens only. A macro named like a real domain replaces that domain wherever it appears in the list.

### Example

```adblock
!#define GplinksPartners.com (powergam.online,qrixpe.com,sanadegreecollege.in)
GplinksPartners.com##center, .main-content, .myTimerDiv
GplinksPartners.com##+js(set, document.hidden, false)
*$script,1p,domain=GplinksPartners.com
```

At parse time `GplinksPartners.com` expands into all three domains, so each rule is written once.

### Where macros expand

| Position | Result |
|---|---|
| Before `##`, `#@#`, `#?#`, `#$#`, `#%#` | Joined with `,` in the same line |
| `domain=`, `from=`, `to=`, `denyallow=` option values | Joined with `\|` in the same line |
| Start of a network filter | One line per domain |

Comment lines (`!`) are never expanded.

### Negation

Prefix a macro with `~` inside a domain list or option to negate every domain in it:

```adblock
*$script,domain=~GplinksPartners.com
```

### Nested macros

```adblock
!#define Gplinks (gplinks.*,get2.in)
!#define GplinksAll (powergam.online,qrixpe.com,Gplinks)
GplinksAll##.ad-banner
```

Duplicates are removed. A macro that references itself, directly or through another macro, resolves to nothing for the looping part. An empty macro is not expanded.

---

## Editor

### Red directive highlighting

`!#define`, `!#if`, `!#else`, `!#endif` and `!#include` are highlighted in red in the filter editor (`#cc0000` light, `#ff6b6b` dark).

### Auto-rename

When you edit the name on a `!#define` line, all usages of that macro in the same list are renamed automatically. Undo and redo do not trigger a rename.

### Mobile input fixes

On Android, Gboard reads select-all, copy and cut from the editor DOM text. Stock CodeMirror 5 put line numbers and extra blank lines into that text. This fork:

- Renders line numbers and lint messages as CSS generated content instead of text.
- Uses inline elements for gutter helpers.
- Renders the whole document for lists up to 5000 lines, so select-all covers everything and not only the visible part.

Copied text is now exactly one line per filter line.

---

## Element Picker: Define Search

The picker has a search box for the `!#define` lines in **My filters**.

1. Type part of a macro name (case-insensitive).
2. Tap **Add Current** on the match.
3. The current page's hostname is appended to that macro, My filters is saved, all filters are reloaded and the picker closes.

Button states: **Added** if the domain is already in the macro, **Not found** if the macro no longer exists. Punycode hostnames are converted to Unicode before being added.

---

## Build

### Artifact

`build.yml` runs on every push and pull request. It checks out upstream `gorhill/uBlock`, applies `apply_patches.py` and `patch.py`, then runs `make firefox`. Download the result from [Actions](../../actions) → latest run → **uBlockOrigin Define V<version> Fork Unsigned**.

### Release

Run the **Release XPI** workflow manually. It:

- Builds `uBlockDefine.firefox.xpi` from this repo.
- Creates release `v<version>`. If that release already exists, it is skipped.
- Sets `update_url` in the manifest. Set the repository variable `ADDON_ID` to override the add-on ID.
- Publishes `updates.json` to the `updates` release, so installed copies update themselves (Firefox 115+).

For a signed build, head to the Release section.

### Upstream sync

`sync-upstream.yml` runs daily at 03:17 UTC. It merges `gorhill/uBlock` master into this repo, keeps this README and the fork's workflows, then triggers **Release XPI**.

---

## How Patching Works

This fork does not maintain hand-edited copies of uBlock Origin's files. Two scripts apply string-based patches at build time:

| Script | Patches |
|---|---|
| `apply_patches.py` | `!#define` parser and expansion, directive color, auto-rename, element picker search |
| `patch.py` | CodeMirror mobile input fixes |

Both scripts are idempotent: a patch already present is skipped. If an upstream change breaks a patch anchor (it must match exactly once), the build fails with a descriptive error. Touched JS files are syntax-checked with `node --check`.

---

## Based On

[uBlock Origin](https://github.com/gorhill/uBlock) by Raymond Hill — GPLv3
