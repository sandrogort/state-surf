#include "hsm.hpp"

namespace statesurf {
namespace static_analysis {

namespace {

struct DummyCallbacks {
  void on_entry(HsmState) {}
  void on_exit(HsmState) {}
  bool guard(HsmState, HsmEvent, HsmGuardId) { return true; }
  void action(HsmState, HsmEvent, HsmActionId) {}
};

}  // namespace

void touch() {
  DummyCallbacks callbacks{};
  HsmMachine<DummyCallbacks> machine(callbacks);
  machine.reset();
  machine.start();
  machine.dispatch(HsmEvent::A);
  (void)machine.state();
  (void)machine.terminated();
}

}  // namespace static_analysis
}  // namespace statesurf
