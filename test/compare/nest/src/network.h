#ifndef NETWORK_H
#define NETWORK_H

#include "random.h"


namespace nest {

    class Scheduler {
      public:
        static delay get_min_delay() { return LONG_MAX; }
        static delay min_delay;
        static delay max_delay;
    };

    class Network {
      public:
        Network(long seed=1234567890);
        Network(const Network& net) : rng_(net.rng_) {}
        void send(Node& node, SpikeEvent& se, long_t lag) {}
        librandom::RngPtr get_rng(int dummy) { return rng_; }
        const Time& get_slice_origin() const;
      private:
        librandom::RngPtr rng_;
    };

}

#endif
