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
    fn signup_trainer(&self, job_hash: ManagedBuffer) {
        let caller = self.blockchain().get_caller();
        self.trainers(&job_hash).insert(caller);
    }

    #[endpoint]
    fn remove_trainer(&self, job_hash: ManagedBuffer) -> bool {
        let caller = self.blockchain().get_caller();
        self.trainers(&job_hash).swap_remove(&caller)
    }

    #[view]
    fn trainers_count(&self, job_hash: ManagedBuffer) -> usize {
        self.trainers(&job_hash).len()
    }

    #[view]
    fn iterate_trainers(&self, job_hash: ManagedBuffer) -> ManagedBuffer {
        let result: ManagedBuffer = ManagedBuffer::new();
        for trainer in self.trainers(&job_hash).iter() {
            let another = trainer.as_managed_buffer();
            result.clone().concat(ManagedBuffer::from(" | "));
            result.clone().concat(another.clone());
        };
        result
    }

    #[endpoint]
    fn set_ipfs_file(&self, address: ManagedBuffer, client_id: u32) {
        self.client_by_ipfs_address(&address).set(client_id);
        self.ipfs_address_by_client(&client_id).set(address.clone());
        self.new_flchain_event(client_id, address.clone());
    }

    #[endpoint]
    fn set_genesis_address(&self, address: ManagedBuffer) {
        self.genesis_address().set(&address);
    }

    #[endpoint]
    fn set_global_version_address(&self, address: ManagedBuffer) {
        self.global_model_version().set(&address);
    }

    #[view]
    fn get_genesis_address(&self) -> ManagedBuffer{
        require!(
            !self.genesis_address().is_empty(),
            "This genesis address has not been inserted before!"
        );
        self.genesis_address().get()
    }

    #[view]
    fn get_global_version_address(&self) -> ManagedBuffer{
        require!(
            !self.global_model_version().is_empty(),
            "There is no global version available!"
        );
        self.global_model_version().get()
    }

    #[event("new_flchain_event")]
    fn new_flchain_event(
        &self,
        #[indexed] client_id: u32,
        data: ManagedBuffer
    );

    // #[storage_mapper("trainers")]
    // fn trainers(&self, job_id: &u32) -> UnorderedSetMapper<ManagedAddress[]>;

    #[storage_mapper("trainers")]
    fn trainers(&self, job_hash: &ManagedBuffer) -> UnorderedSetMapper<ManagedAddress>;

    #[storage_mapper("caller_storage")]
    fn caller_storage(&self) -> SingleValueMapper<ManagedAddress>;

    #[storage_mapper("global_model_version")]
    fn global_model_version(&self) -> SingleValueMapper<ManagedBuffer>;

    #[storage_mapper("genesis_address")]
    fn genesis_address(&self) -> SingleValueMapper<ManagedBuffer>;

    #[storage_mapper("client_by_ipfs_address")]
    fn client_by_ipfs_address(&self, address: &ManagedBuffer) -> SingleValueMapper<u32>;

    #[storage_mapper("ipfs_address_by_client")]
    fn ipfs_address_by_client(&self, client_id: &u32) -> SingleValueMapper<ManagedBuffer>;
}   
