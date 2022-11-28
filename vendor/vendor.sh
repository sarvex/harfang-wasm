if echo "$PACKAGES" |grep -q emsdk
then
    # mixed static
    export PACKAGES="$PACKAGES harfang"
else
    # standalone
    export PACKAGES="emsdk harfang"
fi
export VENDOR=harfang
export LD_VENDOR="$LD_VENDOR -sUSE_WEBGL2 -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sFULL_ES2 -sFULL_ES3" 
