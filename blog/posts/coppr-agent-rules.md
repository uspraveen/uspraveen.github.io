# The Model Decides, the Tool Does: Three Rules for an Agent That Designs Circuit Boards

> At **Coppr**, Arun and I are building an agent-native EDA tool: you describe the hardware you want, and Coppr works toward a board a factory can build. The first agent we wrote produced files that looked right. This post covers the three rules we rebuilt it around, why each one exists, and the code that holds the agent to them. It is the first in a series on how an agent-native EDA tool actually gets built.

## First, what a circuit board design actually is

If you have never opened an EDA (electronic design automation) tool, here is the whole job in four steps.

<div class="pipeline"><div class="pipeline-step"><span class="pipeline-num">01 / PARTS</span><strong>Pick real components</strong><span>A regulator, a microcontroller, a USB connector, each with a real part number someone sells.</span></div><div class="pipeline-step"><span class="pipeline-num">02 / SCHEMATIC</span><strong>Say what connects to what</strong><span>The netlist: every pin, and the named wire ("net") it belongs to.</span></div><div class="pipeline-step"><span class="pipeline-num">03 / LAYOUT</span><strong>Make it physical</strong><span>Place each part on the board and route copper tracks between pins, layer by layer.</span></div><div class="pipeline-step"><span class="pipeline-num">04 / FAB</span><strong>Hand it to a factory</strong><span>Gerber and drill files: the exact copper, mask and holes the fab will make.</span></div></div>

Rule checks sit between every step. ERC (electrical rules check) catches mistakes like two outputs driving the same wire. DRC (design rules check) catches tracks too close together, or holes too small for the factory to drill. In hardware, a mistake doesn't show up as a stack trace. It shows up weeks later as a board that doesn't power on, plus another fab order.

Coppr runs the same four steps as a compiler pipeline. Agents decide which step runs and with what inputs; every artifact along the way is produced by deterministic code:

<figure><a href="/images/coppr-agent-rules/pipeline.png"><picture><source media="(max-width: 640px)" srcset="/images/coppr-agent-rules/pipeline-m.png"><img src="/images/coppr-agent-rules/pipeline.png" alt="" aria-describedby="cap-pipeline" loading="lazy"></picture></a><figcaption id="cap-pipeline">Coppr's compiler pipeline, from intent to fab outputs</figcaption></figure>

That is why an AI that "looks like it designed a board" is worthless. The only thing that matters is whether the board is right.

## The agent we threw away

Our first harness worked the way most people would guess. A model wrote one Coppr design file. We ran a fixed pipeline over it (compile, check, export), and if a check failed, the model rewrote the file and tried again.

It produced output. It was not an engineer. It couldn't source a part. It couldn't decide that a power rail needed a different topology. It couldn't lay out a board. And it couldn't ask a question. Our internal architecture doc says it plainly: *that is a generator, not an engineer.*

So we rebuilt it as an orchestrator that delegates to specialists. The intake step reads the brief and comes back with constraints and open questions. The orchestrator plans the work. Specialists for parts, power, schematic, symbols, footprints, library, layout, placement, routing, verification, visual review and KiCad interchange each own a slice of the job.

<figure><a href="/images/coppr-agent-rules/orchestrator.png"><picture><source media="(max-width: 640px)" srcset="/images/coppr-agent-rules/orchestrator-m.png"><img src="/images/coppr-agent-rules/orchestrator.png" alt="" aria-describedby="cap-orchestrator" loading="lazy"></picture></a><figcaption id="cap-orchestrator">How Coppr's agents are organized</figcaption></figure>

The structure is the easy part. What made it work was three rules, each enforced in code rather than requested in a prompt.

## Rule 1: The model decides. The tool does.

**No agent writes a netlist, a footprint, a check verdict, or a Gerber.** A model chooses *what* should happen. A deterministic tool does it: the compiler, the rule checkers, the land-pattern generator, the router, the CAM writers.

This isn't a guideline in a prompt. The only way an agent can touch the filesystem is through the tool dispatcher. If a model wants a track on the board, it asks the layout tools for one. Those tools work in integer nanometres and check clearances as they go. A model never gets to type coordinates into a file.

