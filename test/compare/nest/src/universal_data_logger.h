#ifndef UNIVERSAL_DATA_LOGGER_H
#define UNIVERSAL_DATA_LOGGER_H

namespace nest {

    class DataLoggingRequest {
      public:
        void handle(const SpikeEvent& e) {}
        void handle(const CurrentEvent& e) {}
    };


    template <class NodeType> class UniversalDataLogger {
      public:
        UniversalDataLogger() {}
        UniversalDataLogger(NodeType& node);
        ~UniversalDataLogger();
        port connect_logging_device(DataLoggingRequest& request,
                RecordablesMap<NodeType>& map);
        void init() {}
        void reset() {}
        void record_data(long_t step);
        void handle(const DataLoggingRequest& dlr) {}
      private:
        std::ofstream* output_file;
        NodeType* node_;
    };

}

#endif
