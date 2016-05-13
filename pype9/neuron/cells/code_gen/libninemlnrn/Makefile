all: libninemlnrn

libninemlnrn:
	gcc-5 -fPIC -c -o nineml.o nineml.cpp -I/usr/local/Cellar/gsl/1.16/include
	gcc-5 -shared -L/usr/local/Cellar/gsl/1.16/lib -lm -lgslcblas -lgsl -o libninemlnrn.so.1.0.1 nineml.o -lc
	ln -s libninemlnrn.so.1.0.1 libninemlnrn.so
	ln -s libninemlnrn.so.1.0.1 libninemlnrn.so.1

clean:
	rm -f libninemlnrn.so.1.0.1 libninemlnrn.so libninemlnrn.so.1 nineml.o

