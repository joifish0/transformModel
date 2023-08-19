import logging
import os
from typing import Annotated, Optional
import functools
import numpy as np
import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# transformModel
#

class transformModel(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "transformModel"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation



class transformModelWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):


    def __init__(self, parent=None) -> None:

        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:

        ScriptedLoadableModuleWidget.setup(self)

        uiWidget = slicer.util.loadUI(self.resourcePath('UI/transformModel.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        uiWidget.setMRMLScene(slicer.mrmlScene)


        #self.ui.inputSelector.currentNodeChanged.connect(self.onMove)
        self.ui.Start.connect('clicked(bool)', self.onStart)
        self.ui.HardTransform.connect('clicked(bool)', self.onHardTransform)
        self.NodeList=[]


    def onStart(self):
        #将平面的变换矩阵赋值给模型
        def ApplyTransform(caller, event, TransFormID):
            #首先将模型至原点的变化矩阵求出来
            matrixOfModel=np.array([[1, 0, 0, -center[0]],
                                    [0, 1, 0, -center[1]],
                                    [0, 0, 1, -center[2]],
                                    [0, 0, 0, 1]])
            transNode=slicer.util.getNode(TransFormID)
            #获取平面的变换矩阵
            transNodeMatrix=vtk.vtkMatrix4x4()
            caller.GetObjectToWorldMatrix(transNodeMatrix)
            transNodeMatrixArray=slicer.util.arrayFromVTKMatrix(transNodeMatrix)
            #将模型变换至原点，再赋予平面的变换矩阵
            outMatrixArray=np.dot(transNodeMatrixArray,matrixOfModel)
            matrix_new=slicer.util.vtkMatrixFromArray(outMatrixArray)
            transNode.SetMatrixTransformToParent(matrix_new)

        model=self.ui.inputSelector.currentNode()
        #获取模型中心点，作为旋转中心
        bounds=[0,0,0,0,0,0]
        model.GetBounds(bounds)
        center=[(bounds[0]+bounds[1])/2,(bounds[2]+bounds[3])/2,(bounds[4]+bounds[5])/2]
        #将模型放在变换下
        TransForm=slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode')
        TransForm.SetName('PlaneUseForTransForm')
        model.SetAndObserveTransformNodeID(TransForm.GetID())
        #添加平面
        plane=slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsPlaneNode')
        plane.SetName('PlaneUseForTransForm')
        plane.AddControlPoint(center)
        plane.SetSize(0,0)
        plane.SetSize(1,0)
        plane.GetDisplayNode().SetGlyphScale(0)
        plane.GetDisplayNode().SetGlyphSize(0)
        plane.GetDisplayNode().RotationHandleVisibilityOn()
        plane.GetDisplayNode().TranslationHandleVisibilityOn()
        plane.GetDisplayNode().SetTextScale(0)

        #添加观察者，将平面的变换矩阵赋值给模型
        observer_func = functools.partial(ApplyTransform, TransFormID=TransForm.GetID())
        plane.AddObserver(vtk.vtkCommand.ModifiedEvent, observer_func)
        self.NodeList.append([model,TransForm,plane])
    
    def onHardTransform(self):
        model=self.ui.inputSelector.currentNode()
        model.HardenTransform()
        for i in range(len(self.NodeList)):
            if model in self.NodeList[i]:
                slicer.mrmlScene.RemoveNode(self.NodeList[i][1])
                slicer.mrmlScene.RemoveNode(self.NodeList[i][2])
                del self.NodeList[i]
                break




