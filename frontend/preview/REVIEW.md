# Light redesign — preview for review

Branch `design/light-preview`. Nothing here is live. The three pages you use today
are byte-identical to `main`; this folder is a parallel copy so nobody's demo
breaks while we decide.

Open them at:

```
http://localhost:8000/static/preview/landing.html
http://localhost:8000/static/preview/index.html
http://localhost:8000/static/preview/report.html
```

`landing.html` also opens straight from the file system by double-clicking it.
The other two call `/api/…` and need the server.

---

## What changed — five bullets

1. **The theme is light.** One palette across landing, app and report. Every colour
   is a token, every ratio was computed (table below), and `#3E8F14` — which fails
   AA at 4.08 : 1 and is in `report.html` today — is gone.
2. **The seal is a real vector.** `Brand/New_Logo.svg` was 276 KB of embedded
   raster; `frontend/assets/brand/seal.svg` is 10.7 KB of paths. Ring text is
   outlined, so it no longer depends on a font being installed.
3. **The seal has three jobs and no fourth.** A dated stamp on the report, a quiet
   watermark on the landing hero, a compact lockup in the navbar. It is not
   something a customer puts on their own site — that is the Badge, deferred.
4. **New section: "Warum sollte ich das brauchen?"** Four small-business stories —
   Restaurant, Friseursalon, Physiotherapie, Handwerk — written for someone who
   has never heard the word "prompt".
5. **The mantis head survived the move to light.** Same canvas, same node
   sampling; glow replaced by heavier, darker lines with a pale halo, plus a
   pause button the original never had.

---

## Look at this first

- **The hero on a phone.** The head sits above the headline; check it does not
  crowd the first line.
- **The four stories.** This is the whole point of the session. Do they sound like
  something you would say out loud to a restaurant owner, or like a brochure?
- **The stamp on the report,** and what it says. It states that a test happened,
  when, and under which reference. It never states a verdict.

## Ignore this for now

- **`index.html` (the app) keeps its existing layout.** It got the light system,
  the missing `prefers-reduced-motion` block and corrected tinted backgrounds —
  not a redesign. The landing carries the design direction; the app follows once
  the direction is agreed. Judging its layout now would be judging the old layout
  in new colours.
- **Impressum and Datenschutz still show `{{TOKEN}}` placeholders.** They already
  existed with a TODO banner; I did not touch them. They still load the shared
  dark stylesheet, so they will look dark until the swap.
- The report's sample figures. That page has no scan handed to it, so it renders
  a stored example and says so in a banner.

---

## Decisions I made that were not specified

| Decision | Why |
|---|---|
| **Kept the vetted German copy** on the landing rather than rewriting it | It already avoids every forbidden word and cites Art. 50 correctly. Rewriting from scratch risked losing that for no gain. New copy is confined to the stories section. |
| `--accent` is **one** value, `#256B10` | It has to be both green text and a button fill. 6.18 : 1 as text, 6.58 : 1 under a white label — both clear AA, so the system needs no second green. |
| The lockup carries **rings + head, no ring text** | At 40 px the ring text is unreadable mush. I rendered it to check rather than assuming. |
| `seal.svg` carries `color="#1F5C0E"` as a **presentation attribute** | An SVG loaded through `<img>` is a separate document — `currentColor` has no page to read, so the file rendered black. A presentation attribute still loses to page CSS when the file is inlined. |
| The stamp reads the date with `new Date().toISOString().slice(0,10)` | Copied from `build()` character for character. My first version used local time and printed `18.8.2026` next to a header saying `2026-08-17`, on the same sheet. |
| The masthead mark is **inlined** in the report preview | See "already broken" below. |
| Did **not** touch `Brand/New_Logo.svg` | It is the designer's source file. The app reads only `frontend/assets/brand/`. |

---

## Things that were already true, and the brief did not know

The brief asked me to fix these. I checked each against the code first, and most
were already done. I did not "fix" them again.

| Brief said | Reality |
|---|---|
| Ring text says "SICHERE CHATBOTS" | `New_Logo.png/svg` already read **CHATBOT-PRÜFUNG**. The legal problem was fixed in the source before I got there. |
| `aria-expanded` on finding cards never updates | Already fixed — `index.html:614-619`, with a comment explaining why. |
| Live feed needs `role="log"`, progress bar needs `role="progressbar"` | Both already present (`index.html:301`, `:305`). |
| Fonts are only named in fallback stacks | False. `assets/base.css` has real `@font-face` blocks and the `.woff2` files are in the repo. |
| Stray literals `#14181D`, `#191C22`, `#16171B`, `#08170B`, `rgba(78,132,224…)`, `#FF4D4D` | Zero hits in any HTML file. Already collapsed into tokens. |
| `GRADE_COLOUR` has hardcoded hexes | It uses `var(--critical)` etc. |
| `lang` attributes need setting | Already correct: `de` on landing/impressum/datenschutz, `en` on app/report. |
| Mock-mode banner needed | Already built and wired (`index.html:379`). |
| Impressum/Datenschutz may not exist | Both exist, with `{{TOKEN}}` fields and a TODO banner. |

**Genuinely open, and fixed here:** `prefers-reduced-motion` was missing from
`index.html` **and** `report.html` (the brief named only the report), and
`report.html` had no Impressum/Datenschutz footer links.

---

## Already broken on the live report — not caused by this branch

