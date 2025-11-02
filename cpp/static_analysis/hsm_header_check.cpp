#include "hsm.hpp"

namespace statesurf {
namespace static_analysis {

namespace {

struct DummyCallbacks {
  static void on_entry(HsmState state) { (void)state; }
  static void on_exit(HsmState state) { (void)state; }
  static bool guard(HsmState state, HsmEvent event, HsmGuardId guard_id) {
    (void)state;
    (void)event;
    (void)guard_id;
    return true;
  }
  static void action(HsmState state, HsmEvent event, HsmActionId action_id) {
    (void)state;
    (void)event;
    (void)action_id;
  }
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
