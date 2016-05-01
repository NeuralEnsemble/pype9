#ifndef RECORDABLES_MAP_H
#define RECORDABLES_MAP_H

#include "arraydatum.h"

namespace nest {

    template <class NodeType> class RecordablesMap : public std::map< Name, double_t (NodeType::*) () const> {
        typedef std::map< Name,  double_t (NodeType::*) () const> Base_;
      public:
        typedef double_t ( NodeType::*DataAccessFct )() const;
        virtual ~RecordablesMap() {}
        ArrayDatum get_list() const {
          ArrayDatum recordables;
          for ( typename Base_::const_iterator it = this->begin(); it != this->end(); ++it )
              recordables.push_back( new LiteralDatum( it->first ) );
          return recordables;

          // the entire function should just be
          // return recordables_;
        }
        void create() {}
        void insert_(const Name& n, const DataAccessFct f) {
            Base_::insert(std::make_pair(n, f));
        }
    };

}

#endif
