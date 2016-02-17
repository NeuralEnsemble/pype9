

namespace nineml {

    namespace nest {

        class RingBuffer {

              void add_value( const long_t offs, const double_t );

              /**
               * Set a ring buffer entry to a given value.
               * @param  offs     Arrival time relative to beginning of slice.
               * @param  double_t Value to set.
               */
              void set_value( const long_t offs, const double_t );

              /**
               * Read one value from ring buffer.
               * @param  offs  Offset of element to read within slice.
               * @returns value
               */
              double get_value( const long_t offs );

              /**
               * Initialize the buffer with noughts.
               * Also resizes the buffer if necessary.
               */
              void clear();

              /**
               * Resize the buffer according to max_thread and max_delay.
               * New elements are filled with noughts.
               * @note resize() has no effect if the buffer has the correct size.
               */
              void resize();

              /**
               * Returns buffer size, for memory measurement.
               */
              size_t
              size() const
              {
                return buffer_.size();
              }

        };

    }
}
