#[allow(dead_code)]
#[allow(non_camel_case_types)]
#[allow(clippy::upper_case_acronyms)]
#[allow(unreachable_code)]
#[allow(unreachable_patterns)]
pub mod fsm {
    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum FsmState {
        InitialPseudoState,
        State1,
        State2,
        State3,
        State4,
        State5,
        FinalPseudoState,
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum FsmEvent {
        eventA,
        eventB,
        eventC,
        eventD,
        eventFoo,
        init
    }

    impl Default for FsmEvent {
        fn default() -> Self {
            FsmEvent::eventA
        }
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum FsmGuardId {
        guardA,
        guardB
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    pub enum FsmActionId {
        actionA,
        actionB
    }

    pub trait FsmHooks {
        fn on_entry(&mut self, state: FsmState);
        fn on_exit(&mut self, state: FsmState);
        fn guard(&mut self, state: FsmState, event: FsmEvent, guard: FsmGuardId) -> bool;
        fn action(&mut self, state: FsmState, event: FsmEvent, action: FsmActionId);
    }

    #[inline]
    pub fn on_event(_state: FsmState, _event: FsmEvent) {}

    #[inline]
    pub fn on_transition(_from: FsmState, _to: FsmState, _event: FsmEvent) {}

    pub struct FsmMachine<H: FsmHooks> {
        hooks: H,
        state: FsmState,
        started: bool,
        terminated: bool,
    }

    impl<H: FsmHooks> FsmMachine<H> {
        pub fn new(hooks: H) -> Self {
            let mut machine = Self {
                hooks,
                state: FsmState::InitialPseudoState,
                started: false,
                terminated: false,
            };
            machine.reset();
            machine
        }

        pub fn reset(&mut self) {
            self.terminated = false;
            self.started = false;
            self.state = FsmState::InitialPseudoState;
        }

        pub fn start(&mut self) {
            if self.terminated || self.started {
                return;
            }
            self.started = true;
            on_transition(FsmState::InitialPseudoState, FsmState::State1, FsmEvent::default());
            self.state = FsmState::State1;
            self.hooks.on_entry(FsmState::State1);
        }

        pub fn state(&self) -> FsmState {
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

        pub fn dispatch(&mut self, event: FsmEvent) {
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
                FsmState::State1 => {
                    match event {
                        FsmEvent::eventA => {
            on_transition(self.state, FsmState::State2, event);
            self.hooks.on_exit(FsmState::State1);
            self.hooks.on_entry(FsmState::State2);
            self.state = FsmState::State2;
            return;
                        }
                        FsmEvent::init => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        FsmEvent::eventFoo => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                FsmState::State2 => {
                    match event {
                        FsmEvent::eventB => {
            if self.hooks.guard(self.state, event, FsmGuardId::guardA) {
              on_transition(self.state, FsmState::State3, event);
              self.hooks.on_exit(FsmState::State2);
              self.hooks.on_entry(FsmState::State3);
              self.state = FsmState::State3;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                FsmState::State3 => {
                    match event {
                        FsmEvent::eventC => {
            on_transition(self.state, FsmState::State4, event);
            self.hooks.on_exit(FsmState::State3);
            self.hooks.action(self.state, event, FsmActionId::actionA);
            self.hooks.on_entry(FsmState::State4);
            self.state = FsmState::State4;
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                FsmState::State4 => {
                    match event {
                        FsmEvent::eventD => {
            if self.hooks.guard(self.state, event, FsmGuardId::guardB) {
              on_transition(self.state, FsmState::State5, event);
              self.hooks.on_exit(FsmState::State4);
              self.hooks.action(self.state, event, FsmActionId::actionB);
              self.hooks.on_entry(FsmState::State5);
              self.state = FsmState::State5;
              return;
            }
                        }
                        _ => {
                            return;
                        }
                    }
                }
                FsmState::State5 => {
                    match event {
                        FsmEvent::init => {
            on_transition(self.state, self.state, event);
            return;
                        }
                        _ => {
                            return;
                        }
                    }
                }
                FsmState::InitialPseudoState => {
                    return;
                }
                FsmState::FinalPseudoState => {
                    return;
                }
                _ => {}
            }
        }
    }
}