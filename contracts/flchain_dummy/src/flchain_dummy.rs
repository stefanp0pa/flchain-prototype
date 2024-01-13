#![no_std]

multiversx_sc::imports!();
multiversx_sc::derive_imports!();

mod user;
mod participant_role;
mod session_manager;
use user::User;
use participant_role::Role;
use session_manager::SessionManager;

const ROUND_SECONDS: u64 = 6;
const ROUNDS_FOR_SIGNUP: u64 = 6;
const ROUNDS_FOR_TRAINING: u64 = 5;
const ROUNDS_FOR_AGGREGATION: u64 = 2;

#[derive(NestedEncode, NestedDecode, TopEncode, TopDecode, TypeAbi)]
struct Participant {
    user: User,
    role: Role
}

/// An empty contract. To be used as a template when starting a new contract from scratch.
#[multiversx_sc::contract]
pub trait FlchainDummy {

    #[init]
    fn init(&self) {
    }

    #[upgrade]
    fn upgrade(&self) {
    }

    #[endpoint]
    fn start_session(
        &self,
        global_model_addr: ManagedBuffer,
        rounds_signup: u64,
        rounds_training: u64,
        rounds_aggregation: u64
    ) {
        require!(
            self.active_session_manager().is_empty(),
            "Training session already started!"
        );

        let now = self.blockchain().get_block_timestamp();
        let caller: ManagedAddress = self.blockchain().get_caller();

        let mut rand_source = RandomnessSource::new();
        let session_id = rand_source.next_u64_in_range(0u64, 1000u64);
        self.active_session_manager().set(SessionManager {
            session_id,
            start_time: now,
            rounds_signup,
            rounds_training,
            rounds_aggregation,
            round_seconds: ROUND_SECONDS,
        });

        self.active_session_proposer().set(caller);
        self.global_model_versions(0u32).insert(global_model_addr);
        self.version().set(0u32);

        self.session_started_event(session_id, now, rounds_signup, rounds_training, rounds_aggregation);
    }

    #[endpoint]
    fn end_session(&self) {
        require!(
            !self.active_session_manager().is_empty(),
            "Training session empty or already ended!"
        );
        
        let curr_time = self.blockchain().get_block_timestamp();
        let session_id = self.active_session_manager().get().session_id;

        self.clear_round_entities();
        self.session_ended_event(session_id, curr_time);
    }

    fn clear_round_entities(&self) {
        let max_version = self.version().get();
        for i in 0u32..max_version {
            self.global_model_versions(i).clear();
        }

        self.version().clear();
        self.active_session_proposer().clear();
        self.active_session_manager().clear();
    }

    #[view]
    fn is_session_active(&self) -> bool {
        !self.active_session_manager().is_empty()
    }

    #[view]
    fn get_active_session(&self) -> u64 {
        require!(
            !self.active_session_manager().is_empty(),
            "No training session available!"
        );
        self.active_session_manager().get().session_id
        // let mut encoded = ManagedBuffer::new();
        // let _ = self.active_session_manager().get().top_encode(&mut encoded);
        // encoded
    }

    #[view]
    fn is_signup_open(&self) -> bool {
        require!(
            !self.active_session_manager().is_empty(),
            "No training session available!"
        );

        let curr_time = self.blockchain().get_block_timestamp();
        self.active_session_manager().get().is_signup_open(curr_time)
    }

    #[view]
    fn is_training_open(&self) -> bool {
        require!(
            !self.active_session_manager().is_empty(),
            "No training session available!"
        );

        let curr_time = self.blockchain().get_block_timestamp();
        self.active_session_manager().get().is_training_open(curr_time)
    }

    #[view]
    fn is_aggregation_open(&self) -> bool {
        require!(
            !self.active_session_manager().is_empty(),
            "No training session available!"
        );

        let curr_time = self.blockchain().get_block_timestamp();
        self.active_session_manager().get().is_aggregation_open(curr_time)
    }

