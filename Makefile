WORKDIR=/nonexists

all: gen

gen: ${WORKDIR}/parts
	python3 gen.py ${WORKDIR}/data/Open_Data/compmap.json ${WORKDIR}/parts images

${WORKDIR}/parts:
	unzip -d ${WORKDIR} ${WORKDIR}/data/Open_Data/Properties/CNS_component_word.zip
