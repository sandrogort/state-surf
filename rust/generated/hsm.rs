#[allow(dead_code)]
#[allow(non_camel_case_types)]
#[allow(clippy::upper_case_acronyms)]
#[allow(unreachable_code)]
#[allow(unreachable_patterns)]
pub mod hsm {
    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum HsmState {
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
    pub enum HsmEvent {
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

    impl Default for HsmEvent {
        fn default() -> Self {
            HsmEvent::A
        }
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum HsmGuardId {
        isFooTrue,
        isFooFalse
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum HsmActionId {
        setFooFalse,
        setFooTrue
    }

    pub trait HsmHooks {
        fn on_entry(&mut self, state: HsmState);
        fn on_exit(&mut self, state: HsmState);
        fn guard(&mut self, state: HsmState, event: HsmEvent, guard: HsmGuardId) -> bool;
        fn action(&mut self, state: HsmState, event: HsmEvent, action: HsmActionId);
    }

    #[inline]
    pub fn on_event(_state: HsmState, _event: HsmEvent) {}

    #[inline]
    pub fn on_transition(_from: HsmState, _to: HsmState, _event: HsmEvent) {}

    pub struct HsmMachine<H: HsmHooks> {
        hooks: H,
        state: HsmState,
        started: bool,
        terminated: bool,
    }

    impl<H: HsmHooks> HsmMachine<H> {
        pub fn new(hooks: H) -> Self {
            let mut machine = Self {
                hooks,
                state: HsmState::InitialPseudoState,
                started: false,
                terminated: false,
            };
            machine.reset();
            machine
        }

        pub fn reset(&mut self) {
            self.terminated = false;
            self.started = false;
            self.state = HsmState::InitialPseudoState;
        }

        pub fn start(&mut self) {
            if self.terminated || self.started {
                return;
            }
            self.started = true;
            on_transition(HsmState::InitialPseudoState, HsmState::s211, HsmEvent::default());
            self.state = HsmState::s211;
            self.hooks.action(HsmState::s, HsmEvent::default(), HsmActionId::setFooFalse);
            self.hooks.on_entry(HsmState::s);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
        }

        pub fn state(&self) -> HsmState {
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

        pub fn dispatch(&mut self, event: HsmEvent) {
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
                HsmState::s => {
                    match event {
                        HsmEvent::I => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooFalse);
              return;
            }
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::s1 => {
                    match event {
                        HsmEvent::I => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        HsmEvent::D => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooFalse) {
              on_transition(self.state, HsmState::s11, event);
              self.hooks.on_exit(HsmState::s1);
              self.hooks.action(self.state, event, HsmActionId::setFooTrue);
              self.hooks.on_entry(HsmState::s1);
              self.hooks.on_entry(HsmState::s11);
              self.state = HsmState::s11;
              return;
            }
                        }
                        HsmEvent::A => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::B => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::C => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::F => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::s11 => {
                    match event {
                        HsmEvent::G => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::H => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::D => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooTrue) {
              on_transition(self.state, HsmState::s11, event);
              self.hooks.on_exit(HsmState::s11);
              self.hooks.action(self.state, event, HsmActionId::setFooFalse);
              self.hooks.on_entry(HsmState::s11);
              self.state = HsmState::s11;
              return;
            }
            if self.hooks.guard(self.state, event, HsmGuardId::isFooFalse) {
              on_transition(self.state, HsmState::s11, event);
              self.hooks.on_exit(HsmState::s11);
              self.hooks.on_exit(HsmState::s1);
              self.hooks.action(self.state, event, HsmActionId::setFooTrue);
              self.hooks.on_entry(HsmState::s1);
              self.hooks.on_entry(HsmState::s11);
              self.state = HsmState::s11;
              return;
            }
                        }
                        HsmEvent::I => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        HsmEvent::A => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::B => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::C => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::F => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s2);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s11);
            self.hooks.on_exit(HsmState::s1);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::s2 => {
                    match event {
                        HsmEvent::I => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, HsmGuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooFalse);
              return;
            }
                        }
                        HsmEvent::C => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::F => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::s21 => {
                    match event {
                        HsmEvent::G => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::A => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::B => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::I => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, HsmGuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooFalse);
              return;
            }
                        }
                        HsmEvent::C => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::F => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::s211 => {
                    match event {
                        HsmEvent::D => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::H => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::G => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::A => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_entry(HsmState::s21);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::B => {
            on_transition(self.state, HsmState::s211, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_entry(HsmState::s211);
            self.state = HsmState::s211;
            return;
                        }
                        HsmEvent::I => {
            if self.hooks.guard(self.state, event, HsmGuardId::isFooFalse) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooTrue);
              return;
            }
            if self.hooks.guard(self.state, event, HsmGuardId::isFooTrue) {
              on_transition(self.state, self.state, event);
              self.hooks.action(self.state, event, HsmActionId::setFooFalse);
              return;
            }
                        }
                        HsmEvent::C => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::F => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        HsmEvent::TERMINATE => {
            on_transition(self.state, HsmState::FinalPseudoState, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_exit(HsmState::s);
            self.hooks.on_entry(HsmState::FinalPseudoState);
            self.state = HsmState::FinalPseudoState;
            self.terminated = true;
            return;
                        }
                        HsmEvent::E => {
            on_transition(self.state, HsmState::s11, event);
            self.hooks.on_exit(HsmState::s211);
            self.hooks.on_exit(HsmState::s21);
            self.hooks.on_exit(HsmState::s2);
            self.hooks.on_entry(HsmState::s1);
            self.hooks.on_entry(HsmState::s11);
            self.state = HsmState::s11;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                HsmState::InitialPseudoState => {
                    return;
                }
                HsmState::FinalPseudoState => {
                    return;
                }
                _ => {}
            }
        }
    }
}