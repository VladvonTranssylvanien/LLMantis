<table>
  <tr>
    <td valign="middle">
      <img src="Brand/llmantis-seal.svg" alt="LLMantis logo" width="100">
    </td>
    <td valign="middle">
      <h1 style="font-size: 80px;"><span style="color: #008822;">LL</span>Mantis</h1>
    </td>
  </tr>
</table>



### A penetration and compliance test for AI chatbots.

**Your chatbot speaks for your company**. Nobody has ever checked what it says under
pressure.

LLMantis connects to a chatbot, runs a library of documented attacks against it,
has a separate judge model rule on every answer, and returns a risk score, a
grade from A to F, and a Prüfbericht (test report) containing the exact quote
that proves each finding and a concrete fix for it.

We are black box. We never read source code, never connect to a repository and
never show code in a report. We test behaviour.


---

## The problem

A chatbot's answer is a statement by the company that deployed it.

In February 2024 the British Columbia Civil Resolution Tribunal held **Air
Canada** liable for a refund policy its support chatbot had invented. The
airline argued the bot was a separate entity, responsible for its own words.
The tribunal rejected that explicitly.

That is the risk model in one case. An LLM placed in front of customers can:

- **leak data** — its own instructions, internal pricing, a supplier's name,
  another customer's details
- **invent commitments** — a discount, a refund, a delivery date that becomes a
  dispute
- **say something discriminatory or harmful** — under the company's name, in the
  company's colours

A regulatory floor arrived on top of that. Since **02.08.2026**, Art. 50(1) of
the EU AI Act (Regulation (EU) 2024/1689) requires that a person interacting
with an AI system be informed of it, unless that is obvious from the context.
The Digital Omnibus delayed the high-risk obligations; it did not delay Art. 50.
The penalty ceiling under Art. 99 is up to €15M or 3 % of worldwide turnover.

Almost nobody sells a defence: in the ECA European Cybersecurity Mapping 2025,
AI Security and Integrity holds **7 of 828** European vendors — 0.8 %, the
emptiest segment on the map.

## Why a code scanner cannot find this

The vulnerability does not live in the code. It lives in the text.

A static analyser can prove your inputs are escaped and your dependencies are
patched, and it will never find that your bot hands over its system prompt if
you ask politely, or that it grants a full refund to anyone who claims to be a
team leader. The exploit is a sentence, so finding it needs a dynamic, black-box
method with an attack library and a judge, not a parser. It also means the same
bot can answer differently to the same sentence twice — which is why the method
itself has to be measured rather than asserted.

---

## Two layers

| | Art. 50 Check | Red team Prüfung |
|---|---|---|
| Method | Passive: reads one public page | Active: sends real attacks to the bot |
| Price | Free | Paid |
| Role | Lead funnel | The product |

The split exists for a legal reason: attacking a bot you do not own is not a
product, it is an offence. The free layer needs no permission at all, so it can
run on a prospect's site before any conversation exists.

## The free Art. 50 Check

**Why.** It answers a question a German compliance manager already has, in a few
seconds, without a sales call. And every site that fails it is a named,
evidenced lead — which is what makes it a funnel rather than a giveaway.

**How.** One GET of the public page, as an ordinary visitor with an identifiable
user agent. No message is ever sent to the bot, so no permission is required and
no provider's terms are breached. `robots.txt` is honoured, and the URL is
SSRF-guarded — private, loopback, link-local and cloud-metadata addresses are
rejected, re-checked on every redirect hop. Check [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) for more information.

Four findings, each with evidence and a fix:

- `widget_found` — is there a chat widget at all (nine vendor signatures:
  Intercom, Tidio, Userlike, Crisp, Drift, Zendesk, Freshchat, LiveChat, generic)
- `ai_disclosure` — does the widget disclose that it is AI on first contact
- `privacy_link` — is a privacy policy reachable beside it
- `impressum` — § 5 DDG


### Using it on the website


