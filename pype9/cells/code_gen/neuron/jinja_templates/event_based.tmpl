:VERBATIM
:extern double nineml_gsl_normal(double, double);
:extern double nineml_gsl_uniform(double, double);
:extern double nineml_gsl_binomial(double, int);
:extern double nineml_gsl_exponential(double);
:extern double nineml_gsl_poisson(double);
:ENDVERBATIM

TITLE Spiking node generated from the 9ML file $input_filename using 9ml2nmodl.py version $version

NEURON {
    ARTIFICIAL_CELL $component.name
    RANGE regime

    :StateVariables
  #for sv in $component.state_variables
    RANGE $sv.name
  #end for

    :Parameters
  #for p in $component.parameters
    RANGE $p.name
  #end for

    :Aliases
  #for alias in $component.aliases
    RANGE $alias.lhs
  #end for
}

CONSTANT {
    EXTERNAL_EVENT = 0
    INIT = 1

  #for regime in $component.regimes
    $regime.label = $regime.flag
  #end for

  #for transition in $component.transitions
    $transition.label = $transition.flag
  #end for
}

INITIAL {
    : Initialise State Variables  # should we do this? They should be initialised externally
  #for var in $component.state_variables:
    :$var.name = 0
  #end for

    : Initialise Regime
    regime = $initial_regime

    : Initialise the NET_RECEIVE block
    net_send(0, INIT)
}

PARAMETER {
  #for p in $component.parameters
    $p.name = 0
  #end for
}

ASSIGNED {
    regime
  #for var in $component.state_variables:
    $var.name
  #end for
  #for alias in $component.aliases:
    $alias.lhs
  #end for
}

NET_RECEIVE(w) {

    :printf("Received event at %f\n", t)

    if (flag == INIT) {
      #for regime in $component.regimes
       #for transition in $regime.on_conditions
        net_send($transition.trigger.rhs.replace("t > ", ""), $transition.flag)
        : fragile hack: we assume a trigger of the form 't > X'
       #end for
      #end for
    } else if (flag == EXTERNAL_EVENT) {

    }

  #for regime in $component.regimes:
   #for transition in $regime.on_conditions:
    if (flag == $transition.flag) {
        regime = $transition.target_regime.flag
       #for node in $transition.event_outputs
        net_event(t)
       #end for

       #for sa in transition.state_assignments
        $sa.lhs  = $sa.neuron_rhs
       #end for
       
       net_send($transition.trigger.rhs.replace("t > ", "") - t, $transition.flag)
    }
   #end for
  #end for

}
