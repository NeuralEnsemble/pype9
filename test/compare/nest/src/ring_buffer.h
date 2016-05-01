#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <valarray>
#include <vector>
#include "nest.h"

namespace nest {

    class RingBuffer {
      public:
        RingBuffer();

        void add_value( const long_t offs, const double_t ) {}
        void set_value( const long_t offs, const double_t );
        double get_value( const long_t offs );
        void clear() {}
        static delay get_modulo( delay d );

    private:
      //! Buffered data
      std::valarray< double_t > buffer_;

      /**
       * Obtain buffer index.
       * @param delay delivery delay for event
       * @returns index to buffer element into which event should be
       * recorded.
       */
      size_t get_index_( const delay d ) const;
    };


    class ListRingBuffer {

      public:
        ListRingBuffer();

        /**
        * Append a value to the ring buffer list.
        * @param  offs     Arrival time relative to beginning of slice.
        * @param  double_t Value to append.
        */
        void append_value( const long_t offs, const double_t );
        std::list< double_t >& get_list( const long_t offs );
        void clear() {}
        size_t size() const { return buffer_.size(); }

      private:
        //! Buffered data
        std::vector< std::list< double_t > > buffer_;

    };

}

#endif