1. **Go to [llmantis.de](https://llmantis.de)**, scroll down to the Art.-50-Check and click on **"Jetzt prüfen ->"**.

<img src="Screenshots/SS_003.png" alt="1" width="300">


2. **Paste a web address, you want to check.** For example: "otto.de".

<img src="Screenshots/SS_010.png" alt="2" width="400">


3. Press **Check now**. It reads the page and lists what it found: chat widget, AI disclosure, privacy link, Impressum. No account, and nothing is sent to the bot.

<img src="Screenshots/SS_008.png" alt="3" width="400">


4. Check the result and open the PDF report.

<img src="Screenshots/SS_009.png" alt="4" width="400">

---

## The red team Prüfung

**Why.** Art. 50 is a label on the outside of the box: it asks whether you told
the user it was a bot. This asks what the bot does when someone actually tries —
which is where the Air Canada class of liability lives, and no label prevents it.

**How.** The scanner runs automated attacks against the target bot and judges the response with a calibrated AI. Check [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) for more information.

### Using it on the website

1. **Go to [llmantis.de](https://llmantis.de)**, scroll down to the Starter-tier and click on **"Prüfung starten ->"**.

<img src="Screenshots/SS_001.png" alt="1" width="300">


2. **Choose 'live endpoint or 'system prompt'.**

<img src="Screenshots/SS_014.png" alt="2" width="400">

For live endpoint:
**Paste your bot's web address.** Use 'https://phishing.workshop.bogdanorel.de/', because this is the only site whitelisted until we add owner verification. 

<img src="Screenshots/SS_015.png" alt="2" width="400">

Alternatively you can test a custom system prompt or one of our three preconfigured bots on our LLM.

<img src="Screenshots/SS_007.png" alt="3" width="400">

<img src="Screenshots/SS_002.png" alt="4" width="400">

Optionally name a canary — a string that must never appear in an answer. That is what makes a leak deterministic instead of a judgement.

<img src="Screenshots/SS_004.png" alt="5" width="400">


3. Press **Run scan**. Attacks stream in with a verdict each, twice over, and the worse of the two passes becomes the report.

<img src="Screenshots/SS_011.png" alt="6" width="400">

<img src="Screenshots/SS_013.png" alt="6" width="400">


4. Open the Prüfbericht: the grade, every finding with the bot's own words as evidence, the fix, the coverage, and the attack library version.

<img src="Screenshots/SS_012.png" alt="8" width="400">

---

# Governance and Compliance

[LLMantis Governance V2](governance/README.md) is an evidence-based technical governance framework for the LLMantis platform. It assesses 17 controls across the frontend and backend, each independently verified against the current codebase — implementation, configuration, and enforcement — rather than against documentation or intent alone.

<img src="Screenshots/SS_016.png" alt="9" width="400">

---

# Where this goes next

**Built, not wired.** Registration and login (bcrypt, JWT, per-account lockout).
Organizations with owner/admin/member ranks on fifteen endpoints. API keys,
hashed at rest. Domain ownership verification by DNS TXT, which already gates
active scans. White-label branding. Scan history. Attack library reload. All of it
works over the API; none of it has a screen.

**The gaps, honestly.** API keys and roles can only be created with curl today.
`Target.retention` is a column, not a deletion routine.

**Outside the product.** `tools/voice50` judges Art. 50 disclosure for voice bots,
8 of 8 fixtures, but places no call: the Twilio transport needs a paid account.
`tools/art50v2` and `calibration/` run by hand.

**Next.** A larger attack library, which is data rather than engine work. An
attacking model that reads the target's own answers instead of replaying a fixed
list. Multi-turn attacks, scheduled re-scans, WhatsApp and Telegram.

## Licence

Licensed under **AGPL-3.0** (see `LICENSE`) rather than MIT for one reason: this
repository is public and the product is sold as a hosted service, so a competitor
who runs this code as a service must publish their changes.
