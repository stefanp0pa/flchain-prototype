#![no_std]

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
    fn retrieve_client_id_by_address(&self, address: ManagedBuffer) -> u32{
        require!(
            !self.client_by_ipfs_address(&address).is_empty(),
            "This address has not been inserted before!"
        );

        self.client_by_ipfs_address(&address).get()
    }

    #[view]
    fn retrieve_address_by_client_id(&self, client_id: u32) -> ManagedBuffer{
        require!(
            !self.ipfs_address_by_client(&client_id).is_empty(),
            "This client id has not been inserted before!"
        );

        self.ipfs_address_by_client(&client_id).get()
    }

    #[endpoint]
    fn store_ipfs_file(&self, address: ManagedBuffer, client_id: u32) {
        self.client_by_ipfs_address(&address).set(client_id);
        self.ipfs_address_by_client(&client_id).set(address);
    }

    #[storage_mapper("client_by_ipfs_address")]
    fn client_by_ipfs_address(&self, address: &ManagedBuffer) -> SingleValueMapper<u32>;

    #[storage_mapper("ipfs_address_by_client")]
    fn ipfs_address_by_client(&self, client_id: &u32) -> SingleValueMapper<ManagedBuffer>;
}   
