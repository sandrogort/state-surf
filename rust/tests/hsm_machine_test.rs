use state_surf::generated::hsm::statesurf::{
    ActionId, Event, GuardId, Hooks, State, StateSurfMachine,
};

struct RecordingHooks {
    entries: Vec<State>,
    exits: Vec<State>,
    actions: Vec<ActionId>,
    guard_calls: Vec<GuardId>,
    foo: bool,
}

impl Default for RecordingHooks {
    fn default() -> Self {
        Self::new()
    }
}

impl RecordingHooks {
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

impl Hooks for RecordingHooks {
    fn on_entry(&mut self, state: State) {
        self.entries.push(state);
    }

    fn on_exit(&mut self, state: State) {
        self.exits.push(state);
    }

    fn guard(&mut self, _state: State, _event: Event, guard: GuardId) -> bool {
        self.guard_calls.push(guard);
        match guard {
            GuardId::isFooTrue => self.foo,
            GuardId::isFooFalse => !self.foo,
        }
    }

    fn action(&mut self, _state: State, _event: Event, action: ActionId) {
        self.actions.push(action);
        match action {
            ActionId::setFooFalse => self.foo = false,
            ActionId::setFooTrue => self.foo = true,
        }
    }
}

fn dispatch_and_expect(
    machine: &mut StateSurfMachine<RecordingHooks>,
    event: Event,
    expected_exits: &[State],
    expected_entries: &[State],
    expected_actions: &[ActionId],
    expected_guards: &[GuardId],
    expected_state: State,
) {
    machine.dispatch(event);
    {
        let hooks = machine.hooks();
        assert_eq!(hooks.exits.as_slice(), expected_exits);
        assert_eq!(hooks.entries.as_slice(), expected_entries);
        assert_eq!(hooks.actions.as_slice(), expected_actions);
        assert_eq!(hooks.guard_calls.as_slice(), expected_guards);
    }
    assert_eq!(machine.state(), expected_state);
    assert!(!machine.terminated());
    machine.hooks_mut().reset_logs();
}

#[test]
fn drives_through_lifecycle() {
    let hooks = RecordingHooks::new();
    let mut machine = StateSurfMachine::new(hooks);

    {
        let hooks_view = machine.hooks();
        assert_eq!(machine.state(), State::InitialPseudoState);
        assert!(!machine.terminated());
        assert!(hooks_view.entries.is_empty());
        assert!(hooks_view.actions.is_empty());
        assert!(hooks_view.guard_calls.is_empty());
    }

    machine.start();
    {
        let hooks_view = machine.hooks();
        let expected_initial_entries = vec![State::s, State::s2, State::s21, State::s211];
        assert_eq!(hooks_view.entries, expected_initial_entries);
        assert!(hooks_view.exits.is_empty());
        let expected_initial_actions = vec![ActionId::setFooFalse];
        assert_eq!(hooks_view.actions, expected_initial_actions);
        assert!(hooks_view.guard_calls.is_empty());
        assert!(!hooks_view.foo);
    }
    assert!(!machine.terminated());
    assert_eq!(machine.state(), State::s211);
    machine.hooks_mut().reset_logs();

    dispatch_and_expect(
        &mut machine,
        Event::G,
        &[State::s211, State::s21, State::s2],
        &[State::s1, State::s11],
        &[],
        &[],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::I,
        &[],
        &[],
        &[],
        &[],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::A,
        &[State::s11, State::s1],
        &[State::s1, State::s11],
        &[],
        &[],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::D,
        &[State::s11, State::s1],
        &[State::s1, State::s11],
        &[ActionId::setFooTrue],
        &[GuardId::isFooTrue, GuardId::isFooFalse],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::D,
        &[State::s11],
        &[State::s11],
        &[ActionId::setFooFalse],
        &[GuardId::isFooTrue],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::C,
        &[State::s11, State::s1],
        &[State::s2, State::s21, State::s211],
        &[],
        &[],
        State::s211,
    );

    dispatch_and_expect(
        &mut machine,
        Event::E,
        &[State::s211, State::s21, State::s2],
        &[State::s1, State::s11],
        &[],
        &[],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::E,
        &[State::s11, State::s1],
        &[State::s1, State::s11],
        &[],
        &[],
        State::s11,
    );

    dispatch_and_expect(
        &mut machine,
        Event::G,
        &[State::s11, State::s1],
        &[State::s2, State::s21, State::s211],
        &[],
        &[],
        State::s211,
    );

    dispatch_and_expect(
        &mut machine,
        Event::I,
        &[],
        &[],
        &[ActionId::setFooTrue],
        &[GuardId::isFooFalse],
        State::s211,
    );

    dispatch_and_expect(
        &mut machine,
        Event::I,
        &[],
        &[],
        &[ActionId::setFooFalse],
        &[GuardId::isFooFalse, GuardId::isFooTrue],
        State::s211,
    );

    machine.dispatch(Event::TERMINATE);
    assert!(machine.terminated());
    assert_eq!(machine.state(), State::FinalPseudoState);
    {
        let hooks_view = machine.hooks();
        assert_eq!(hooks_view.exits, vec![State::s211, State::s21, State::s2, State::s]);
        assert_eq!(hooks_view.entries, vec![State::FinalPseudoState]);
    }
}
