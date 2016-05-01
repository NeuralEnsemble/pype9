#ifndef UNIVERSAL_DATA_LOGGER_IMPL_H
#define UNIVERSAL_DATA_LOGGER_IMPL_H

#include "universal_data_logger.h"

namespace nest {

    template <class NodeType> UniversalDataLogger<NodeType>::UniversalDataLogger(NodeType& node)
      : node_(&node) {
        std::string path = ::get_data_path<NodeType>();
        std::cout << "Writing output to " << path << std::endl;
        output_file = new std::ofstream(path);
    }

    template <class NodeType> UniversalDataLogger<NodeType>::~UniversalDataLogger() {
        delete output_file;
    }

    template <class NodeType> void UniversalDataLogger<NodeType>::record_data(long_t step) {
        if (!step) {
            (*output_file) << "# ";
            for (typename RecordablesMap<NodeType>::iterator it = node_->recordablesMap_.begin(); it != node_->recordablesMap_.end(); ++it)
                (*output_file) << it->first << " ";
            (*output_file) << std::endl;
        }
        for (typename RecordablesMap<NodeType>::iterator it = node_->recordablesMap_.begin(); it != node_->recordablesMap_.end(); ++it)
            (*output_file) << ((*node_).*(it->second))()  << " ";
        (*output_file) << std::endl;
    }

}

#endif
