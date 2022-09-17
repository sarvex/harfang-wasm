#!/bin/bash

export SDKROOT=${SDKROOT:-/opt/python-wasm-sdk}
export CONFIG=${CONFIG:-$SDKROOT/config}


. ${CONFIG}

echo "

    * building Harfang3D for ${CIVER}, PYBUILD=$PYBUILD => CPython${PYMAJOR}.${PYMINOR}
            PYBUILD=$PYBUILD
            EMFLAVOUR=$EMFLAVOUR
            SDKROOT=$SDKROOT
            SYS_PYTHON=${SYS_PYTHON}

" 1>&2




mkdir -p src
pushd $(pwd)/src
    if [ -d harfang ]
    then
        pushd $(pwd)/harfang
        git restore .
        git pull
    else
        git clone --no-tags --depth 1 --single-branch --branch wasm https://github.com/pmp-p/python-harfang3d-wasm harfang
        pushd $(pwd)/harfang
        git submodule update --init --recursive
        git clone --depth 1 https://github.com/ejulien/FABGen fabgen
        cp -r extern/pypeg2 ${SDKROOT}/devices/x86_64/usr/lib/python3.11/site-packages/
        cp -r extern/pypeg2 ${SDKROOT}/devices/emsdk/usr/lib/python3.11/site-packages/
    fi
    export HG_SRC_DIR=$(pwd)

    FABGEN=$HG_SRC_DIR/fabgen
    sed -i 's|error|warning|g' ${HG_SRC_DIR}/extern/cmft/src/cmft/common/platform.h

popd
popd


mkdir -p build/harfang

pushd build/harfang

if which cmake
then
    echo "
    * using local cmake
" 1>&2
else
    $SYS_PYTHON -m pip install cmake
fi

# $SYS_PYTHON -m pip install pypeg2
/opt/python-wasm-sdk/python3-wasm -m pip install pypeg2

. ${SDKROOT}/emsdk/emsdk_env.sh
export EMSDK_PYTHON=$SYS_PYTHON


emcmake cmake $HG_SRC_DIR \
 -DCMAKE_INSTALL_PREFIX=$PREFIX \
 -DHG_CPPSDK_PATH=${PREFIX} \
 -DHG_FABGEN_PATH=${FABGEN} \
 -DHG_GRAPHIC_API=GLES \
 -DHG_USE_GLFW=OFF \
 -DHG_BUILD_GLTF_EXPORTER=OFF \
 -DHG_BUILD_GLTF_IMPORTER=OFF \
 -DHG_BUILD_SPHERICAL_HARMONICS_EXTRACTOR=OFF \
 -DHG_BUILD_ASSETC=OFF \
 -DHG_ENABLE_OPENVR_API=OFF \
 -DHG_ENABLE_OPENXR_API=OFF \
 -DHG_ENABLE_BULLET3_SCENE_PHYSICS=OFF \
 -DHG_BUILD_ASSIMP_CONVERTER=OFF \
 -DHG_BUILD_FBX_CONVERTER=OFF \
 -DHG_BUILD_TESTS=OFF \
 -DHG_BUILD_ASSETC=OFF \
 -DHG_BUILD_HG_LUA=OFF \
 -DHG_BUILD_CPP_SDK=OFF \
 -DHG_BUILD_HARFANG_STATIC=ON \
 -DHG_BUILD_HG_PYTHON:BOOL=ON \
    -DPython3_EXECUTABLE:FILEPATH=${SDKROOT}/python3-wasm \
    -DPython3_INCLUDE_DIR=${SDKROOT}/devices/emsdk/usr/include/python${PYBUILD} \
    -DPython3_LIBRARY=${SDKROOT}/devices/emsdk/usr/lib \
    -DPython3_FOUND=TRUE \
    -DPython3_Development_FOUND=TRUE \
    -DPython3_Development.Module_FOUND=TRUE \
    -DPython3_Development.Embed_FOUND=TRUE \


#
if EMCC_CFLAGS="-DBX_CONFIG_DEBUG=0 -I${SDKROOT}/devices/emsdk/usr/include/python${PYBUILD} -Wno-unused-command-line-argument -lopenal" make -j4
then
    HG=$(pwd)
    cd $HG_SRC_DIR/wasm_test


    LINKALL=""

    for lib in $(find ${HG}/extern| grep lib.*.a$|grep -v stb_vorbis)
    do
        LINKALL="$LINKALL $lib"
    done

    for lib in\
      harfang/foundation/libfoundation.a\
      harfang/platform/libplatform.a\
      harfang/script/libscript.a\
      harfang/engine/libengine.a
    do
        LINKALL="$LINKALL ${HG}/$lib"
    done

    LD_HARFANG="-lopenal -lSDL2 $LINKALL"

    echo "
        *   building cpp test :
http://localhost:8000/archives/${PYGBAG_BUILD}/harfang_cpptest.html
" 1>&2


    em++ \
     -sUSE_WEBGL2 \
     -sALLOW_MEMORY_GROWTH \
     -I${HG_SRC_DIR}/harfang \
     -I${HG_SRC_DIR}/extern \
     -I${HG_SRC_DIR}/extern/bgfx/bgfx/include \
     -I${HG_SRC_DIR}/extern/bgfx/bimg/include \
     -o $DIST_DIR/harfang_cpptest.html app.cpp mdl_gles_fsb.cpp mdl_gles_vsb.cpp $LD_HARFANG

lib=languages/hg_python/harfang.a
LINKALL="$LINKALL ${HG}/$lib"

    echo "

Linking :
    $LINKALL
Into : ${SDKROOT}/prebuilt/emsdk/libharfang${PYBUILD}.a

" 1>&2
    emcc -r -Wl,--whole-archive -o libharfang${PYBUILD}.o $LINKALL
    emar cr ${SDKROOT}/prebuilt/emsdk/libharfang${PYBUILD}.a libharfang${PYBUILD}.o

    du -hs ${SDKROOT}/prebuilt/emsdk/libharfang${PYBUILD}.a

else
    echo build failed
    exit 66
fi

popd





