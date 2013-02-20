'''
Created on Feb 5, 2013

@author: Lisicovas
'''
# A little script to plot a set of periodic equations. Done to improve the knowledge of scipy.

#Imported modules

import math
import pylab
import numpy


#Custom functions

def Intensity (b,d, amplitude, omega, wavelength):
    Iarray = []
    for i in omega: 
        beta=math.pi*b*math.sin(omega[i])/wavelength
        gamma=math.pi*d*math.sin(omega[i])/wavelength
        I=4*(amplitude**2)*(math.sin(beta)**2)*(math.cos(gamma)**2)/(beta**2)
        Iarray.append(I)
    return Iarray

def Plotter(omega, intensity):
    pylab.plot(omega, intensity) 
    pylab.xlabel('Angle [rad]')
    pylab.ylabel('Intensity')
    pylab.title('Interference pattern')
    pylab.grid(True)
    pylab.show()
    return

    
#Variable definitions

omega = numpy.arange(math.pi, 100*math.pi, math.pi/2**11)
b = 1
d = 100
amplitude = 10
wavelength = 10


#Simulating interference

a = Intensity (b,d, amplitude, omega, wavelength)

Plotter(omega, a)