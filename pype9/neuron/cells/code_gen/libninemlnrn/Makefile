all: libninemlnrn

libninemlnrn:
	gcc-5 -fPIC -c -o nineml.o nineml.cpp -I/usr/local/Cellar/gsl/1.16/include
	gcc-5 -shared -L/usr/local/Cellar/gsl/1.16/lib -lm -lgslcblas -lgsl -o libninemlnrn.dylib nineml.o -lc

clean:
	rm -f libninemlnrn.dylib nineml.o