    #[view]
    fn get_proposer(&self) -> ManagedAddress {
        require!(
            !self.active_session_proposer().is_empty(),
            "No training session available!"
        );

        self.active_session_proposer().get()
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
    fn get_string_vector(&self) -> ManagedVec<ManagedBuffer> {
        let mut result: ManagedVec<ManagedBuffer> = ManagedVec::new();
        result.push(ManagedBuffer::from("Hello"));
        result.push(ManagedBuffer::from("World"));
        result
    }

    // #[view]
    // fn iterate_trainers(&self, job_hash: ManagedBuffer) -> ManagedBuffer {
    //     let result: ManagedBuffer = ManagedBuffer::new();
    //     for trainer in self.trainers(&job_hash).iter() {
    //         let another = trainer.as_managed_buffer();
    //         result.clone().concat(ManagedBuffer::from(" | "));
    //         result.clone().concat(another.clone());
    //     };
    //     result
    // }


    #[view]
    fn get_timestamp(&self) -> u64 {
        self.blockchain().get_block_timestamp()
    }

    #[endpoint]
    fn set_ipfs_file(&self, address: ManagedBuffer, client_id: u32) {
        self.client_by_ipfs_address(&address).set(client_id);
        self.ipfs_address_by_client(&client_id).set(address.clone());
    }

    // #[endpoint]
    // fn set_genesis_address(&self, address: ManagedBuffer) {
    //     self.genesis_address().set(&address);
    // }

    // #[endpoint]
    // fn set_global_version_address(&self, address: ManagedBuffer) {
    //     self.global_model_version().set(&address);
    // }

    // #[view]
    // fn get_genesis_address(&self) -> ManagedBuffer{
    //     require!(
    //         !self.genesis_address().is_empty(),
    //         "This genesis address has not been inserted before!"
    //     );
    //     self.genesis_address().get()
    // }

    // #[view]
    // fn get_global_version_address(&self) -> ManagedBuffer{
    //     require!(
    //         !self.global_model_version().is_empty(),
    //         "There is no global version available!"
    //     );
    //     self.global_model_version().get()
    // }

    // Events.............................................

    #[event("session_started_event")]
    fn session_started_event(
        &self,
        #[indexed] session_id: u64,
        #[indexed] start_time: u64,
        #[indexed] rounds_signup: u64,
        #[indexed] rounds_training: u64,
        #[indexed] rounds_aggregation: u64,
    );

    #[event("session_ended_event")]
    fn session_ended_event(
        &self,
        #[indexed] session_id: u64,
        #[indexed] end_time: u64,
    );

    #[event("new_signup_event")]
    fn new_signup_event(
        &self,
        #[indexed] session_id: u64,
        #[indexed] user: ManagedAddress,
        #[indexed] role: Role,
    );

    // ----------------------------------------------------

    // #[storage_mapper("trainers")]
    // fn trainers(&self, session_id: &u32) -> UnorderedSetMapper<ManagedAddress[]>;
    #[storage_mapper("active_session_manager")]
    fn active_session_manager(&self) -> SingleValueMapper<SessionManager>;

    #[storage_mapper("active_session_proposer")]
    fn active_session_proposer(&self) -> SingleValueMapper<ManagedAddress>;

    #[storage_mapper("global_model_versions")]
    fn global_model_versions(&self, version: u32) -> UnorderedSetMapper<ManagedBuffer>;

    #[storage_mapper("version")]
    fn version(&self) -> SingleValueMapper<u32>;

    // -----------------------------------------------

    // stores all the users that have signeup up so far in a round
    #[storage_mapper("users")]
    fn users(&self, address: ManagedAddress) -> UnorderedSetMapper<User>;

    #[storage_mapper("participants")]
    fn participants(&self, session_id: u64) -> UnorderedSetMapper<Participant>;

    // -----------------------------------------------


    
    #[storage_mapper("trainers")]
    fn trainers(&self, job_hash: &ManagedBuffer) -> UnorderedSetMapper<ManagedAddress>;

    #[storage_mapper("caller_storage")]
    fn caller_storage(&self) -> SingleValueMapper<ManagedAddress>;

    

    

    #[storage_mapper("client_by_ipfs_address")]
    fn client_by_ipfs_address(&self, address: &ManagedBuffer) -> SingleValueMapper<u32>;

    #[storage_mapper("ipfs_address_by_client")]
    fn ipfs_address_by_client(&self, client_id: &u32) -> SingleValueMapper<ManagedBuffer>;
}   
