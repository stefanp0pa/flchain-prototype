#![no_std]

use chrono::prelude::*;

multiversx_sc::imports!();

/// An empty contract. To be used as a template when starting a new contract from scratch.
#[multiversx_sc::contract]
pub trait FlchainDummy {
    #[init]
    fn init(&self) {
    }

    #[upgrade]
    fn upgrade(&self) {
    }

    #[view]
    fn generate_random_dna(&self) -> ManagedBuffer{
        ManagedBuffer::from("Waka waka eee")
    }

    #[view]
    fn get_current_timestamp(&self) -> ManagedBuffer{
        let utc: DateTime<Utc> = Utc::now();
        let formatted_time = utc.format("%Y-%m-%d %H:%M:%S");
        let something = formatted_time
        ManagedBuffer::from(formatted_time)
    }
}
