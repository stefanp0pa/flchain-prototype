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

    pub fn match_role(number: u8) -> Option<Role> {
        match number {
            0 => Some(Role::Proposer),
            1 => Some(Role::Trainer),
            2 => Some(Role::Aggregator),
            _ => None
        }
    }
}