

namespace test {


    class RingBuffer
    {

      public:
        RingBuffer();

        /**
        * Add a value to the ring buffer.
        * @param  offs     Arrival time relative to beginning of slice.
        * @param  double_t Value to add.
        */
        void add_value( const long_t offs, const double_t );

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

    inline void
    RingBuffer::add_value( const long_t offs, const double_t v )
    {
      buffer_[ get_index_( offs ) ] += v;
    }

    inline void
    RingBuffer::set_value( const long_t offs, const double_t v )
    {
      buffer_[ get_index_( offs ) ] = v;
    }

    inline double
    RingBuffer::get_value( const long_t offs )
    {
      assert( 0 <= offs && ( size_t ) offs < buffer_.size() );
      assert( ( delay ) offs < Scheduler::get_min_delay() );

      // offs == 0 is beginning of slice, but we have to
      // take modulo into account when indexing
      long_t idx = get_index_( offs );
      double_t val = buffer_[ idx ];
      buffer_[ idx ] = 0.0; // clear buffer after reading
      return val;
    }

    inline size_t
    RingBuffer::get_index_( const delay d ) const
    {
      const long_t idx = Scheduler::get_modulo( d );
      assert( 0 <= idx );
      assert( ( size_t ) idx < buffer_.size() );
      return idx;
    }



}
