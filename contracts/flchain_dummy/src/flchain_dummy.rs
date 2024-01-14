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
// const ROUNDS_FOR_SIGNUP: u64 = 6;
// const ROUNDS_FOR_TRAINING: u64 = 5;
// const ROUNDS_FOR_AGGREGATION: u64 = 2;

#[derive(NestedEncode, NestedDecode, TopEncode, TopDecode, TypeAbi)]
pub struct Participant<M: ManagedTypeApi> {
    user_addr: ManagedAddress<M>,
    role: Role
}

#[derive(NestedEncode, NestedDecode, TopEncode, TopDecode, TypeAbi)]
pub struct ModelUpdate<M: ManagedTypeApi, N: ManagedTypeApi> {
    user_addr: ManagedAddress<M>,
    file_location: ManagedBuffer<N>
}


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
        // self.global_model_versions(0u32).set(global_model_addr);
        // self.version().set(0u32);
        self.version(session_id).set(0u32);
        self.global_updates(session_id, 0u32).insert(ModelUpdate {
            user_addr: self.blockchain().get_caller(),
            file_location: global_model_addr,
        });
        self.participants(session_id).insert(Participant {
            user_addr: self.blockchain().get_caller(),
            role: Role::Proposer,
        });

        self.session_started_event(session_id, now, rounds_signup, rounds_training, rounds_aggregation);
        self.new_signup_event(session_id, self.blockchain().get_caller(), Role::Proposer);
    }

    #[endpoint]
    fn end_session(&self) {
        require!(
            !self.active_session_manager().is_empty(),
            "Training session empty or already ended!"
        );
        
        let curr_time = self.blockchain().get_block_timestamp();
        let session_id = self.active_session_manager().get().session_id;

        self.clear_round_entities(session_id);
        self.session_ended_event(session_id, curr_time);
    }

    #[endpoint]
    fn signup(&self, role: u8) {
        require!(
            !self.active_session_manager().is_empty(),
            "Cannot signup! No training session ongoing!"
        );
        // let curr_time = self.blockchain().get_block_timestamp();
        let session_manager = self.active_session_manager().get();
        // require!(
        //     session_manager.is_signup_open(curr_time),
        //     "Cannot register! Sign-up period is over!"
        // );

        let caller_addr = self.blockchain().get_caller();
        let session_id = session_manager.session_id;
        require!(
            !self.has_signed_up(caller_addr, session_id),
            "Cannot signup! Already signed up!"
        );
        
        self.participants(session_id).insert(Participant {
            user_addr: self.blockchain().get_caller(),
            role: Role::match_role(role).unwrap(),
        });

        self.new_signup_event(
            session_id,
            self.blockchain().get_caller(),
            Role::match_role(role).unwrap());
    }

    fn has_signed_up(&self, caller_addr: ManagedAddress, session_id: u64) -> bool {
        let session_participants = self.participants(session_id);
        let count = session_participants
                        .iter()
                        .filter(|participant| {
                            (*participant).user_addr == caller_addr
                        })
                        .count();
        return count > 0;
    }

    fn clear_round_entities(&self, session_id: u64) {
        let max_version = self.version(session_id).get();
        for i in 0u32..max_version {
            self.global_updates(session_id, i).clear();
        }

        self.version(session_id).clear();
        self.participants(session_id).clear();
        self.active_session_proposer().clear();
        self.active_session_manager().clear();
    }

    #[view]
    fn trainers_count(&self, session_id: u64) -> usize {
        require!(
            !self.participants(session_id).is_empty(),
            "No participants in this session!"
        );
        
        let session_participants = self.participants(session_id);
        session_participants
                        .iter()
                        .filter(|participant| {
                            (*participant).role.can_train()
                        })
                        .count()
    }

    #[view]
    fn aggregators_count(&self, session_id: u64) -> usize {
        require!(
            !self.participants(session_id).is_empty(),
            "No participants in this session!"
        );
        
        let session_participants = self.participants(session_id);
        session_participants
                        .iter()
                        .filter(|participant| {
                            (*participant).role.can_upgate_global()
                        })
                        .count()
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
    fn get_session_proposer(&self) -> ManagedAddress {
        require!(
            !self.active_session_proposer().is_empty(),
            "No training session available!"
        );

        self.active_session_proposer().get()
    }

    // #[view]
    // fn get_current_global_version(&self) -> ManagedBuffer {
    //     require!(
    //         !self.active_session_proposer().is_empty(),
    //         "No training session available!"
    //     );

    //     let session_id = self.active_session_manager().get().session_id;
    //     let version = self.version(session_id).get();
    //     self.global_model_versions(version).get()
    // }


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

    // #[endpoint]
    // fn signup_trainer(&self, job_hash: ManagedBuffer) {
    //     let caller = self.blockchain().get_caller();
    //     self.trainers(&job_hash).insert(caller);
    // }

    // #[endpoint]
    // fn remove_trainer(&self, job_hash: ManagedBuffer) -> bool {
    //     let caller = self.blockchain().get_caller();
    //     self.trainers(&job_hash).swap_remove(&caller)
    // }

    #[view]
    fn get_string_vector(&self) -> ManagedVec<ManagedBuffer> {
        let mut result: ManagedVec<ManagedBuffer> = ManagedVec::new();
        // result.push(ManagedBuffer::from("Hello"));
        // result.push(ManagedBuffer::from("World"));
        // result
        self.local_updates(10u64, 21u32).insert(ManagedBuffer::from("Helloooo"));
        self.local_updates(10u64, 21u32).insert(ManagedBuffer::from("World"));
        self.local_updates(10u64, 22u32).insert(ManagedBuffer::from("cococ"));
        for update in self.local_updates(10u64, 21u32).iter() {
            result.push(update);
        }
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

    // #[storage_mapper("global_model_versions")]
    // fn global_model_versions(&self, version: u32) -> SingleValueMapper<ManagedBuffer>;

    

    // -----------------------------------------------

    // stores all the users that have signeup up so far in a round
    #[storage_mapper("users")]
    fn users(&self, address: ManagedAddress) -> UnorderedSetMapper<User>;

    #[storage_mapper("participants")]
    fn participants(&self, session_id: u64) -> UnorderedSetMapper<Participant<Self::Api>>;

    // -----------------------------------------------

    #[storage_mapper("local_updates")]
    fn local_updates(&self, session_id: u64, version: u32) -> UnorderedSetMapper<ManagedBuffer>;

    #[storage_mapper("global_updates")]
    fn global_updates(&self, session_id: u64, version: u32) -> UnorderedSetMapper<ModelUpdate<Self::Api, Self::Api>>;

    #[storage_mapper("version")]
    fn version(&self, session_id: u64) -> SingleValueMapper<u32>;



    #[storage_mapper("trainers")]
    fn trainers(&self, job_hash: &ManagedBuffer) -> UnorderedSetMapper<ManagedAddress>;

    #[storage_mapper("caller_storage")]
    fn caller_storage(&self) -> SingleValueMapper<ManagedAddress>;

    

    

    #[storage_mapper("client_by_ipfs_address")]
    fn client_by_ipfs_address(&self, address: &ManagedBuffer) -> SingleValueMapper<u32>;

    #[storage_mapper("ipfs_address_by_client")]
    fn ipfs_address_by_client(&self, client_id: &u32) -> SingleValueMapper<ManagedBuffer>;
}   
