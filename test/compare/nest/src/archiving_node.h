#ifndef ARCHIVING_NODE_H
#define ARCHIVING_NODE_H

#include "dict.h"
#include "network.h"
#include "event.h"
#include "nest_names.h"

namespace nest {

    class Node {
      public:
        Node() : net_(new Network()) {}
        Node(const Node& node) : net_(node.net_) {}
        virtual ~Node() { delete net_; }
        void handle(SpikeEvent& event);
        void handle(CurrentEvent& event);
        port handles_test_event(SpikeEvent& event, port receptor_type);

        std::string get_name() { return "TestNode"; }
        void set_spiketime(Time const& t_sp ) {}
        int get_thread() const { return 0; }

        template < typename ConcreteNode > const ConcreteNode& downcast( const Node& n ) {
          ConcreteNode const* tp = dynamic_cast< ConcreteNode const* >( &n );
          assert( tp != 0 );
          return *tp;
        }

        Network* network() { return net_; }

      public:
        Network *net_;

    };

    class Archiving_Node : public Node {
      public:
        Archiving_Node() : last_spike_(-1.0) {}
        Archiving_Node(const Archiving_Node& node) : Node(node), last_spike_(node.last_spike_) {}
        virtual ~Archiving_Node() {}
        virtual void get_status(DictionaryDatum& d) const = 0;
        virtual void set_status(const DictionaryDatum& d) = 0;
        double_t get_spiketime_ms() const { return last_spike_; }
        void set_spiketime_ms(double_t st) { last_spike_ = st; }
        void clear_history() {}

        double_t last_spike_;

    };

}

#endif
