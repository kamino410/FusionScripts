#Author-diomedea16
#Description-Draw wing.

import adsk.core, traceback
from os import path
import csv
import math

resources_dir = path.join(path.dirname(__file__), 'resources')

def run(context):
    ui = None
    try:
        #おまじない
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent
        sketches = rootComp.sketches

        #ペラのデータをロード
        data = get_setting_csv('setting.csv')
        foilCache = {}

        #回転軸対称に2枚描画
        for lr in [-1, 1]:
            sketch = sketches.add(rootComp.xZConstructionPlane)
            tops = adsk.core.ObjectCollection.create()
            ends = adsk.core.ObjectCollection.create()
            paths = []

            #リブを1枚ずつ検証
            for r in data:
                #翼型データのロード
                if r[5] in foilCache:
                    foil = foilCache[r[5]]
                else:
                    foil = get_2d_csv(r[5] + '.csv')
                    foilCache[r[5]] = foil

                #翼型をスケッチ
                points = adsk.core.ObjectCollection.create()
                for p, i in zip(foil[:-1], range(len(foil[:-1]))):
                    x = (p[0] - r[3]/100) * r[2]
                    y = - (p[1] - r[4]/100) * r[2]
                    rx = x * math.cos(math.radians(r[1])) - y * math.sin(math.radians(r[1]))
                    ry = x * math.sin(math.radians(r[1])) + y * math.cos(math.radians(r[1]))
                    node = adsk.core.Point3D.create(lr * rx, ry, lr * r[0])
                    points.add(node)
                    if i == 0:
                        ends.add(node)
                    elif p[0] == 0:
                        tops.add(node)
                spline = sketch.sketchCurves.sketchFittedSplines.add(points)
                spline.isClosed = True
                paths.append(rootComp.features.createPath(spline))

            #前縁・後縁の線を描画(ロフト時に型崩れしないようレールとして使う)
            topLine = sketch.sketchCurves.sketchFittedSplines.add(tops)
            endLine = sketch.sketchCurves.sketchFittedSplines.add(ends)

            #ロフト
            loftFeats = rootComp.features.loftFeatures
            loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            for pa in paths:
                loftInput.loftSections.add(pa)
            loftInput.isSolid = True
            loftInput.centerLineOrRails.addRail(rootComp.features.createPath(topLine))
            loftInput.centerLineOrRails.addRail(rootComp.features.createPath(endLine))
            loftFeats.add(loftInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

#設定csvの読み取り
def get_setting_csv(filename):
    with open(path.join(resources_dir, filename)) as f:
        return list(
            map(lambda r: [float(r[0]),
                            float(r[1]),
                            float(r[2]),
                            float(r[3]),
                            float(r[4]),
                            r[5]], csv.reader(f)))

#二次元座標を格納したcsvの読み取り
def get_2d_csv(filename):
	with open(path.join(resources_dir, filename)) as f:
		return list(
            map(lambda r: list(map(lambda c: float(c), r)), csv.reader(f)))
