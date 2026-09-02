# TriZ: The Startup That Taught Me What to Build

<img src="/images/triz-pitch-thumb.jpg" alt="TriZ AI pitch video thumbnail" width="100%" style="max-height:420px;object-fit:cover;border:1px solid #e8e8e8;display:block;margin:1.25em 0;" loading="lazy" decoding="async" />

> **TriZ AI (2020)** — my first startup. A privacy-first smart home system that worked in complete isolation from the internet. Co-founded by two graduates with more conviction than experience, pitched on a stage at UPenn, and eventually folded into something bigger. This is the story — and why everything I'm building with Coppr traces back to it.

## "Home is where our heart is"

Those are the first words of our pitch video. It sounds like a greeting, but it was the whole thesis.

It was 2020. The pandemic had collapsed the boundary between home and everything else, and smart home devices were pouring into that collapsed space at a pace nobody was questioning. Every camera, every speaker, every sensor was an ear and an eye with a permanent uplink to someone else's cloud.

I recorded the pitch opening like this: *home is the only place in this whole blue planet where we feel safe and comfortable — now how would it feel when I say that someone might be listening to, or perhaps keeping an eye on, our precious moments at home?*

That was the problem we couldn't unsee. The smart home industry was selling convenience and quietly charging privacy as the subscription fee. We believed that was a design failure, not an inevitability.

So in 2020, as a team of two graduates, we founded TriZ AI on a mission to build a smart home system that was genuinely smart and genuinely private — which, at the time, most people considered a contradiction.

## Building the un-buildable

The core architectural bet was isolation. Not a privacy policy, not a toggle in a settings menu — physical and network isolation from the internet.

The system managed a trade-off between edge and cloud computing, but ran inside a completely private network. Your voice, your routines, your cameras — none of it needed to leave the house to be useful. That single decision bought two things the incumbents couldn't match:

**Security.** You can't breach what you can't reach. With the system isolated from the internet, the attack surface that plagues every mainstream smart home platform simply doesn't exist.

**Reach.** Isolation turned out to be a feature, not a limitation. A system that doesn't depend on fat cloud pipes works beautifully in bandwidth-limited countries — which is exactly where the next hundred million smart homes were going to be built.

And we didn't stop at the software layer. We designed and developed every component indigenously — from the chip to the cloud, including our own communication protocols. It was the hardest engineering I had ever done, and I wouldn't trade it for anything.

## The assistant we actually wanted

A smart home without an intelligent assistant is just a house with expensive light switches. So the second half of TriZ was a native AI assistant that lived inside that private network.

We wanted it to be emotionally intelligent — an assistant customized for every person in the home, one that could help manage mental health, which even then was becoming a sheer need rather than a luxury. And we wanted it speaking the language of its users: while every existing system was English-only, we were building a multilingual assistant supporting five major Indian languages.

The assistant controlled the entire array of smart home devices and acted as a commerce layer too — ordering from e-commerce stores, booking services like cabs, all through simple voice commands, all inside the private network.

## The pitch

In 2021 I stood up at UPenn and delivered this pitch — the problem, the architecture, the market, the business. The full video is here, unlisted until now:

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border:1px solid #e8e8e8;margin:1.5em 0;">
<iframe src="https://www.youtube.com/embed/ko5god90Dm0" title="TriZ AI Video Pitch" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
</div>

The numbers we presented: smart home and smart speaker markets growing at 15.31% and 24.96% CAGR respectively, and the integration of the two — our target market — a 6.4 trillion rupee space in India alone. Three revenue streams: pre-installed smart homes in partnership with construction companies (~40%), the retrofit market — converting "home sweet homes" to "sweet smart homes" — and commissioned orders with in-skill purchases (~30%). The promise was operational too: you call, we send a technical assessment team within 48 hours, and you live in a tailor-made smart home.

Watching it back now, I see two graduates who were right about the problem and naive about everything else. That combination is not the worst thing a first startup can be.

## What actually happened

TriZ didn't become the smart home company we pitched. It became something the pitch was quietly training us to build.

Running an AI infrastructure company — even a small one — forces you down the stack. The smart home work became LearnChain, a cross-cloud ETL and knowledge graph system built on Neo4j and GraphRAG, processing 100K+ nodes. The multimedia pipeline behind the cameras and voice interfaces became Supersense, a large-scale multimedia analysis system. TriZ AI's legacy is the infrastructure layer: the pipelines, the graphs, the systems that move and structure data at scale.

That's the part they don't put in pitch videos. The startup you pitch is rarely the startup you build — but the engineering you do trying to reach the pitch is permanent.

## Why this story ends at Coppr

Here's the part I've wanted to write for a long time.

At TriZ, we designed and developed every component indigenously — including the hardware, from the chip up, with our own protocols. And the tooling for that work in 2020 was brutal. Designing a board, verifying it, iterating on it — every step was manual, slow, and gated behind judgment that lived in specialists' heads. We were a team of two; we felt every one of those gates.

**Coppr is the product we wish we had while building TriZ.** An AI hardware engineer that designs, verifies, and ships real circuit boards — from intent to Gerbers. Where we hand-drew our way through custom hardware, Coppr compiles it. Where we waited days for a verification pass, Coppr runs it continuously.

Every founder has a company they had to build the hard way first. TriZ was mine. Coppr is the shortcut I'm building so the next team of two doesn't have to suffer the way we did.

*TriZ AI, 2020. The first domino.*
