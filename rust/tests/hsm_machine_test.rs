use state_surf::generated::hsm::hsm::{
    HsmActionId, HsmCallbacks, HsmEvent, HsmGuardId, HsmMachine, HsmState,
};

struct RecordingCallbacks {
    entries: Vec<HsmState>,
    exits: Vec<HsmState>,
    actions: Vec<HsmActionId>,
    guard_calls: Vec<HsmGuardId>,
    foo: bool,
}

impl Default for RecordingCallbacks {
    fn default() -> Self {
        Self::new()
    }
}

impl RecordingCallbacks {
    fn new() -> Self {
        Self {
            entries: Vec::new(),
            exits: Vec::new(),
            actions: Vec::new(),
            guard_calls: Vec::new(),
            foo: true,
        }
    }

    fn reset_logs(&mut self) {
        self.entries.clear();
        self.exits.clear();
        self.actions.clear();
        self.guard_calls.clear();
    }
}

impl HsmCallbacks for RecordingCallbacks {
    fn on_entry(&mut self, state: HsmState) {
        self.entries.push(state);
    }

    fn on_exit(&mut self, state: HsmState) {
        self.exits.push(state);
    }

    fn guard(&mut self, _state: HsmState, _event: HsmEvent, guard: HsmGuardId) -> bool {
        self.guard_calls.push(guard);
        match guard {
            HsmGuardId::isFooTrue => self.foo,
            HsmGuardId::isFooFalse => !self.foo,
        }
    }

    fn action(&mut self, _state: HsmState, _event: HsmEvent, action: HsmActionId) {
        self.actions.push(action);
        match action {
            HsmActionId::setFooFalse => self.foo = false,
            HsmActionId::setFooTrue => self.foo = true,
        }
    }
}

fn dispatch_and_expect(
    machine: &mut HsmMachine<RecordingCallbacks>,
    event: HsmEvent,
    expected_exits: &[HsmState],
    expected_entries: &[HsmState],
    expected_actions: &[HsmActionId],
    expected_guards: &[HsmGuardId],
    expected_state: HsmState,
) {
    machine.dispatch(event);
    {
        let callbacks = machine.callbacks();
        assert_eq!(callbacks.exits.as_slice(), expected_exits);
        assert_eq!(callbacks.entries.as_slice(), expected_entries);
        assert_eq!(callbacks.actions.as_slice(), expected_actions);
        assert_eq!(callbacks.guard_calls.as_slice(), expected_guards);
    }
    assert_eq!(machine.state(), expected_state);
    assert!(!machine.terminated());
    machine.callbacks_mut().reset_logs();
}

#[test]
fn drives_through_lifecycle() {
    let callbacks = RecordingCallbacks::new();
    let mut machine = HsmMachine::new(callbacks);

    {
        let callbacks_view = machine.callbacks();
        assert_eq!(machine.state(), HsmState::InitialPseudoState);
        assert!(!machine.terminated());
        assert!(callbacks_view.entries.is_empty());
        assert!(callbacks_view.actions.is_empty());
        assert!(callbacks_view.guard_calls.is_empty());
    }

    machine.start();
    {
        let callbacks_view = machine.callbacks();
        let expected_initial_entries = vec![HsmState::s, HsmState::s2, HsmState::s21, HsmState::s211];
        assert_eq!(callbacks_view.entries, expected_initial_entries);
        assert!(callbacks_view.exits.is_empty());
        let expected_initial_actions = vec![HsmActionId::setFooFalse];
        assert_eq!(callbacks_view.actions, expected_initial_actions);
        assert!(callbacks_view.guard_calls.is_empty());
        assert!(!callbacks_view.foo);
    }
    assert!(!machine.terminated());
    assert_eq!(machine.state(), HsmState::s211);
    machine.callbacks_mut().reset_logs();

    dispatch_and_expect(
        &mut machine,
        HsmEvent::G,
        &[HsmState::s211, HsmState::s21, HsmState::s2],
        &[HsmState::s1, HsmState::s11],
        &[],
        &[],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::I,
        &[],
        &[],
        &[],
        &[],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::A,
        &[HsmState::s11, HsmState::s1],
        &[HsmState::s1, HsmState::s11],
        &[],
        &[],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::D,
        &[HsmState::s11, HsmState::s1],
        &[HsmState::s1, HsmState::s11],
        &[HsmActionId::setFooTrue],
        &[HsmGuardId::isFooTrue, HsmGuardId::isFooFalse],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::D,
        &[HsmState::s11],
        &[HsmState::s11],
        &[HsmActionId::setFooFalse],
        &[HsmGuardId::isFooTrue],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::C,
        &[HsmState::s11, HsmState::s1],
        &[HsmState::s2, HsmState::s21, HsmState::s211],
        &[],
        &[],
        HsmState::s211,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::E,
        &[HsmState::s211, HsmState::s21, HsmState::s2],
        &[HsmState::s1, HsmState::s11],
        &[],
        &[],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::E,
        &[HsmState::s11, HsmState::s1],
        &[HsmState::s1, HsmState::s11],
        &[],
        &[],
        HsmState::s11,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::G,
        &[HsmState::s11, HsmState::s1],
        &[HsmState::s2, HsmState::s21, HsmState::s211],
        &[],
        &[],
        HsmState::s211,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::I,
        &[],
        &[],
        &[HsmActionId::setFooTrue],
        &[HsmGuardId::isFooFalse],
        HsmState::s211,
    );

    dispatch_and_expect(
        &mut machine,
        HsmEvent::I,
        &[],
        &[],
        &[HsmActionId::setFooFalse],
        &[HsmGuardId::isFooFalse, HsmGuardId::isFooTrue],
        HsmState::s211,
    );

    machine.dispatch(HsmEvent::TERMINATE);
    assert!(machine.terminated());
    assert_eq!(machine.state(), HsmState::FinalPseudoState);
    {
        let callbacks_view = machine.callbacks();
        assert_eq!(callbacks_view.exits, vec![HsmState::s211, HsmState::s21, HsmState::s2, HsmState::s]);
        assert_eq!(callbacks_view.entries, vec![HsmState::FinalPseudoState]);
    }
}
