# FGO-AUTO

Automation helper for Fate/Grand Order (TW) on BlueStacks 5. First milestone: Screen state skeleton, then one Quest loop driven by user-supplied anchors.

## Language

### Automation

**Run**:
One full automation execution from script start to normal end or error exit.
_Avoid_: session, job

**Script**:
Code module that drives UI or game flow (recognition, clicks, state machine). Not an in-game story script.
_Avoid_: macro

**Screen state**:
Current screen or battle phase inferred from image recognition or hooks.
_Avoid_: page, view

**State catalog**:
Built-in Screen state names and detectors for the TW main flow (e.g. main menu, terminal, battle, result).
_Avoid_: screen registry, predefined list

**Custom Screen state**:
A Screen state outside the State catalog, usually defined on a Script and detected via Screen anchors.
_Avoid_: user state, extension state

**Screen anchor**:
A reference image used to detect or confirm a Screen state, especially for Custom Screen states.
_Avoid_: state template, UI snippet

**Battle assist**:
During the Battle Screen state, the Script triggers in-game automation (e.g. autoplay) without choosing command cards or noble phantasm strategy.
_Avoid_: auto battle, combat bot

**Combat strategy**:
Rules for selecting command cards, skills, and noble phantasms during battle; not part of the first Quest loop milestone.
_Avoid_: battle AI, deck logic

**Recognition retry**:
A bounded re-attempt to detect the current Screen state before treating recognition as failed.
_Avoid_: poll loop, spin wait

**Run pause**:
The Run halts after recognition fails past the retry budget, keeping context so a human can fix the game UI and resume.
_Avoid_: stop, crash, kill

**Recognition failure**:
Screen state could not be determined within the configured Recognition retry budget.
_Avoid_: timeout, miss

**Stop condition**:
A rule that ends a Run normally when satisfied (Loop limit, AP insufficient, or Manual stop).
_Avoid_: exit criteria, termination policy

**Loop limit**:
The maximum number of Quest loop iterations a Run performs before a normal Run end.
_Avoid_: run count, max battles

**AP check**:
Verification that enough AP exists before each deploy or sortie attempt; insufficient AP triggers a normal Run end.
_Avoid_: stamina check, energy check

**Manual stop**:
User-initiated end of the Run as a normal Run end before other Stop conditions fire.
_Avoid_: cancel, abort, kill

**Normal Run end**:
The Run finished because a Stop condition was met (not because of Run pause).
_Avoid_: success, complete, done

**Quest loop**:
Closed loop for repeating one quest or event (enter, deploy, result, repeat).
_Avoid_: farm script, bot loop

**AP**:
Action Points; automation must check AP before deploying.
_Avoid_: stamina, energy

**Quest anchor**:
A reference image used to find and tap a quest entry or button on the current UI.
_Avoid_: template, quest screenshot, thumbnail

**Anchor set**:
The named Quest anchors available for a Run, merged from Script defaults plus any Run-specific overrides or additions.
_Avoid_: template pack, image bundle

**Script anchor**:
A Quest anchor defined on a Script and used by default when a Run does not override that name.
_Avoid_: default template, bundled image

**Run anchor override**:
A Quest anchor supplied at Run start that replaces or adds to the Script anchor for matching names in that Run only.
_Avoid_: runtime upload, session image

### Environment

**Host**:
The Windows machine running BlueStacks 5 with the TW FGO app installed.
_Avoid_: emulator, device, VM

**Locale**:
The game’s server and UI region; this project targets 台服 (TW).
_Avoid_: server, region, language pack

**Display preset**:
The single fixed width and height of the BlueStacks game window used for capture and image matching on a Host.
_Avoid_: resolution, DPI scale

**Run config**:
The CLI inputs and configuration file that define a Run (Script, Loop limit, Anchor set paths, Recognition retry budget).
_Avoid_: settings file, profile, job spec

**Operator**:
The person who starts and stops Runs via the CLI and may supply Run anchor overrides.
_Avoid_: user, player, master

**Window binding**:
How a Run selects which game window on the Host to capture and control.
_Avoid_: HWND, emulator instance

**Window title rule**:
A substring or pattern in Run config used for Window binding when multiple windows may match.
_Avoid_: title filter, window matcher

**Window pick**:
An interactive CLI step where the Operator chooses one window when Window title rule matches more than one candidate.
_Avoid_: window menu, selector UI

## Relationships

- One Run executes on one Host with TW Locale and a matching Display preset
- Quest anchors and Screen anchors are authored for one Display preset; mismatch on the Host blocks or ends the Run
- The Operator starts a Run through the CLI using a Run config; Manual stop is issued through the CLI
- Window binding uses a Window title rule by default; Window pick is used when multiple windows match
- One Run may contain multiple Quest loop iterations
- Script transitions based on Screen state from the State catalog and any Custom Screen states
- Custom Screen states are typically identified by Screen anchors; built-in states use catalog detectors
- In Battle Screen state, a Script may use Battle assist; Combat strategy is deferred to later milestones
- On Recognition failure after Recognition retries, the Run enters Run pause (not a Normal Run end)
- A Run ends normally when Loop limit, AP check finds insufficient AP, or Manual stop occurs
- A Script declares Script anchors; a Run may apply Run anchor overrides to form the Anchor set
- A Script may use one or more Quest anchors from the Anchor set before entering a Quest loop

### Local data root
The default on-disk workspace for the Desktop app and GUI-edited profiles: data/profiles/<name>/ (run.yaml, script.yaml), data/anchors/ (Phase 2), and logs/ for pause screenshots and frame diagnostics. Not committed; seed from examples/data-profile/ via scripts/init-local-profile.ps1.
_Avoid:_ cloud sync of data/ without operator consent.

### Desktop app
CustomTkinter local window (go-auto-gui) for Run control, Run config editing, capture preview, and logs. Shares the same service layer as the CLI.
_Avoid:_ running GUI integration tests in headless CI.

