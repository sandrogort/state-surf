#include <vector>

#include <gtest/gtest.h>

#include "hsm.hpp"

namespace {

struct RecordingHooks final : statesurf::IHooks {
  std::vector<statesurf::State> entries;
  std::vector<statesurf::State> exits;
  std::vector<statesurf::ActionId> actions;
  std::vector<statesurf::GuardId> guard_calls;
  bool foo = true;

  void on_entry(statesurf::State s) override { entries.push_back(s); }
  void on_exit(statesurf::State s) override { exits.push_back(s); }

  bool guard(statesurf::State, statesurf::Event, statesurf::GuardId id) override {
    guard_calls.push_back(id);
    switch (id) {
      case statesurf::GuardId::s_I_isFooTrue:
      case statesurf::GuardId::s11_D_isFooTrue:
        return foo;
      case statesurf::GuardId::s1_D_isFooFalse:
      case statesurf::GuardId::s2_I_isFooFalse:
        return !foo;
      default:
        return false;
    }
  }

  void action(statesurf::State, statesurf::Event, statesurf::ActionId id) override {
    actions.push_back(id);
    switch (id) {
      case statesurf::ActionId::s_I_setFooFalse:
      case statesurf::ActionId::s11_D_setFooFalse:
      case statesurf::ActionId::__root___Initial_setFooFalse:
        foo = false;
        break;
      case statesurf::ActionId::s1_D_setFooTrue:
      case statesurf::ActionId::s2_I_setFooTrue:
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
  statesurf::StateSurfMachine machine(hooks);

  const std::vector<statesurf::State> expected_initial_entries{
      statesurf::State::s,
      statesurf::State::s2,
      statesurf::State::s21,
      statesurf::State::s211};
  EXPECT_EQ(hooks.entries, expected_initial_entries);
  EXPECT_TRUE(hooks.exits.empty());
  const std::vector<statesurf::ActionId> expected_initial_actions{
      statesurf::ActionId::__root___Initial_setFooFalse};
  EXPECT_EQ(hooks.actions, expected_initial_actions);
  EXPECT_FALSE(hooks.foo);
  EXPECT_FALSE(machine.terminated());
  EXPECT_EQ(machine.state(), statesurf::State::s211);

  hooks.reset_logs();

  auto dispatch_and_expect = [&](statesurf::Event event,
                                 std::vector<statesurf::State> expected_exits,
                                 std::vector<statesurf::State> expected_entries,
                                 std::vector<statesurf::ActionId> expected_actions,
                                 std::vector<statesurf::GuardId> expected_guards,
                                 statesurf::State expected_state) {
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
      statesurf::Event::G,
      {statesurf::State::s211, statesurf::State::s21, statesurf::State::s2},
      {statesurf::State::s1, statesurf::State::s11},
      {},
      {},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::I,
      {},
      {},
      {},
      {},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::A,
      {statesurf::State::s11},
      {statesurf::State::s1, statesurf::State::s11},
      {},
      {},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::D,
      {statesurf::State::s11},
      {statesurf::State::s11},
      {statesurf::ActionId::s1_D_setFooTrue},
      {statesurf::GuardId::s11_D_isFooTrue, statesurf::GuardId::s1_D_isFooFalse},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::D,
      {},
      {},
      {statesurf::ActionId::s11_D_setFooFalse},
      {statesurf::GuardId::s11_D_isFooTrue},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::C,
      {statesurf::State::s11, statesurf::State::s1},
      {statesurf::State::s2, statesurf::State::s21, statesurf::State::s211},
      {},
      {},
      statesurf::State::s211);

  dispatch_and_expect(
      statesurf::Event::E,
      {statesurf::State::s211, statesurf::State::s21, statesurf::State::s2},
      {statesurf::State::s1, statesurf::State::s11},
      {},
      {},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::E,
      {statesurf::State::s11, statesurf::State::s1},
      {statesurf::State::s1, statesurf::State::s11},
      {},
      {},
      statesurf::State::s11);

  dispatch_and_expect(
      statesurf::Event::G,
      {statesurf::State::s11, statesurf::State::s1},
      {statesurf::State::s2, statesurf::State::s21, statesurf::State::s211},
      {},
      {},
      statesurf::State::s211);

  dispatch_and_expect(
      statesurf::Event::I,
      {},
      {},
      {statesurf::ActionId::s2_I_setFooTrue},
      {statesurf::GuardId::s2_I_isFooFalse},
      statesurf::State::s211);

  dispatch_and_expect(
      statesurf::Event::I,
      {},
      {},
      {statesurf::ActionId::s_I_setFooFalse},
      {statesurf::GuardId::s2_I_isFooFalse, statesurf::GuardId::s_I_isFooTrue},
      statesurf::State::s211);

      machine.dispatch(statesurf::Event::TERMINATE);
      EXPECT_TRUE(machine.terminated());
}
