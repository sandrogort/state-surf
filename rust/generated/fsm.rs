#[allow(dead_code)]
#[allow(non_camel_case_types)]
#[allow(clippy::upper_case_acronyms)]
#[allow(unreachable_code)]
#[allow(unreachable_patterns)]
pub mod statesurf {
    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum State {
        InitialPseudoState,
        State1,
        State2,
        State3,
        State4,
        State5,
        FinalPseudoState,
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum Event {
        eventA,
        eventB,
        eventC,
        eventD,
        eventFoo,
        init
    }

    impl Default for Event {
        fn default() -> Self {
            Event::eventA
        }
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum GuardId {
        guardA,
        guardB
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum ActionId {
        actionA,
        actionB
    }

    pub trait Hooks {
        fn on_entry(&mut self, state: State);
        fn on_exit(&mut self, state: State);
        fn guard(&mut self, state: State, event: Event, guard: GuardId) -> bool;
        fn action(&mut self, state: State, event: Event, action: ActionId);
    }

    #[inline]
    pub fn on_event(_state: State, _event: Event) {}

    #[inline]
    pub fn on_transition(_from: State, _to: State, _event: Event) {}

    pub struct StateSurfMachine<H: Hooks> {
        hooks: H,
        state: State,
        started: bool,
        terminated: bool,
    }

    impl<H: Hooks> StateSurfMachine<H> {
        pub fn new(hooks: H) -> Self {
            let mut machine = Self {
                hooks,
                state: State::InitialPseudoState,
                started: false,
                terminated: false,
            };
            machine.reset();
            machine
        }

        pub fn reset(&mut self) {
            self.terminated = false;
            self.started = false;
            self.state = State::InitialPseudoState;
        }

        pub fn start(&mut self) {
            if self.terminated || self.started {
                return;
            }
            self.started = true;
            on_transition(State::InitialPseudoState, State::State1, Event::default());
            self.state = State::State1;
            self.hooks.on_entry(State::State1);
        }

        pub fn state(&self) -> State {
            self.state
        }

        pub fn terminated(&self) -> bool {
            self.terminated
        }

        pub fn hooks(&self) -> &H {
            &self.hooks
        }

        pub fn hooks_mut(&mut self) -> &mut H {
            &mut self.hooks
        }

        pub fn dispatch(&mut self, event: Event) {
            if self.terminated {
                return;
            }
            if !self.started {
                self.start();
                if !self.started {
                    return;
                }
            }
            on_event(self.state, event);
            match self.state {
                State::State1 => {
                    match event {
                        Event::eventA => {
            on_transition(self.state, State::State2, event);
            self.hooks.on_exit(State::State1);
            self.hooks.on_entry(State::State2);
            self.state = State::State2;
            return;
                        }
                        Event::init => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        Event::eventFoo => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::State2 => {
                    match event {
                        Event::eventB => {
            if self.hooks.guard(self.state, event, GuardId::guardA) {
              on_transition(self.state, State::State3, event);
              self.hooks.on_exit(State::State2);
              self.hooks.on_entry(State::State3);
              self.state = State::State3;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::State3 => {
                    match event {
                        Event::eventC => {
            on_transition(self.state, State::State4, event);
            self.hooks.on_exit(State::State3);
            self.hooks.action(self.state, event, ActionId::actionA);
            self.hooks.on_entry(State::State4);
            self.state = State::State4;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::State4 => {
                    match event {
                        Event::eventD => {
            if self.hooks.guard(self.state, event, GuardId::guardB) {
              on_transition(self.state, State::State5, event);
              self.hooks.on_exit(State::State4);
              self.hooks.action(self.state, event, ActionId::actionB);
              self.hooks.on_entry(State::State5);
              self.state = State::State5;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::State5 => {
                    match event {
                        Event::init => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::InitialPseudoState => {
                    return;
                }
                State::FinalPseudoState => {
                    return;
                }
                _ => {}
            }
        }
    }
}