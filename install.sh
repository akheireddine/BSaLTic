#!/bin/bash



if [ ! -z packages ]; then
	echo "NEED TO INSTALL PACKAGES LISTED IN PACKAGES.TXT FILE. STORE .DEB FILES IN A NEW packages REPOSITORY." 
	exit 1
fi

cd packages
dpkg -i *.deb

pip3 install *.whl

cd ../spot

./configure && make 
#&& make check && make install


cd ../sources


echo " ******************* ANALYZE SECTION UNAVAILABLE DUE TO INSTANCES SIZE ******************* "

git checkout log

make cleanall
make all
cp bsaltic_analyzer ..


git checkout master

make cleanall
make all
cp bsaltic ..


cd ..

echo "Installation done".
