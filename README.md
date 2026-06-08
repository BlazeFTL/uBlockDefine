<h1 align="center">
<sub>
<img src="https://github.com/gorhill/uBlock/blob/master/src/img/ublock.svg" height="38" width="38">
</sub>
uBlockDefine
</h1>

The purpose of this fork is to use https://github.com/uBlockOrigin/uBlock-issues/issues/330#issuecomment-2110930423

check release for Patched file for testing

# uBlockDefine

A fork of [uBlock Origin](https://github.com/gorhill/uBlock) that adds `!#define` macro support for domain list expansion in filter lists.

---

## What's Different

### `!#define` Domain Macros

Define a named group of domains once, use it everywhere:

```adblock
!#define GplinksPartners.com (powergam.online,qrixpe.com,sanadegreecollege.in)

GplinksPartners.com##center, .main-content, .myTimerDiv
GplinksPartners.com##+js(set, document.hidden, false)
*$script,1p,domain=GplinksPartners.com
```

At parse time, `GplinksPartners.com` expands into all three domains — so you write the rule once instead of repeating it for every domain.

### Red Directive Highlighting

`!#define`, `!#if`, `!#include` and other directives are highlighted in **red** in the filter editor for visibility.

### Auto-Rename Macro Usages

When you edit a `!#define` name in the filter editor, all usages of that macro in the list are renamed automatically.

---

## Syntax

```adblock
!#define MacroName (domain1.com,domain2.com,domain3.*)
```

- The macro name can be anything without spaces
- Domains are comma-separated inside `( )`
- Wildcards like `gplinks.*` are supported
- Nest macros inside other macro values

```adblock
!#define Gplinks (gplinks.*,get2.in)
!#define GplinksAll (powergam.online,qrixpe.com,Gplinks)

GplinksAll##.ad-banner
```

---

## Build

Builds are generated automatically via GitHub Actions on every push. Download the latest XPI from [Actions](../../actions) → most recent run → **uBlock0-fork-firefox** artifact.

To create a named release with a direct `.xpi` download (no zip), trigger the workflow manually with **"Create a release"** set to `true`.

---

## How Patching Works

This fork does not maintain a modified copy of uBlock Origin's source. Instead, `apply_patches.py` at the repo root applies targeted string-based patches to a fresh checkout of `gorhill/uBlock` at build time. When gorhill updates upstream, the patches apply on top automatically. If an upstream change conflicts with a patch anchor, the build fails with a descriptive error.

---

## Based On

[uBlock Origin](https://github.com/gorhill/uBlock) by Raymond Hill — GPLv3
