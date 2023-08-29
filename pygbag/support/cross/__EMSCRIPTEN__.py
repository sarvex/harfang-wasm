# builtins.__EMSCRIPTEN__
# builtins.__WASI__
# builtins.__ANDROID__   also defines __ANDROID_API__
# builtins.__UPY__ too can point to this module

import sys, os, builtins
import json

builtins.builtins = builtins

builtins.true = True
builtins.false = False


def breakpointhook(*argv, **kw):
    aio.paused = True


def shed_yield():
    # TODO: coroutine id as pid
    print("21", time_time() - aio.enter, aio.spent)
    return True


sys.breakpointhook = breakpointhook

this = __import__(__name__)

# those  __dunder__ are usually the same used in C conventions.

try:
    __UPY__
except:
    builtins.__UPY__ = this if hasattr(sys.implementation, "mpy") else None

if hasattr(sys, "_emscripten_info"):
    is_browser = not sys._emscripten_info.runtime.startswith("Node.js")
    builtins.__EMSCRIPTEN__ = this
    try:
        from embed import *
        from platform import *
        from embed_emscripten import *
        from embed_browser import window, document, navigator
        from embed_browser import Audio, File, Object
        from embed_browser import fetch, console, prompt, alert, confirm

        # pyodide compat
        sys.modules["js"] = sys.modules["embed_browser"]

        Object_type = type(Object())
    except Exception as e:
        sys.print_exception(e)
        pdb(__file__, ":47 no browser/emscripten modules yet", e)

    def ffi(arg):
        return window.JSON.parse(json.dumps(arg))

else:
    is_browser = False
    builtins.__EMSCRIPTEN__ = None


# force use a fixed, tested version of uasyncio to avoid non-determinism
if __UPY__:
    sys.modules["sys"] = sys
    sys.modules["builtins"] = builtins
    try:
        from . import uasyncio as uasyncio

        print("Warning : using WAPY uasyncio")
    except Exception as e:
        sys.print_exception(e)

else:
    try:
        from . import uasyncio_cpy as uasyncio
    except:
        pdb("INFO: no uasyncio implementation found")
        uasyncio = aio

sys.modules["uasyncio"] = uasyncio


def init_platform(embed):
    # simulator won't run javascript for now
    if not hasattr(embed, "run_script"):
        pdb("186: no js engine")
        return False

    import json

    def js(code, delay=0):
        # keep a ref till next loop
        aio.protect.append(code)
        if not delay:
            result = embed.run_script(f"JSON.stringify({code})")
            if result is not None:
                return json.loads(result)
        elif delay < 0:
            embed.run_script(code)
        else:
            embed.run_script(code, int(delay))

    embed.js = js

    if __WASM__:
        import _thread

        try:
            _thread.start_new_thread(lambda: None, ())
        except RuntimeError:
            pdb("WARNING: that wasm build does not support threads")


# ========================================== DOM EVENTS ===============

if is_browser:
    # implement "js.new"

    def new(oclass, *argv):
        from embed_browser import Reflect, Array

        return Reflect.construct(oclass, Array(*argv))

    # dom events
    class EventTarget:
        clients = {}
        events = []

        def addEventListener(self, host, type, listener, options=None, useCapture=None):
            cli = self.clients.setdefault(type, [])
            cli.append(listener)

        def build(self, evt_name, jsondata):
            self.events.append([evt_name, json.loads(jsondata)])

        # def dispatchEvent
        async def rpc(self, method, *argv):
            import inspect

            # TODO resolve whole path
            if hasattr(__import__("__main__"), method):
                client = getattr(__import__("__main__"), method)
                if is_coro := inspect.iscoroutinefunction(client):
                    await client(*argv)
                else:
                    client(*argv)
            else:
                print(f"RPC not found: {method}{argv}")

        async def process(self):
            import inspect
            from types import SimpleNamespace

            # notify event queue we are ready to process
            window.python.is_ready = 1

            while not aio.exit:
                if len(self.events):
                    evtype, evdata = self.events.pop(0)
                    if evtype == "rpc":
                        print("rpc.id", evdata.pop("rpcid"))
                        await self.rpc(evdata.pop("call"), *evdata.pop("argv"))
                        continue

                    discarded = True
                    for client in self.clients.get(evtype, []):
                        is_coro = inspect.iscoroutinefunction(client)
                        discarded = False
                        sns = SimpleNamespace(**evdata)
                        if is_coro:
                            await client(sns)
                        else:
                            client(sns)
                    if discarded:
                        console.log(f"221 DISCARD : {evtype} {evdata}")

                await aio.sleep(0)

    EventTarget = EventTarget()


