all: libninemlnrn

libninemlnrn:
	gcc -fPIC -c -o nineml.o nineml.cpp -I/usr/local/Cellar/gsl/1.16/include
	gcc -shared -L/usr/local/Cellar/gsl/1.16/lib -lm -lgslcblas -lgsl -o libninemlnrn.so nineml.o -lc

clean:
	rm -f libninemlnrn.so nineml.o

