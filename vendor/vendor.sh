if $STATIC
    export PACKAGES="emsdk harfang"
else
    export PACKAGES="emsdk"
fi
export VENDOR=harfang
export LD_VENDOR="-sUSE_WEBGL2 -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sFULL_ES2 -sFULL_ES3" 
