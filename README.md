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
- `!#Collapse` macro: fold any block of lines, with an automatic label
- Folded `!#if` blocks show their hosts after `!#endif`
- Fold state is remembered across sessions; searching unfolds everything
- Define search panel in the element picker, with one-tap **Add Current**
- Mobile (Gboard) fixes for select-all, copy, cut and delete in the filter editor
- Fork name shown in the About page and the add-on manager
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

### Collapse macro

`!#Collapse`, `!#Col` or `!#Collapsed` (case-insensitive), optionally followed by a label, makes the lines right below it foldable. The block ends at the next empty line. uBO treats the macro line as a comment, and it is drawn red and bold like other directives.

```adblock
!#Collapse
! https://example.com/some/page
example.com##.ad-banner
example.com##+js(set, document.hidden, false)

!#Collapse My label
other.net##.popup
```

A folded block shows:

1. The label you typed, if any.
2. Otherwise the host of the first `! https://...` comment in the block.
3. Otherwise the host of the first filter in the block.
4. Otherwise the line count.

### Folded `!#if` blocks

A folded `!#if` block shows the hosts found in its `! https://...` comments after `!#endif`, in green, for example `!#endif(arolinks.com+vplink.com)`. Lines starting with `!#` and `! <<<<<<<< ` are skipped. The label is CSS generated content, never part of the editor text.

### Fold memory

In **My filters**, folded `!#if` and `!#Collapse` blocks are remembered across sessions (stored as `myFiltersFolds`).

- `!#Collapse` blocks never seen before start folded. `!#if` blocks start unfolded.
- A block is identified by its first two lines plus its rank among identical blocks. Editing those lines resets its state.
- While a search is active, everything is unfolded. The remembered state returns when the search ends.
- Reloading the content, reverting or toggling trust restores the folds afterwards.

### Mobile input fixes

On Android, Gboard reads select-all, copy and cut from the editor DOM text. Stock CodeMirror 5 put line numbers and extra blank lines into that text. This fork:

- Renders line numbers and lint messages as CSS generated content instead of text.
- Uses inline elements for gutter helpers.
- Renders the whole document for lists up to 5000 lines, so select-all covers everything and not only the visible part.
- Applies IME deletions and multi-line replacements to the document directly. Stock CodeMirror 5 could not map Gecko's native DOM edit back to the document, so cut or delete of whole selected lines made them vanish and then reappear.

Copied text is now exactly one line per filter line.

### Fork name

The About page shows `uBlockOrigin Define <version>`. The add-on manager shows the name `uBlockOrigin Define`.

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

`build.yml` runs on every push and pull request. It checks out upstream `gorhill/uBlock`, applies `apply_patches.py`, `patch.py` and `patch2.py`, sets the add-on ID and `update_url` with `set_update_url.py`, then runs `make firefox`. Download the result from [Actions](../../actions) → latest run → **uBlockOrigin Define V<version> Fork Unsigned**.

### Release

Run the **Release XPI** workflow manually. It:

- Applies all three patch scripts and `set_update_url.py`.
- Builds `uBlockDefine.firefox.xpi`.
- Creates release `v<version>`. If that release already exists, the run is skipped. Enable the `force` input to delete and rebuild it.
- Writes `updates.json` and uploads it to the `updates` pre-release, which is created if missing. Installed copies read it to update themselves (Firefox 115+).

Releases are unsigned.

### Add-on ID and updates

`set_update_url.py` sets the manifest `id` and `update_url`:

- ID: the `ADDON_ID` repository variable, or `ublockdefine@define.fork` if unset. It never uses the upstream ID.
- `update_url`: `https://github.com/<repo>/releases/download/updates/updates.json`

Updates do not use a branch. They depend on the `updates` release: do not delete it. The key in `updates.json` must match the installed add-on's ID, so changing `ADDON_ID` stops existing installs from updating.

### Upstream sync

`sync-upstream.yml` runs daily at 03:17 UTC. It merges `gorhill/uBlock` master into this repo, keeps this README and the fork's workflows, then triggers **Release XPI**.

---

## How Patching Works

This fork does not maintain hand-edited copies of uBlock Origin's files. Three scripts apply string-based patches at build time, in this order:

| Script | Patches |
|---|---|
| `apply_patches.py` | `!#define` parser and expansion, directive color, auto-rename, element picker search |
| `patch.py` | CodeMirror mobile input fixes (line numbers, gutter helpers, full render) |
| `patch2.py` | Fork name, `!#Collapse` macro, `!#if` end labels, fold memory, search unfold, Gboard cut/delete fix |

`set_update_url.py` then sets the add-on ID and `update_url`.

All three patch scripts are idempotent: a patch already present is skipped. If an upstream change breaks a patch anchor (it must match exactly once), the build fails with a descriptive error. Touched JS files are syntax-checked with `node --check`.

---

## Based On

[uBlock Origin](https://github.com/gorhill/uBlock) by Raymond Hill — GPLv3
