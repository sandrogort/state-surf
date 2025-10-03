pub mod generated {
    pub mod hsm {
        include!(concat!(env!("CARGO_MANIFEST_DIR"), "/generated/hsm.rs"));
    }

    pub mod fsm {
        include!(concat!(env!("CARGO_MANIFEST_DIR"), "/generated/fsm.rs"));
    }
}