The reason is simple. Language models are excellent at judgment and terrible at being exact a thousand times in a row. A footprint is a few hundred numbers that each have to be exactly right. A Gerber is millions. We want the model doing what only a model can do, like reading a brief, weighing trade-offs, or noticing a missing requirement. Everything else should be work a test can verify byte for byte.

This rule also turned up some funny failures. In August, a run finished and checked its schematic, then stopped and asked the engineer to hand-create the board file for an 80 × 60 mm two-layer board. The design had been carrying those dimensions since the project was created. A CLI command to create the board had existed the whole time, but no agent could reach it. The fix wasn't a smarter prompt. We gave the agent a tool that reads the board size from the design source, writes the board, and refuses to overwrite one that already exists. If the tool doesn't exist, the agent can't do the job, however capable the model is.

Here is what the rule looks like in practice. This is real Coppr output, not an illustration: the demo flight controller from our routing benchmark, routed by Coppr's own deterministic router and passing its DRC with zero errors. No model drew a single one of those tracks.

<figure><a href="/images/coppr-agent-rules/board-real.png"><picture><source media="(max-width: 640px)" srcset="/images/coppr-agent-rules/board-real-m.png"><img src="/images/coppr-agent-rules/board-real.png" alt="" aria-describedby="cap-board-real" loading="lazy"></picture></a><figcaption id="cap-board-real">Real Coppr output: the demo flight controller, routed and DRC-clean</figcaption></figure>

<div class="pull-quote"><svg viewBox="0 0 24 24" fill="#ff5000"><path d="M7 7h4v4H8c0 2 1 3 3 3v3c-3 0-5-2-5-6V7zm8 0h4v4h-3c0 2 1 3 3 3v3c-3 0-5-2-5-6V7z"/></svg><div><p>Language models are excellent at judgment and terrible at being exact a thousand times in a row. So we let them judge, and let tools be exact.</p><cite>Rule 1</cite></div></div>

## Rule 2: Specialists hand back a result, not a transcript

Delegation is for context, not decoration.

A parts specialist might make forty tool calls during one search, querying suppliers, reading specs and rejecting candidates. If all of that flowed back to the orchestrator, its context window would fill with noise by the second delegation. So the transcript never comes back. The orchestrator gets a five-candidate shortlist.

Every specialist returns the same small, typed shape, and it is validated against a schema:

<div class="decision-panel"><div><strong>status</strong><span>One of <code>complete</code>, <code>partial</code> or <code>blocked</code>. Nothing else is accepted.</span></div><div><strong>summary</strong><span>The one paragraph the orchestrator actually reads. Capped at 1,200 characters.</span></div><div><strong>findings</strong><span>The payload the specialist exists for, typed per specialist.</span></div><div><strong>evidence</strong><span>Up to 40 claims, each with a source it rests on.</span></div><div><strong>open_questions</strong><span>Up to 12. This is how a specialist refuses to guess.</span></div></div>

We care most about the last two. The code comment on the schema says why: *a fabricated part number costs more than an admitted gap.* A specialist that can't finish says so in `status`, and can describe the remaining work so the orchestrator can give it more turns and pick up where it stopped.

We test this rather than trusting it. One test runs a full verification delegation. It checks that the specialist's result reaches the orchestrator and that none of the specialist's own tool calls do.

### The tool cap, and the day we got it wrong

The same rule applies to what a specialist can see. Each one gets an allowlist, a slice of the tool catalog narrow enough that the model is choosing between a few plausible tools rather than the whole catalog.

Our first version of this test said no specialist could hold more than **a quarter of the catalog**. It measured the wrong thing. Coppr's catalog has 156 tools today. As it grows toward two hundred, a quarter would be fifty, and a model choosing among fifty tools is not a specialist. What matters is the absolute number a model is choosing between on any one turn, and that shouldn't grow with how much Coppr can do.

