PYTHON?=python3
BSDCONV_SRC?=
CNS11643_SRC?=

.PHONY: all build run clean
all: run

build:
	$(PYTHON) scripts/build.py $(if $(BSDCONV_SRC),--bsdconv "$(BSDCONV_SRC)") $(if $(CNS11643_SRC),--cns11643 "$(CNS11643_SRC)")

run: build
	$(PYTHON) -m http.server 8000 --bind 127.0.0.1 --directory dist

clean:
	rm -rf .build dist
