BOS_BIN_DIR=${DESTDIR}/usr/bin/
BCLI_DIR=${DESTDIR}/usr/lib/boscli/

build:
	echo "build: Nothing to do"

install:
	echo "install: ${dir}"

	mkdir -p ${BOS_BIN_DIR} 

	install -m 775 -o root -g root -d ${BOS_BIN_DIR}/
	install -m 775 -o root -g root bin/* ${BOS_BIN_DIR}/

	cd src && find . -type d -exec install -m 775 -o root -g root -d ${BCLI_DIR}/\{} \; && cd -
	cd src && find . -type f -exec install -m 664 -o root -g root \{} ${BCLI_DIR}/\{} \; && cd -

	# Eliminamos ficheros de subversion
	find ${BCLI_DIR}/ -type d -name ".svn" -exec rm -rf \{} \; 2>/dev/null || echo

clean:
	echo "clean: Nothing to do"


distclean: clean
