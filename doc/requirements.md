# StateSurf v1 — Requirements

## Vision
A playful, low-ceremony state machine generator.  
Define an HSM in PlantUML → get flat, efficient, readable C++11 header-only code.  
Target: embedded systems with no dependencies.

## Core Principles
- KISS: minimal ceremony  
- Generated-only: code is not edited, only regenerated, but must remain human-readable and easy to debug  
- Flat runtime: no dynamic hierarchy traversal; entry/exit chains are precomputed at generation  
- Embedded-friendly: C++11, no dynamic allocation, no exceptions, no RTTI  
- Deterministic: same model → same code  
- Traceable: optional hooks for debugging  

## PlantUML Subset (v1)
- Simple states, composite states, initial/final  
- Transitions with `[guard] / action`  
- Entry/exit actions  
- Nested states allowed, but entry/exit execution is flattened  
- No history, timeouts, or junctions in v1  

## Generated C++ Design

### Enums
```cpp
enum class State { … };
enum class Event { … };
enum class GuardId { … };
enum class ActionId { … };
```

### Interface
Exactly four pure virtual methods:
```cpp
struct IHooks {
  virtual ~IHooks() {}
  virtual void on_entry(State) = 0;
  virtual void on_exit(State) = 0;
  virtual bool guard(State, Event, GuardId) = 0;
  virtual void action(State, Event, ActionId) = 0;
};
```

### Machine Class
```cpp
class StateSurfMachine {
public:
  explicit StateSurfMachine(IHooks& impl);
  void reset();              // go to initial state, call entry
  void dispatch(Event e);    // process one event
  State state() const;       // current state
};
```

- Stores current `State`  
- Calls into `IHooks` using `GuardId` and `ActionId`, with precomputed entry/exit chains  
- If no transition matches → silently ignored  
- If multiple guards match → pick most specific state  
- If no guard true → silently ignored  

### Tracing
Non-virtual free functions, weak-linked defaults:
```cpp
void on_event(State, Event);
void on_transition(State from, State to, Event e);
```
User can override by providing definitions.

## CLI
- `statesurf generate -i model.puml -o out/ -l cpp`  
- `statesurf validate -i model.puml`  
- Hard fail on unreachable states, missing initial, ambiguous transitions  

## Implementation Details
- Header-only: one `.hpp` per machine (v1)  
- Text-templating architecture, so adding new languages later is easy  
- Guards/actions/entries/exits generate unique IDs → enforced completeness  
- Generated code prioritizes readability; compiler does the optimization  

## Out of Scope (v1)
- Timeouts, history, orthogonal regions  
- Payloaded events (enum-only)  
- Source/header split (h+cpp)  
- Concurrency  
