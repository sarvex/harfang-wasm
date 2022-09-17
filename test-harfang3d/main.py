# src="http://localhost:8000/archives/0.4/pythons.js" data-src="fs,vtx,gui"

# src="https://pmp-p.github.io/harfang-wasm-wip/0.4/pythons.js" data-src="fs,vtx,gui"

import sys
import platform
import asyncio

#import pygame

import harfang as hg

hg.InputInit()
hg.WindowSystemInit()


res_x, res_y = 1024, 1024

# Draw models without a pipeline
async def main():
    await asyncio.sleep(1)
    print("===================================")
    win = hg.RenderInit('Harfang - Draw Models no Pipeline', res_x, res_y, hg.RT_OpenGLES)
    print("===================================")

    if 1:
        # vertex layout and models
        vtx_layout = hg.VertexLayoutPosFloatNormUInt8()

        cube_mdl = hg.CreateCubeModel(vtx_layout, 1, 1, 1)
        ground_mdl = hg.CreatePlaneModel(vtx_layout, 5, 5, 1, 1)

        shader = hg.LoadProgramFromFile('resources_compiled/shaders/mdl')

        # main loop
        angle = 0

        while 1: #not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(win):
            dt = hg.TickClock()
            angle = angle + hg.time_to_sec_f(dt)

            viewpoint = hg.TranslationMat4(hg.Vec3(0, 1, -3))
            hg.SetViewPerspective(0, 0, 0, res_x, res_y, viewpoint)

            hg.DrawModel(0, cube_mdl, shader, [], [], hg.TransformationMat4(hg.Vec3(0, 1, 0), hg.Vec3(angle, angle, angle)))
            hg.DrawModel(0, ground_mdl, shader, [], [], hg.TranslationMat4(hg.Vec3(0, 0, 0)))

            hg.Frame()
            hg.UpdateWindow(win)
            await asyncio.sleep(0)


        hg.RenderShutdown()

asyncio.run(main())