`report.html:246` loads the masthead mark as
`<img src="/static/assets/brand/mark.svg">`. That file sets `color="#7BE33F"` as
its own default, and an `<img>`-loaded SVG cannot inherit colour from the page.
So on the white sheet the mark renders at **1.5 : 1**. The preview inlines the
same paths and tints them with the page's ink. **The live report has this today.**

---

## Measured contrast — computed here, not copied

Against `--bg #F7F8F5` and against white.

| Token | Hex | on `#F7F8F5` | on white | Role |
|---|---|---|---|---|
| `--ink` | `#111827` | 16.64 | 17.74 | body text |
| `--ink-muted` | `#5A6660` | 5.62 | 5.99 | secondary text |
| `--brand` | `#1F5C0E` | 7.59 | 8.09 | green text, icons |
| `--accent` / `--brand-btn` | `#256B10` | 6.18 | 6.58 | text **and** button fill |
| `--brand-lite` | `#7BE33F` | 1.53 | 1.63 | **decorative shapes only** |
| `--critical` | `#A3200F` | 7.11 | 7.58 | severity |
| `--high` | `#B45309` | 4.71 | 5.02 | severity |
| `--medium` | `#7A5200` | 6.49 | 6.92 | severity |
| ~~`#3E8F14`~~ | | 3.83 | 4.08 | **removed — fails AA** |

White on `#256B10` = 6.58. White on `#A3200F` = 7.58. The favicon's `#4A991E` is
3.58 : 1 on white — a graphic, not text, so it clears the 3 : 1 bar.

---

## A review checklist a non-designer can run

- [ ] `landing.html` opens by double-clicking the file, with no server running
- [ ] Nothing green is unreadable. In particular: no bright green text anywhere
- [ ] The navbar link for the section you are looking at is underlined
- [ ] Tab through the page — you can always see where you are
- [ ] Press "Animation anhalten" — the head stops, and the label flips
- [ ] Turn on Reduce Motion in system settings, reload: the head is a still frame
      and the pause button is hidden
- [ ] Narrow the window to phone width — nothing overlaps, nothing scrolls sideways
- [ ] On the report: Print preview looks like a document, the stamp is on it, and
      the buttons are not
- [ ] The stamp's date and the header's `Issued` date are the same date
- [ ] Open the browser network tab: no request leaves our origin

---

## Open questions, by name

**Kwabena — nothing below ships without you.**
- The **ring text** `LLMANTIS · CHATBOT-PRÜFUNG`. A round seal is the visual
  language of a Prüfsiegel in Germany. This wording states a category, not a
  verdict, and the stamp carries a date and a scan id rather than a grade — but
  the shape still carries an expectation, and that is your call, not mine.
- The **four stories** and every sentence in them carrying a `§` or an `Art.`
  Marked in the source with `<!-- REVIEW: Kwabena -->`: Air Canada (CRT, Feb 2024),
  Art. 33 DSGVO 72 hours, Art. 50 AI Act since 02.08.2026.
- The closing line of the stories section is the only legal claim in that section.
  Is "Ein Bot, der sich dazu überreden lässt, das zu bestreiten, erfüllt das
  nicht" a statement we can stand behind, or does it need softening?

**Bogdan**
- The app keeps its old layout in new colours. Do you want a real redesign pass
  before the swap, or does the landing carry the pitch on its own?
- The seal watermark in the hero sits at 5 % opacity behind the head. Louder,
  quieter, or gone?

**Vlad**
- The report has no date field. `build()` derives it with `new Date()` at render
  time, so a report opened tomorrow prints tomorrow's date. On a document we call
  a Prüfbericht that seems wrong. Should the API return the scan's own timestamp?
- `library_version` came back empty on the sample. The stamp prints
  "Bibliothek nicht angegeben" rather than inventing one.

**Gregor**
- Nothing here needs you. Flagging only that the stamp prints the attack-library
  version, so a library edit is visible on every report from then on.

---

## The swap — one commit, and it is not mine to make

When the team approves:

```bash
git checkout design/light-preview

# 1. the previews become the pages
git mv -f frontend/preview/landing.html frontend/landing.html
git mv -f frontend/preview/index.html   frontend/index.html
git mv -f frontend/preview/report.html  frontend/report.html

# 2. asset paths move up one level (preview/ -> frontend/)
sed -i '' 's|\.\./assets/|/static/assets/|g' \
  frontend/landing.html frontend/index.html frontend/report.html
sed -i '' 's|href="\.\./impressum.html"|href="/static/impressum.html"|g;
           s|href="\.\./datenschutz.html"|href="/static/datenschutz.html"|g' \
  frontend/landing.html frontend/index.html frontend/report.html

# 3. the app's link to the report is same-folder again
sed -i '' 's|href="report.html"|href="/static/report.html"|g' frontend/index.html

# 4. the folder goes
git rm -r frontend/preview

# 5. flip the shared stylesheet so impressum/datenschutz/art50check/scanner
#    stop being dark. PLAYBOOK §3 already describes the light tokens.
#    assets/base.css is the last dark thing standing — that is a separate commit.

git commit -m "design: the product goes light"
```

Step 5 is deliberately not automated. `base.css` is loaded by four pages this
branch never looked at (`art50check.html`, `scanner.html`, `impressum.html`,
`datenschutz.html`), and flipping it blind is exactly the kind of change that
looks fine in a diff and wrong in a browser.

If the team rejects the direction: `git branch -D design/light-preview`. One
folder, nothing lost.
