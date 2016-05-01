#ifndef EXCEPTIONS_H
#define EXCEPTIONS_H

namespace nest {

    class KernelException: public std::exception {
      public:
        KernelException(const std::string& name) {
        }
    };

    class GSLSolverFailure : public KernelException {
      public:
        GSLSolverFailure(const std::string& name, int status) : KernelException(name) {}
    };

    class UnknownReceptorType: public std::exception {
      public:
        UnknownReceptorType(const port& port, const std::string& name) {
        }
    };

    class IncompatibleReceptorType: public std::exception {
      public:
        IncompatibleReceptorType(const port& port,
                const std::string& name, const std::string& msg) {
        }
    };

}

#endif
