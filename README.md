# StateSurf

StateSurf turns a PlantUML hierarchical state machine model into generated code that is readable, embedded-friendly, and easy to integrate. Today the generator emits a flat C++11 header, a Rust module, or a Python class, so teams can sketch state charts, regenerate code when the model changes, and keep runtime logic deterministic and traceable.

## Highlights
- Generated-only workflow: edit PlantUML, regenerate `*.hpp` / `*.rs`, never touch emitted code by hand
- Embedded-first runtime: header-only C++11 or `no_std`-friendly Rust with no dynamic allocations, exceptions, or RTTI
- Flattened execution: entry/exit chains and transition specificity resolved ahead of time
- Deterministic IDs: guard/action identifiers are shared by name across the model, so reused logic hits the same hook entry point
- Multi-language output: choose between the C++ (`-l cpp`), Rust (`-l rust`), or Python (`-l python`) templates
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
   ```
4. **Implement hooks** by inheriting from `statesurf::IHooks`:
   ```cpp
   struct Impl : statesurf::IHooks {
     void on_entry(statesurf::State s) override { /* GPIOs, logs, ... */ }
     void on_exit(statesurf::State s) override { /* cleanup */ }
     bool guard(statesurf::State s, statesurf::Event e, statesurf::GuardId g) override {
       /* `g` is the shared name (e.g., GuardId::isFooTrue) */
       }
     void action(statesurf::State s, statesurf::Event e, statesurf::ActionId a) override {
       /* `a` is the shared name (e.g., ActionId::setFooFalse) */
       }
   };
   ```
5. **Run the machine**:
   ```cpp
   Impl impl;
   statesurf::MyMachine machine(impl);
   machine.dispatch(statesurf::Event::A);
   ```

   For Python, implement a subclass of `MyMachineHooks`, then pass an instance into `MyMachine(hooks)` and call `dispatch` with `MyMachineEvent` values.

The machine caches its current `State`, automatically executes entry/exit/action hooks, and ignores events with no matching transition. Final transitions mark the machine as terminated so later dispatches become no-ops.

## Modeling Notes
- Initial transitions may target deep descendants and may carry actions
- Internal/self transitions are supported via either `state : Event` or `state -> state : Event`
- Empty entry/exit/action bodies are allowed and will still call into hooks without an `ActionId`
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
