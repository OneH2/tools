CC=gcc
CFLAGS=`pkg-config --cflags --libs libmodbus`

locationServices: locationservices.c
	$(CC) locationservices.c $(CFLAGS) -o $@

clean:
	rm locationServices
