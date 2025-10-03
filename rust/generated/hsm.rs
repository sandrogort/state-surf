#[allow(dead_code)]
#[allow(non_camel_case_types)]
#[allow(clippy::upper_case_acronyms)]
#[allow(unreachable_code)]
#[allow(unreachable_patterns)]
pub mod statesurf {
    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum State {
        InitialPseudoState,
        s,
        s1,
        s11,
        s2,
        s21,
        s211,
        FinalPseudoState,
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum Event {
        A,
        B,
        C,
        D,
        E,
        F,
        G,
        H,
        I,
        TERMINATE
    }

    impl Default for Event {
        fn default() -> Self {
            Event::A
        }
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum GuardId {
        isFooTrue,
        isFooFalse
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum ActionId {
        setFooFalse,
        setFooTrue
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
            on_transition(State::InitialPseudoState, State::s211, Event::default());
            self.state = State::s211;
            self.hooks.action(State::s, Event::default(), ActionId::setFooFalse);
            self.hooks.on_entry(State::s);
            self.hooks.on_entry(State::s2);
            self.hooks.on_entry(State::s21);
            self.hooks.on_entry(State::s211);
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
                State::s => {
                    match event {
                        Event::I => {
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::s1 => {
                    match event {
                        Event::I => {
            {
              on_transition(self.state, self.state, event);
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::D => {
            if self.hooks.guard(self.state, event, GuardId::isFooFalse) {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s1);
              self.hooks.action(self.state, event, ActionId::setFooTrue);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::A => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::B => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::C => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s2);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::F => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s2);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::s11 => {
                    match event {
                        Event::G => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s2);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::H => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::D => {
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooFalse) {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.action(self.state, event, ActionId::setFooTrue);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::I => {
            {
              on_transition(self.state, self.state, event);
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::A => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::B => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::C => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s2);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::F => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s2);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s11);
              self.hooks.on_exit(State::s1);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::s2 => {
                    match event {
                        Event::I => {
            if self.hooks.guard(self.state, event, GuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::C => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::F => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s2);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::s21 => {
                    match event {
                        Event::G => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::A => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::B => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::I => {
            if self.hooks.guard(self.state, event, GuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::C => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::F => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                State::s211 => {
                    match event {
                        Event::D => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::H => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::G => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::A => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_entry(State::s21);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::B => {
            {
              on_transition(self.state, State::s211, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_entry(State::s211);
              self.state = State::s211;
              return;
            }
                        }
                        Event::I => {
            if self.hooks.guard(self.state, event, GuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, GuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, ActionId::setFooFalse);
              return;
            }
                        }
                        Event::C => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::F => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
                        }
                        Event::TERMINATE => {
            {
              on_transition(self.state, State::FinalPseudoState, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_exit(State::s);
              self.hooks.on_entry(State::FinalPseudoState);
              self.state = State::FinalPseudoState;
              self.terminated = true;
              return;
            }
                        }
                        Event::E => {
            {
              on_transition(self.state, State::s11, event);
              self.hooks.on_exit(State::s211);
              self.hooks.on_exit(State::s21);
              self.hooks.on_exit(State::s2);
              self.hooks.on_entry(State::s1);
              self.hooks.on_entry(State::s11);
              self.state = State::s11;
              return;
            }
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