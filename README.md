<h1 align="center">
<sub>
<img src="https://github.com/gorhill/uBlock/blob/master/src/img/ublock.svg" height="38" width="38">
</sub>
uBlockDefine
</h1>

The purpose of this fork is to use https://github.com/uBlockOrigin/uBlock-issues/issues/330#issuecomment-2110930423

Check release for patched file

<img width="702" height="306" alt="Screenshot_20260608-171910_Spark Launcher_1" src="https://github.com/user-attachments/assets/55b63da6-cd56-47d6-805d-e50e86e0a692" />

Element Picker - Add Current Domain To Define Lines Screenshot
<details><summary>Details</summary>
<p>

<img width="702" height="1560" alt="Screenshot_20260608-211723_Spark Launcher" src="https://github.com/user-attachments/assets/ea420f8d-9a87-4f57-9f58-1be642097b3f" />

</p>
</details>

---

# uBlockDefine

A fork of [uBlock Origin](https://github.com/gorhill/uBlock) that adds `!#define` macro support for domain list expansion in filter lists.

In 2018 this was a convenience request. In 2024–25 it's a countermeasure. Link shortner, file hosting, video hosting sites now buy 1-2 domains per day specifically to outpace static filter updates. The only sustainable response is a domain group you update in one place. Maintaining 20+ filter lines each repeating a 10-domain prefix — where that list changes daily — is not a viable workflow.

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


### Define Search Panel


The element picker toolbar includes a search box for your `!#define` lists. Type a macro name to filter matches, then tap **Add Current** to append the current page's domain to that macro and close the picker — without ever opening the filter editor.


---


## Syntax


```adblock
!#define MacroName (domain1.com,domain2.com,domain3.*)
```


- The macro name can be anything without spaces
- Domains are comma-separated inside `( )`
- Wildcards like `gplinks.*` are supported
- Nest macros inside other macro values

Nest Macro Example:
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