So the test now has a fixed ceiling, `MAX_WORKING_SET = 33`, and the comment above it records every time we raised it. It went from 29 to 32 when the via-array generators joined layout, and from 32 to 33 when one deterministic arrange call replaced the dozens of single-part placement calls a first placement used to take. Then the interactive router arrived with four new tools, and we made the split the comment had predicted. Board copper became its own routing specialist with eight tools moved out of layout, which dropped to 25 at the time. (It holds 29 today, and the busiest specialist is now verification, at exactly 33.)

When a specialist hits the ceiling, that tells us the domain wants splitting. That's how the symbol and footprint specialists came out of the library specialist too.

## Rule 3: Success is something a check said, not something a model claimed

This is the rule that makes it safe to let Coppr run on its own.

A run can't report `complete` unless verification passed with zero errors. When the orchestrator submits "complete" without that, the loop intercepts it and hands back a refusal:

> *This run cannot be reported as complete: no verification pass has returned zero errors. Delegate to the 'verification' specialist, fix what it reports, and submit again. If the design genuinely cannot pass, submit with status 'partial' or 'blocked' and say why.*

That is the actual `GATE_REFUSAL` text in the orchestrator. The test that pins it down is almost funny to read. A scripted model declares victory straight away ("board is done"), gets refused, and resubmits as "unverified draft" with status partial. The test asserts the final report says `partial` and `verified: false`.

<figure><a href="/images/coppr-agent-rules/gate.png"><picture><source media="(max-width: 640px)" srcset="/images/coppr-agent-rules/gate-m.png"><img src="/images/coppr-agent-rules/gate.png" alt="" aria-describedby="cap-gate" loading="lazy"></picture></a><figcaption id="cap-gate">The verification gate</figcaption></figure>

The first version of the gate had loopholes, and closing them taught us the most:

- **One clean gate opened the door.** The verification specialist chose which checks to run, so a run could pass by checking less. Now four gates are always required for an electrical design: core rules, the schematic model, cross-view identity, and pre-layout readiness.
- **"Zero errors" can mean "checked nothing."** A power tree with no rails and a simulation that never ran a simulator both report zero errors. A required gate that reports `skipped`, `not_run`, `not_applicable`, `unknown` and the like is treated as absent, not passed.
- **Silence is not success.** If a gate leaves out its error count, it counts as one error.
- **A stale pass is not a pass.** If a source-authoring specialist changes the design, or anyone commits a physical edit to the board, after the last verification, the gate closes again and the refusal says who changed what.
- **A vague refusal makes the agent guess.** "Something failed" makes an agent re-run everything or give up. So the refusal names exactly what is missing.

The core of it is a few lines of Rust:

```rust
for gate in gates {
    let errors = gate.get("errors").and_then(Value::as_u64).unwrap_or(1);
    if errors > 0 {
        shortfall.push(format!("`{}` reported {errors} error(s)", name_of(gate)));
    }
}
```

`unwrap_or(1)` is the whole philosophy in one call. When we don't know, we assume it's broken.

<div class="stat-grid"><div class="stat"><strong>4</strong><span>gates every electrical design must pass</span></div><div class="stat"><strong>33</strong><span>max tools any specialist chooses from</span></div><div class="stat"><strong>0</strong><span>artifacts written by a model directly</span></div></div>

## Why this matters beyond Coppr

None of this is specific to circuit boards. Any agent that produces something with real-world consequences (a migration, a contract, a payment, a building permit) runs into the same three questions. Who actually makes the artifact? What does the coordinator get to see? And who decides when it's done?

Our answers are deterministic tools, typed results, and a check rather than a claim. They make Coppr slower to demo and much harder to fool, including when the one being fooled is us. In hardware we'll take that trade every time.

Next in the series: what happened when we read our own Gerber files back with someone else's reader, and the three fab defects it found.

<p class="source-note">Details are from Coppr's orchestrator source, tests and architecture docs as of October 2026. Quoted strings and limits (GATE_REFUSAL, the result schema caps, MAX_WORKING_SET and its history, the four required gates) are verbatim from the code; tool counts were read from the roster at the current commit. The flight-controller board was routed and checked with Coppr's CLI on October 13, 2026.</p>
