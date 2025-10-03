# StateSurf v1 — Requirements

## Vision
A playful, low-ceremony state machine generator.  
Define an HSM in PlantUML → get flat, efficient, readable generated code for C++11 or Rust.  
Target: embedded systems with no dependencies beyond the selected language runtime.

## Core Principles
- KISS: minimal ceremony  
- Generated-only: code is not edited, only regenerated, but must remain human-readable and easy to debug  
- Flat runtime: no dynamic hierarchy traversal; entry/exit chains are precomputed at generation  
- Embedded-friendly: generated code avoids dynamic allocation, exceptions, and RTTI (C++), and remains `no_std`-friendly for Rust  
- Deterministic: same model → same code  
- Traceable: optional hooks for debugging  

## PlantUML Subset (v1)
- Simple states, composite states, initial/final  
- Transitions with `[guard] / action`  
- Entry/exit actions (`state : entry / Action`)  
- Nested states allowed, but entry/exit execution is flattened  
- No history, timeouts, or junctions in v1  

### Identifier Rules
- State, event, guard, and action names must match `[A-Za-z_]\w*`
- Entry/exit declarations do not accept guards; `state : entry [guard] / action` is rejected
- Internal transitions treat `entry` and `exit` as reserved keywords and reject guards/actions when used that way

## PlantUML Subset (v1) — Additions
- Initial transitions may target **deep descendants** (e.g., `[*] --> s2.s21.s211`) at any scope, including root
- Initial transitions may have **actions** (e.g., `[*] --> s2 : / setFooFalse`)
- Empty `entry`/`exit` declarations are valid (call `on_entry`/`on_exit` with **no** `ActionId`)
- Empty internal actions are valid (e.g., `s1 : I /` → no `ActionId`)
- Internal/self transitions: both `state : E ...` and `state -> state : E ...` are supported
- Final transitions allowed: `state --> [*] : EVENT` (machine becomes terminal; later `dispatch` calls are ignored)

## Semantics — Clarifications
- **Normalization of deep initials:** generator computes the leaf target and emits a precomputed `enter` chain (root → … → leaf). If the target is a composite without a leaf, descend via its own initial(s).
- **Initial action timing:** initial transition action runs **after** parent entry of the source scope and **before** entering the target chain.
- **Specificity:** when multiple transitions match, the more specific (deeper state) wins.

## Generated Code Design

### Shared Concepts
- Deterministic `State`, `Event`, `GuardId`, and `ActionId` enumerations keyed off PlantUML identifiers
- Hooks interface/trait that applications implement to provide guard/action bodies and observe entry/exit transitions
- Optional tracing callbacks (`on_event`, `on_transition`) for lightweight logging/instrumentation
- Precomputed entry/exit chains so dispatch never walks the hierarchy at runtime

### C++11 Output
```cpp
enum class State { … };
enum class Event { … };
enum class GuardId { … };
enum class ActionId { … };

struct IHooks {
  virtual ~IHooks() {}
  virtual void on_entry(State) = 0;
  virtual void on_exit(State) = 0;
  virtual bool guard(State, Event, GuardId) = 0;
  virtual void action(State, Event, ActionId) = 0;
};

class StateSurfMachine {
public:
  explicit StateSurfMachine(IHooks& impl);
  void reset();
  void dispatch(Event e);
  State state() const;
  bool started() const;
  bool terminated() const;
};
```
- Generated code avoids dynamic allocation, exceptions, and RTTI
- `on_event` / `on_transition` are emitted as weak symbols so applications can override them

### Rust Output
- Mirrors the same enums (`State`, `Event`, `GuardId`, `ActionId`)
- Emits a `Hooks` trait with `on_entry`, `on_exit`, `guard`, and `action`
- `Machine` struct stores state, exposes `new`, `reset`, `dispatch`, `state`, `started`, and `terminated`
- Tracing hooks (`on_event`, `on_transition`) are provided as trait default methods
- Designed to be `no_std` friendly: no heap allocation and only `core` dependencies

## CLI
- `python3 python/statesurf.py generate -i model.puml -o out.hpp -l cpp`
- `python3 python/statesurf.py generate -i model.puml -o out.rs -l rust`
- `python3 python/statesurf.py validate -i model.puml` (syntax validation with line-level diagnostics)

## Implementation Details
- Header-only output for C++; single-module output for Rust  
- Text-templating architecture, so adding new languages later is easy  
- Guards/actions/entries/exits generate IDs by name → repeated labels reuse the same enum value  
- Generated code prioritizes readability; the compiler performs optimization  

## Out of Scope (v1)
- Timeouts, history, orthogonal regions  
- Payloaded events (enum-only)  
- Source/header split (h+cpp)  
- Concurrency  
