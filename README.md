<<<<<<< HEAD
=======
[![Badge Commits]][Commit Rate]
[![Badge Issues]][Issues]
[![Badge Localization]][Crowdin]
[![Badge License]][License]
[![Badge NPM]][NPM]
[![Badge Mozilla]][Mozilla]
![Badge Chrome]
[![Badge Edge]][Edge]

***

>>>>>>> upstream/master
<h1 align="center">
<sub>
<img src="https://github.com/gorhill/uBlock/blob/master/src/img/ublock.svg" height="38" width="38">
</sub>
uBlockDefine
</h1>

<<<<<<< HEAD
The purpose of this fork is to use https://github.com/uBlockOrigin/uBlock-issues/issues/330#issuecomment-2110930423
=======
| Browser   | Install from ... | Status |
| :-------: | ---------------- | ------ |
| <img src="https://github.com/user-attachments/assets/b0136512-56a5-4856-8c50-4971c957a24f" alt="Get uBlock Origin for Firefox"> | <a href="https://addons.mozilla.org/addon/ublock-origin/">Firefox Add-ons</a> | [uBO works best on Firefox](https://github.com/gorhill/uBlock/wiki/uBlock-Origin-works-best-on-Firefox) |
| <img src="https://github.com/user-attachments/assets/3a7569f8-688b-4eb1-a643-8d0fe173aefe" alt="Get uBlock Origin for Microsoft Edge"> | <a href="https://microsoftedge.microsoft.com/addons/detail/ublock-origin/odfafepnkmbhccpbejgmiehpchacaeak">Edge Add-ons</a> | <a href="https://blogs.windows.com/msedgedev/2026/08/07/moving-the-microsoft-edge-extensions-ecosystem-forward-with-manifest-version-3/">"Moving the Microsoft Edge extensions ecosystem forward with Manifest Version 3"</a>: "Beginning in August 2026, Microsoft Edge will start the consumer transition away from Manifest Version 2 (MV2) extensions and toward MV3. Our goal is to complete the consumer transition by the end of 2026, with enterprise deprecation following in early 2027." |
| <img src="https://github.com/user-attachments/assets/938f080c-fe64-4e48-8b89-4bfceabb56e6" alt="Get uBlock Origin for Opera"> | <a href="https://addons.opera.com/extensions/details/ublock/">Opera Add-ons</a> |
| <img src="https://github.com/user-attachments/assets/5463ef88-873b-4516-8514-5277664cfde7" alt="Get uBlock Origin for Chromium"> | Removed | <a href="https://developer.chrome.com/docs/extensions/develop/migrate/mv2-deprecation-timeline#aug_31st_2026_all_remaining_manifest_v2_extensions_removed_from_the_chrome_web_store">"Manifest V2 support timeline"</a>: "Aug 31st 2026: All remaining Manifest V2 extensions removed from the Chrome Web Store"<br><a href="https://github.com/uBlockOrigin/uBlock-issues/wiki/About-Google-Chrome's-%22This-extension-may-soon-no-longer-be-supported%22">About Google Chrome's "This extension may soon no longer be supported"</a> |
| <img src="https://github.com/user-attachments/assets/2e9037c4-836d-44c1-a716-ba96e89daaff" alt="Get uBlock Origin for Thunderbird"> | <a href="https://addons.thunderbird.net/thunderbird/addon/ublock-origin/">Thunderbird Add-ons</a> | [No longer updated and stuck at 1.49.2.](https://github.com/uBlockOrigin/uBlock-issues/issues/2928) Later versions require "GitHub - Releases". |
| <img src="https://upload.wikimedia.org/wikipedia/commons/c/c2/GitHub_Invertocat_Logo.svg" height="50" alt="Get uBlock Origin through GitHub"> | <a href="https://github.com/gorhill/uBlock/releases">GitHub - Releases</a> | Stable and development versions on Firefox, Chromium MV2, and Thunderbird. Must be placed manually into web browsers; the Chromium and Thunderbird versions usually won't auto-update.
>>>>>>> upstream/master

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


<<<<<<< HEAD
### `!#define` Domain Macros
=======
***

uBlock Origin (uBO) is a CPU and memory-efficient [wide-spectrum content blocker][Blocking] for Chromium and Firefox. It blocks ads, trackers, coin miners, popups, annoying anti-blockers, malware sites, etc., by default using [EasyList][EasyList], [EasyPrivacy][EasyPrivacy], [Peter Lowe's Blocklist][Peter Lowe's Blocklist], [Online Malicious URL Blocklist][Malicious Blocklist], and uBO [filter lists][uBO Filters]. There are many other lists available to block even more. Hosts files are also supported. uBO uses the EasyList filter syntax and [extends][Extended Syntax] the syntax to work with custom rules and filters.

You may easily unselect any preselected filter lists if you think uBO blocks too much. For reference, Adblock Plus installs with only EasyList, ABP filters, and Acceptable Ads enabled by default.

It is important to note that using a blocker is **NOT** [theft]. Do not fall for this creepy idea. The _ultimate_ logical consequence of `blocking = theft` is the criminalization of the inalienable right to privacy.

Ads, "unintrusive" or not, are just the visible portion of the privacy-invading means entering your browser when you visit most sites. **uBO's primary goal is to help users neutralize these privacy-invading methods** in a way that welcomes those users who do not wish to use more technical means.

***

* [Documentation](#documentation)
* [Installation](#installation)
  * [Firefox](#firefox)
  * [Chromium](#chromium)
  * [Thunderbird](#thunderbird)
  * [All Programs](#all-programs)
  * [Enterprise Deployment](#enterprise-deployment)
* [Release History](#release-history)
* [Translations](#translations)
* [About](#about)

## Documentation

<table>
    <thead>
        <tr>
            <th>Basic Mode</th>
            <th>Advanced Mode</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The <a href="https://github.com/gorhill/uBlock/wiki/Quick-guide:-popup-user-interface">simple popup user interface</a> for an install-it-and-forget-it type of installation that is configured optimally by default.</td>
            <td>The <a href="https://github.com/gorhill/uBlock/wiki/Dynamic-filtering:-quick-guide">advanced popup user interface</a> includes a point-and-click firewall that is configurable on a per-site basis.</td>
        </tr>
        <tr>
            <td align="center" valign="top"><a href="https://github.com/gorhill/uBlock/wiki/Quick-guide:-popup-user-interface"><img src="https://user-images.githubusercontent.com/585534/232531044-c4ac4dd5-0b60-4c1e-aabb-914be04b846c.png"/></a></td>
            <td align="center" valign="top"><a href="https://github.com/gorhill/uBlock/wiki/Dynamic-filtering:-quick-guide"><img src="https://user-images.githubusercontent.com/585534/232531439-a8f81cc3-6622-45c4-8b32-7348cecf6e98.png"/></a></td>
        </tr>
    </tbody>
</table>

Visit the [Wiki][Wiki] for documentation.

For support, questions, or help, visit [/r/uBlockOrigin][Reddit].

## Installation

[Required Permissions][Permissions]

#### Firefox

[Firefox Add-ons][Mozilla]

[Development Builds][Beta]

uBO [works best][Works Best] on Firefox and is available for desktop and Android versions.

#### Chromium

Chrome Web Store: Removed on 2026-08-31

[Microsoft Edge Add-ons][Edge] (Published by [Nicole Rolls][Nicole Rolls] until version 1.62. Ownership transfer at version 1.64.)

[Opera Add-ons][Opera]

uBO should be compatible with any Chromium-based browser.

#### Thunderbird

[Thunderbird Add-ons][Thunderbird]

In Thunderbird, uBlock Origin does not affect emails, just feeds.

#### All Programs

Do **NOT** use uBO with any other content blocker. uBO [performs][Performance] as well as or better than most popular blockers. Other blockers can prevent uBO's privacy or anti-blocker-defusing features from working correctly.

[Manual Installation][Manual Installation]

#### Enterprise Deployment

[Deploying uBO][Deployment]

## Release History

[Releases Page][Releases]

## Translations

Help translate uBO via [Crowdin][Crowdin].

## About

[Manifesto][Manifesto]

[Privacy Policy][Privacy Policy]

[GPLv3 License][License]

Free. Open-source. For users by users. No donations sought.

If you ever want to contribute something, think about the people working hard to maintain the filter lists you are using, which are available to use by all for free.
>>>>>>> upstream/master


Define a named group of domains once, use it everywhere:

<<<<<<< HEAD
=======
[Peter Lowe's Blocklist]: https://pgl.yoyo.org/adservers/
[Malicious Blocklist]: https://gitlab.com/malware-filter/urlhaus-filter#malicious-url-blocklist
[Performance]: https://www.debugbear.com/blog/chrome-extensions-website-performance#the-impact-of-ad-blocking-on-website-performance
[EasyPrivacy]: https://easylist.to/#easyprivacy
[Thunderbird]: https://addons.thunderbird.net/thunderbird/addon/ublock-origin/
[EasyList]: https://easylist.to/#easylist
[Mozilla]: https://addons.mozilla.org/addon/ublock-origin/
[Crowdin]: https://crowdin.com/project/ublock
[Reddit]: https://www.reddit.com/r/uBlockOrigin/
[Theft]: https://x.com/LeaVerou/status/518154828166725632
[Opera]: https://addons.opera.com/extensions/details/ublock/
[Edge]: https://microsoftedge.microsoft.com/addons/detail/ublock-origin/odfafepnkmbhccpbejgmiehpchacaeak
[NPM]: https://www.npmjs.com/package/@gorhill/ubo-core
>>>>>>> upstream/master

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


Builds are generated automatically via GitHub Actions on every push. Download the latest XPI from [Actions](../../actions) → most recent run → **uBlock0-fork-firefox** artifact. (Unsigned Builds)

For Signed Build Head On To Release Section

To create a named release with a direct `.xpi` download (no zip), trigger the workflow manually with **"Create a release"** set to `true`.


---


## How Patching Works


This fork does not maintain a modified copy of uBlock Origin's source. Instead, `apply_patches.py` at the repo root applies targeted string-based patches to a fresh checkout of `gorhill/uBlock` at build time. When gorhill updates upstream, the patches apply on top automatically. If an upstream change conflicts with a patch anchor, the build fails with a descriptive error.


---


## Based On


[uBlock Origin](https://github.com/gorhill/uBlock) by Raymond Hill — GPLv3
