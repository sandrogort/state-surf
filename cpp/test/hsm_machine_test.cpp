#include <vector>

#include <gtest/gtest.h>

#include "hsm.hpp"

namespace {

struct RecordingHooks final : HsmHooks {
  std::vector<HsmState> entries;
  std::vector<HsmState> exits;
  std::vector<HsmActionId> actions;
  std::vector<HsmGuardId> guard_calls;
  bool foo = true;

  void on_entry(HsmState s) override { entries.push_back(s); }
  void on_exit(HsmState s) override { exits.push_back(s); }

  bool guard(HsmState, HsmEvent, HsmGuardId id) override {
    guard_calls.push_back(id);
    switch (id) {
      case HsmGuardId::isFooTrue:
        return foo;
      case HsmGuardId::isFooFalse:
        return !foo;
      default:
        return false;
    }
  }

  void action(HsmState, HsmEvent, HsmActionId id) override {
    actions.push_back(id);
    switch (id) {
      case HsmActionId::setFooFalse:
        foo = false;
        break;
      case HsmActionId::setFooTrue:
        foo = true;
        break;
      default:
        break;
    }
  }

  void reset_logs() {
    entries.clear();
    exits.clear();
    actions.clear();
    guard_calls.clear();
  }
};

}  // namespace

TEST(StateSurfMachine, DrivesThroughLifecycle) {
  RecordingHooks hooks;
  HsmMachine machine(hooks);

  EXPECT_EQ(machine.state(), HsmState::InitialPseudoState);
  EXPECT_FALSE(machine.terminated());
  EXPECT_TRUE(hooks.entries.empty());
  EXPECT_TRUE(hooks.actions.empty());

  machine.start();

  const std::vector<HsmState> expected_initial_entries{
      HsmState::s,
      HsmState::s2,
      HsmState::s21,
      HsmState::s211};
  EXPECT_EQ(hooks.entries, expected_initial_entries);
  EXPECT_TRUE(hooks.exits.empty());
  const std::vector<HsmActionId> expected_initial_actions{
      HsmActionId::setFooFalse};
  EXPECT_EQ(hooks.actions, expected_initial_actions);
  EXPECT_FALSE(hooks.foo);
  EXPECT_FALSE(machine.terminated());
  EXPECT_EQ(machine.state(), HsmState::s211);

  hooks.reset_logs();

  auto dispatch_and_expect = [&](HsmEvent event,
                                 std::vector<HsmState> expected_exits,
                                 std::vector<HsmState> expected_entries,
                                 std::vector<HsmActionId> expected_actions,
                                 std::vector<HsmGuardId> expected_guards,
                                 HsmState expected_state) {
    machine.dispatch(event);
    EXPECT_EQ(hooks.exits, expected_exits);
    EXPECT_EQ(hooks.entries, expected_entries);
    EXPECT_EQ(hooks.actions, expected_actions);
    EXPECT_EQ(hooks.guard_calls, expected_guards);
    EXPECT_EQ(machine.state(), expected_state);
    EXPECT_FALSE(machine.terminated());
    hooks.reset_logs();
  };

  dispatch_and_expect(
      HsmEvent::G,
      {HsmState::s211, HsmState::s21, HsmState::s2},
      {HsmState::s1, HsmState::s11},
      {},
      {},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::I,
      {},
      {},
      {},
      {},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::A,
      {HsmState::s11, HsmState::s1},
      {HsmState::s1, HsmState::s11},
      {},
      {},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::D,
      {HsmState::s11, HsmState::s1},
      {HsmState::s1, HsmState::s11},
      {HsmActionId::setFooTrue},
      {HsmGuardId::isFooTrue, HsmGuardId::isFooFalse},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::D,
      {HsmState::s11},
      {HsmState::s11},
      {HsmActionId::setFooFalse},
      {HsmGuardId::isFooTrue},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::C,
      {HsmState::s11, HsmState::s1},
      {HsmState::s2, HsmState::s21, HsmState::s211},
      {},
      {},
      HsmState::s211);

  dispatch_and_expect(
      HsmEvent::E,
      {HsmState::s211, HsmState::s21, HsmState::s2},
      {HsmState::s1, HsmState::s11},
      {},
      {},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::E,
      {HsmState::s11, HsmState::s1},
      {HsmState::s1, HsmState::s11},
      {},
      {},
      HsmState::s11);

  dispatch_and_expect(
      HsmEvent::G,
      {HsmState::s11, HsmState::s1},
      {HsmState::s2, HsmState::s21, HsmState::s211},
      {},
      {},
      HsmState::s211);

  dispatch_and_expect(
      HsmEvent::I,
      {},
      {},
      {HsmActionId::setFooTrue},
      {HsmGuardId::isFooFalse},
      HsmState::s211);

  dispatch_and_expect(
      HsmEvent::I,
      {},
      {},
      {HsmActionId::setFooFalse},
      {HsmGuardId::isFooFalse, HsmGuardId::isFooTrue},
      HsmState::s211);

  machine.dispatch(HsmEvent::TERMINATE);
  EXPECT_TRUE(machine.terminated());
  EXPECT_EQ(machine.state(), HsmState::FinalPseudoState);
}
