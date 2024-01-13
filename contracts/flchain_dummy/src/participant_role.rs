multiversx_sc::derive_imports!();

#[derive(TopEncode, TopDecode, NestedDecode, NestedEncode, TypeAbi, Clone, Copy, PartialEq, Eq, Debug)]
pub enum Role {
    Proposer,
    Trainer,
    Aggregator
}

impl Role {
    pub fn can_propose(&self) -> bool {
        matches!(*self, Role::Proposer)
    }
    
    pub fn can_train(&self) -> bool {
        matches!(*self, Role::Trainer)
    }

    pub fn can_upgate_global(&self) -> bool {
        matches!(*self, Role::Aggregator)
    }

    pub fn can_end_session(&self) -> bool {
        matches!(*self, Role::Proposer)
    }
}