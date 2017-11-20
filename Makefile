WORKDIR=/nonexists

all: gen

gen: ${WORKDIR}/parts ${WORKDIR}/parts/1111.jpg
	python3 gen.py ${WORKDIR}/data/Open_Data/compmap.json ${WORKDIR}/parts images

${WORKDIR}/parts:
	unzip -d ${WORKDIR} ${WORKDIR}/data/Open_Data/Properties/CNS_component_word.zip

${WORKDIR}/parts/1111.jpg:
	wget -O ${WORKDIR}/parts/1111.jpg http://www.cns11643.gov.tw/AIDB/images/parts/1111.jpg
