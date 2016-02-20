#ifndef MOCK_NEST_H
#define MOCK_NEST_H

namespace std {
#include <math.h>
}
#include <vector>
#include <map>
#include "name.h"
#include "datum.h"
#include "dict.h"


class DictionaryDatum {

};

typedef double double_t;



namespace nest {

    enum names {
        receptor_type,
        t_spike,
        recordables
    };

    typedef int synindex;
    typedef long long_t;
    typedef int port;

    class Archiving_Node;

    class KernelException : public std::exception {};

    class UnknownReceptorType : public std::exception {
      public:
        UnknownReceptorType(const port& port, const std::string& name) {}
    };

    class IncompatibleReceptorType : public std::exception {
      public:
        IncompatibleReceptorType(const port& port, const std::string& name, const std::string& msg) {}
    };

    class DataLoggingRequest {

    };

    class Time {

    };

    class SpikeEvent {
      public:
        void set_sender(Archiving_Node& node);
    };

    class CurrentEvent {

    };

    template <class NodeType> class RecordablesMap {
        public:
            std::vector<port> get_list();
    };

    template <class NodeType> class UniversalDataLogger {
      public:
        port connect_logging_device(DataLoggingRequest& request, RecordablesMap<NodeType>& map);
    };

    class RingBuffer {
      public:
        void add_value( const long_t offs, const double_t );
        void set_value( const long_t offs, const double_t );
        double get_value( const long_t offs );
        void clear();
        void resize();
    };


    class Node {
      public:
        void handle(SpikeEvent& event);
        void handle(CurrentEvent& event);
        port handles_test_event(nest::SpikeEvent& event, nest::port receptor_type);
        port handles_test_event(nest::CurrentEvent& event, nest::port receptor_type);
        std::string get_name() { return "TestNode"; }
    };


    class Archiving_Node : public Node {
      public:
        void get_status(DictionaryDatum& d) const;
        void set_status(const DictionaryDatum& d);
        double_t get_spiketime_ms() const;

    };

}

namespace librandom {

    class RngPtr {
        public:
          double drand();
          double drandpos();
    };

}

#endif
