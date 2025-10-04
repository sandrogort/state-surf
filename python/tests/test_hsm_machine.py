import unittest

from python.generated.hsm import (
    HsmActionId,
    HsmEvent,
    HsmGuardId,
    HsmHooks,
    HsmMachine,
    HsmState,
)


class RecordingHooks(HsmHooks):
    def __init__(self) -> None:
        self.entries = []
        self.exits = []
        self.actions = []
        self.guard_calls = []
        self.foo = True

    def on_entry(self, state: HsmState) -> None:
        self.entries.append(state)

    def on_exit(self, state: HsmState) -> None:
        self.exits.append(state)

    def guard(self, state: HsmState, event: HsmEvent, guard: HsmGuardId) -> bool:
        self.guard_calls.append(guard)
        if guard == HsmGuardId.isFooTrue:
            return self.foo
        if guard == HsmGuardId.isFooFalse:
            return not self.foo
        return False

    def action(self, state: HsmState, event: HsmEvent, action: HsmActionId) -> None:
        self.actions.append(action)
        if action == HsmActionId.setFooFalse:
            self.foo = False
        elif action == HsmActionId.setFooTrue:
            self.foo = True

    def reset_logs(self) -> None:
        self.entries.clear()
        self.exits.clear()
        self.actions.clear()
        self.guard_calls.clear()


class HsmMachineTest(unittest.TestCase):
    def test_drives_through_lifecycle(self) -> None:
        hooks = RecordingHooks()
        machine = HsmMachine(hooks)

        self.assertEqual(machine.state(), HsmState.InitialPseudoState)
        self.assertFalse(machine.terminated())
        self.assertEqual(hooks.entries, [])
        self.assertEqual(hooks.actions, [])
        self.assertEqual(hooks.guard_calls, [])

        machine.start()

        expected_initial_entries = [
            HsmState.s,
            HsmState.s2,
            HsmState.s21,
            HsmState.s211,
        ]
        self.assertEqual(hooks.entries, expected_initial_entries)
        self.assertEqual(hooks.exits, [])
        self.assertEqual(hooks.actions, [HsmActionId.setFooFalse])
        self.assertEqual(hooks.guard_calls, [])
        self.assertFalse(hooks.foo)
        self.assertFalse(machine.terminated())
        self.assertEqual(machine.state(), HsmState.s211)

        hooks.reset_logs()

        def dispatch_and_expect(
            event: HsmEvent,
            expected_exits,
            expected_entries,
            expected_actions,
            expected_guards,
            expected_state: HsmState,
        ) -> None:
            machine.dispatch(event)
            self.assertEqual(hooks.exits, expected_exits)
            self.assertEqual(hooks.entries, expected_entries)
            self.assertEqual(hooks.actions, expected_actions)
            self.assertEqual(hooks.guard_calls, expected_guards)
            self.assertEqual(machine.state(), expected_state)
            self.assertFalse(machine.terminated())
            hooks.reset_logs()

        dispatch_and_expect(
            HsmEvent.G,
            [HsmState.s211, HsmState.s21, HsmState.s2],
            [HsmState.s1, HsmState.s11],
            [],
            [],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.I,
            [],
            [],
            [],
            [],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.A,
            [HsmState.s11, HsmState.s1],
            [HsmState.s1, HsmState.s11],
            [],
            [],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.D,
            [HsmState.s11, HsmState.s1],
            [HsmState.s1, HsmState.s11],
            [HsmActionId.setFooTrue],
            [HsmGuardId.isFooTrue, HsmGuardId.isFooFalse],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.D,
            [HsmState.s11],
            [HsmState.s11],
            [HsmActionId.setFooFalse],
            [HsmGuardId.isFooTrue],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.C,
            [HsmState.s11, HsmState.s1],
            [HsmState.s2, HsmState.s21, HsmState.s211],
            [],
            [],
            HsmState.s211,
        )

        dispatch_and_expect(
            HsmEvent.E,
            [HsmState.s211, HsmState.s21, HsmState.s2],
            [HsmState.s1, HsmState.s11],
            [],
            [],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.E,
            [HsmState.s11, HsmState.s1],
            [HsmState.s1, HsmState.s11],
            [],
            [],
            HsmState.s11,
        )

        dispatch_and_expect(
            HsmEvent.G,
            [HsmState.s11, HsmState.s1],
            [HsmState.s2, HsmState.s21, HsmState.s211],
            [],
            [],
            HsmState.s211,
        )

        dispatch_and_expect(
            HsmEvent.I,
            [],
            [],
            [HsmActionId.setFooTrue],
            [HsmGuardId.isFooFalse],
            HsmState.s211,
        )

        dispatch_and_expect(
            HsmEvent.I,
            [],
            [],
            [HsmActionId.setFooFalse],
            [HsmGuardId.isFooFalse, HsmGuardId.isFooTrue],
            HsmState.s211,
        )

        machine.dispatch(HsmEvent.TERMINATE)
        self.assertTrue(machine.terminated())
        self.assertEqual(machine.state(), HsmState.FinalPseudoState)


if __name__ == "__main__":
    unittest.main()