# =============================  PRELOADING      ==============================

preld_counter = -1
prelist = {}
ROOTDIR = f"/data/data/{sys.argv[0]}/assets"


def explore(root):
    global prelist, preld_counter

    preld_counter = max(preld_counter, 0)
    import shutil

    for current, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".so"):
                preld_counter += 1
                src = f"{current}/{filename}"
                embed.preload(src)


def fix_preload_table():
    global prelist, preloadedWasm, preloadedImages, preloadedAudios

    if embed.counter() < 0:
        pdb("212: asset manager not ready 0>", embed.counter())
        aio.defer(fix_preload_table, (), {}, delay=60)

    for (
        src,
        dst,
    ) in prelist.items():
        ext = dst.rsplit(".", 1)[-1]
        if ext in preloadedImages:
            ptype = "preloadedImages"
        elif ext in preloadedAudios:
            ptype = "preloadedAudios"
        elif ext == "so":
            ptype = "preloadedWasm"

        src = f"{ptype}[{repr(src)}]"
        dst = f"{ptype}[{repr(dst)}]"
        swap = f"({src}={dst}) && delete {dst}"
        embed.js(swap, -1)
        # print(swap)


def run_main(PyConfig, loaderhome=None, loadermain="main.py"):
    global ROOTDIR
    global preloadedWasm, preloadedImages, preloadedAudios

    if loaderhome:
        pdb(f"241: appdir mapped to {loaderhome} by loader")
        ROOTDIR = str(loaderhome)

    # simulator won't run javascript for now
    if not hasattr(embed, "run_script"):
        pdb("246: no js engine")
        return False

    # do not do stuff if not called properly from our js loader.
    if PyConfig.executable is None:
        # running in sim
        pdb("252: running in simulator")
        return False

    sys.executable = PyConfig.executable or "python"

    preloadedWasm = "so"
    preloadedImages = "png jpeg jpg gif"
    preloadedAudios = "wav ogg mp4"

    def preload_apk(p=None):
        global preld_counter, prelist, ROOTDIR
        global explore, preloadedWasm, preloadedImages, preloadedAudios
        ROOTDIR = p or ROOTDIR
        if os.path.isdir(ROOTDIR):
            os.chdir(ROOTDIR)
        else:
            pdb(f"cannot chdir to {ROOTDIR=}")
            return

        ROOTDIR = os.getcwd()
        LSRC = len(ROOTDIR) + 1
        preld_counter = -1
        prelist = {}

        sys.path.insert(0, ROOTDIR)

        explore(ROOTDIR)

        if preld_counter < 0:
            pdb(f"{ROOTDIR=}")
            pdb(f"{os.getcwd()=}")

        print("284: assets found :", preld_counter)
        if not preld_counter:
            embed.run()

        return True

    import aio

    if PyConfig.interactive:
        import aio.clock

        aio.clock.start(x=80)

        # org.python REPL no preload !
        preload = sys.argv[0] != "org.python"
    else:
        # org.python script
        preload = True

    pdb(f"274: preload status {preload}")

    if preload and preload_apk():

        def fix_preload_table_apk():
            global fix_preload_table, ROOTDIR
            fix_preload_table()
            os.chdir(ROOTDIR)
            sys.path.insert(0, ROOTDIR)
            if loadermain:
                if os.path.isfile("main.py"):
                    print(f"315: running {ROOTDIR}/{loadermain} for {sys.argv[0]} (deferred)")
                    aio.defer(execfile, [f"{ROOTDIR}/{loadermain}"], {})
                else:
                    pdb(f"no {loadermain} found for {sys.argv[0]} in {ROOTDIR}")
                aio.defer(embed.prompt, (), {}, delay=2000)

    # C should unlock aio loop when preload count reach 0.

    else:

        def fix_preload_table_apk():
            global fix_preload_table_apk, ROOTDIR
            pdb("no assets preloaded")
            os.chdir(ROOTDIR)
            aio.defer(embed.prompt, (), {})

        # unlock embed looper because no preloading
        embed.run()

    aio.defer(fix_preload_table_apk, (), {}, delay=1000)

    if not aio.started:
        aio.started = True
        aio.create_task(EventTarget.process())
    else:
        print("341: EventTarget delayed by loader")


# ===============================================================================================
# platform


def rcp(source, destination):
    import urllib
    import urllib.request

    filename = Path(destination)
    filename.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(source_url, str(filename))
