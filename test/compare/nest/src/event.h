#ifndef EVENT_H
#define EVENT_H

namespace nest {

    class Node;
    class Archiving_Node;

    class Event {
      public:
        Event() : d_(0), w_(0), rp_(0) {}
        void set_sender(Archiving_Node& node) {}
        double_t get_delay() const { return d_; }
        double get_weight() const { return w_; }
        long_t get_rel_delivery_steps(const Time& time) const;
        int get_rport() const { return rp_; }

        // Public members
        delay d_;
        weight w_;
        int rp_;
    };

    class SpikeEvent : public Event {
      public:
        SpikeEvent() : m_(0) {}
        void set_multiplicity(long_t m) { m_ = m; }
        double_t get_delay() const { return d_; }
        double get_weight() const { return w_; }

        // Public members
        long_t m_;

    };

    class CurrentEvent : public Event {
      public:
        CurrentEvent() : c_(0.0) {}
        double get_current() const { return c_; }

        //Public members
        double c_;

    };

}

#endif
