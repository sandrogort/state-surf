# StateSurf

StateSurf turns a PlantUML hierarchical state machine model into a single, flat, C++11 header that is readable, embedded-friendly, and easy to integrate. It is built for teams who sketch state charts, regenerate code when the model changes, and keep runtime logic deterministic and traceable.

## Highlights
- Generated-only workflow: edit PlantUML, regenerate `*.hpp`, never touch emitted code by hand
- Embedded-first runtime: header-only, C++11, no dynamic allocations, exceptions, or RTTI
- Flattened execution: entry/exit chains and transition specificity resolved ahead of time
- Deterministic IDs: guard/action identifiers stay stable per model, simplifying hook implementations
- Optional tracing: override `statesurf::on_event` / `on_transition` for lightweight logging

## Repository Layout
- `python/statesurf.py` — minimal CLI that parses PlantUML and emits C++ headers
- `plantuml/` — example models (see `hsm.puml`)
- `cpp/generated/` — sample generated output used in tests or prototypes
- `doc/requirements.md` — vision and full v1 feature/semantics reference

## Requirements
- Python 3.8+ (stdlib only)
- PlantUML for authoring state machine diagrams (no runtime dependency)
- A C++11 toolchain for consuming the generated header

## Quick Start
1. **Model your machine** in PlantUML using the supported subset (deep initials, guards, entry/exit actions, internal transitions, etc.).
2. **Validate the model** to catch syntax/semantic issues early:
   ```bash
   python3 python/statesurf.py validate -i plantuml/hsm.puml
   ```
3. **Generate the header** and choose the class name you want in C++:
   ```bash
   python3 python/statesurf.py generate -i plantuml/hsm.puml -o cpp/generated/hsm.hpp -n MyMachine
   ```
4. **Implement hooks** by inheriting from `statesurf::IHooks`:
   ```cpp
   struct Impl : statesurf::IHooks {
     void on_entry(statesurf::State s) override { /* GPIOs, logs, ... */ }
     void on_exit(statesurf::State s) override { /* cleanup */ }
     bool guard(statesurf::State s, statesurf::Event e, statesurf::GuardId g) override {
       /* return decision */
     }
     void action(statesurf::State s, statesurf::Event e, statesurf::ActionId a) override {
       /* side effects */
     }
   };
   ```
5. **Run the machine**:
   ```cpp
   Impl impl;
   statesurf::MyMachine machine(impl);
   machine.dispatch(statesurf::Event::A);
   ```

The machine caches its current `State`, automatically executes entry/exit/action hooks, and ignores events with no matching transition. Final transitions mark the machine as terminated so later dispatches become no-ops.

## Modeling Notes
- Initial transitions may target deep descendants and may carry actions
- Internal/self transitions are supported via either `state : Event` or `state -> state : Event`
- Empty entry/exit/action bodies are allowed and will still call into hooks without an `ActionId`
- Final transitions (`state --> [*]`) terminate the machine; use `terminated()` to query

For the full set of guarantees, limitations, and v1 roadmap, read `doc/requirements.md`.

## Development
- The generator currently focuses on a single-language (C++) pipeline. Templating keeps adding other targets straightforward.
- Tests and demos live next to the generated headers; keep them building against regenerated output to catch regressions.
- Contributions welcome! Open issues/PRs that expand the PlantUML subset, improve codegen readability, or tighten validation.
