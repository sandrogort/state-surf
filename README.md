# StateSurf

StateSurf turns a PlantUML hierarchical state machine model into generated code that is readable, embedded-friendly, and easy to integrate. Today the generator emits a flat C++11 header, a Rust module, or a Python class, so teams can sketch state charts, regenerate code when the model changes, and keep runtime logic deterministic and traceable.

## Highlights
- Generated-only workflow: edit PlantUML, regenerate `*.hpp` / `*.rs`, never touch emitted code by hand
- Embedded-first runtime: header-only C++11 or `no_std`-friendly Rust with no dynamic allocations, exceptions, or RTTI
- Flattened execution: entry/exit chains and transition specificity resolved ahead of time
- Deterministic IDs: guard/action identifiers are shared by name across the model, so reused logic hits the same hook entry point
- Multi-language output: choose between the C++ (`-l cpp`), Rust (`-l rust`), or Python (`-l python`) templates
- Interactive simulator: spin up a NiceGUI front-end that lets you drive events, answer guards, and watch the diagram update live (`simulate` command)
- Optional tracing: override `statesurf::on_event` / `on_transition` for lightweight logging

## Repository Layout
- `python/statesurf.py` — minimal CLI that parses PlantUML and emits C++/Rust/Python output
- `plantuml/` — example models
- `cpp/generated/` / `rust/generated/` / `python/generated/` — sample generated output used in tests or prototypes
- `doc/requirements.md` — vision and full v1 feature/semantics reference

## Requirements
- Python 3.8+ (stdlib only) and `jinja2`
- PlantUML for authoring state machine diagrams (no runtime dependency)
- A C++11 toolchain for consuming the generated header
- A Rust 1.70+ toolchain (Cargo) if you target the Rust templates
- A Python 3.8+ runtime if you target the Python template
- For the simulator: `nicegui` (pip installable) and the PlantUML CLI (`plantuml` on PATH)

## Quick Start
1. **Model your machine** in PlantUML using the supported subset (deep initials, guards, entry/exit actions, internal transitions, etc.).
2. **Validate the model** to catch syntax issues early:
   ```bash
   python3 python/statesurf.py validate -i plantuml/hsm.puml
   ```
3. **Generate the header/module** for the language you need and choose the surface name:
   ```bash
   python3 python/statesurf.py generate -i plantuml/hsm.puml -o cpp/generated/hsm.hpp -n MyMachine -l cpp
   python3 python/statesurf.py generate -i plantuml/hsm.puml -o rust/generated/hsm.rs -n MyMachine -l rust
   python3 python/statesurf.py generate -i plantuml/hsm.puml -o python/generated/hsm.py -n MyMachine -l python
   python3 python/statesurf.py simulate -i plantuml/hsm.puml --sim-dir sim/hsm -n MyMachine
   ```
4. **Implement callbacks** by providing a type with the expected methods:
  ```cpp
   struct Impl {
     void on_entry(statesurf::State s) { /* GPIOs, logs, ... */ }
     void on_exit(statesurf::State s) { /* cleanup */ }
     bool guard(statesurf::State s, statesurf::Event e, statesurf::GuardId g) {
       /* `g` is the shared name (e.g., GuardId::isFooTrue) */
       return true;
     }
     void action(statesurf::State s, statesurf::Event e, statesurf::ActionId a) {
       /* `a` is the shared name (e.g., ActionId::setFooFalse) */
     }
   };
  ```
5. **Run the machine**:
  ```cpp
   Impl impl;
   statesurf::MyMachine<Impl> machine(impl);
   machine.dispatch(statesurf::Event::A);
  ```

   For Python, implement a subclass of `MyMachineCallbacks`, then pass an instance into `MyMachine(callbacks)` and call `dispatch` with `MyMachineEvent` values.

   To launch the simulator, `cd sim/hsm && python3 simulator.py`, then open the served UI. Select events from the dropdown, step through reactions, answer guard prompts, and watch the PlantUML diagram render the active state, exits, and entries.

The machine caches its current `State`, automatically executes entry/exit/action callbacks, and ignores events with no matching transition. Final transitions mark the machine as terminated so later dispatches become no-ops.

## Simulator Environment
- Simulator dependencies are captured in `requirements-simulator.txt` (`nicegui` and friends).
- Generating a simulator (`python3 python/statesurf.py simulate ...`) automatically creates a local `.venv` inside the output folder and installs those packages. The venv is *not* committed—rerun the command or install with `pip install -r requirements-simulator.txt` if you need a fresh environment.
- Run the simulator with the bundled interpreter, e.g. `./sim/hsm/.venv/bin/python simulator.py` (or `Scripts\\python.exe` on Windows).

## Modeling Notes
- Initial transitions may target deep descendants and may carry actions
- Internal/self transitions are supported via either `state : Event` or `state -> state : Event`
- Empty entry/exit/action bodies are allowed and will still call into callbacks without an `ActionId`
- Guard/action enums collapse identical names, so reuse `isDoorClosed` or `setFooTrue` freely across states
- Final transitions (`state --> [*]`) terminate the machine; use `terminated()` to query

## PlantUML Syntax Rules
- Identifiers for states, events, guards, and actions must match `[A-Za-z_]\w*`; punctuation such as `?`, `-`, or `()` is rejected at parse time
- `entry` / `exit` lines support the form `State : entry / ActionName`; guards on entry/exit and dangling `/` are invalid
- Internal transitions treat `entry` and `exit` as reserved keywords—use dedicated entry/exit syntax instead

For the full set of guarantees, limitations, and v1 roadmap, read `doc/requirements.md`.

## Development
- The generator currently ships with C++, Rust, and Python templates; templating keeps adding additional targets straightforward.
- Tests and demos live next to the generated headers; keep them building against regenerated output to catch regressions.
- Contributions welcome! Open issues/PRs that expand the PlantUML subset, improve codegen readability, or tighten validation.
- Run `script/test_all.sh` to regenerate code for both languages, build the C++ and Rust artifacts, and execute both test suites in one step.
