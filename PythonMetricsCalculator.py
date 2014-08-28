import os, imp
import unittest
from __main__ import vtk, qt, ctk, slicer

#
# Python Metrics Calculator
#

class PythonMetricsCalculator:
  def __init__(self, parent):
    parent.title = "Python Metrics Calculator" # TODO make this more human readable by adding spaces
    parent.categories = ["Perk Tutor"]
    parent.dependencies = ["PerkEvaluator"]
    parent.contributors = ["Matthew Holden (Queen's University), Tamas Ungi (Queen's University)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    The Python Metric Calculator module is a hidden module for calculating metrics for transform buffers. For help on how to use this module visit: <a href='http://www.github.com/PerkTutor/PythonMetricsCalculator/wiki'>Python Metric Calculator</a>.
    """
    parent.acknowledgementText = """
    This work was was funded by Cancer Care Ontario and the Ontario Consortium for Adaptive Interventions in Radiation Oncology (OCAIRO).
    """ # replace with organization, grant and thanks.
    parent.icon = qt.QIcon( "PythonMetricsCalculator.png" )
    parent.hidden = True # TODO: Set to "True" when deploying module
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['PythonMetricsCalculator'] = self.runTest

  def runTest(self):
    tester = PythonMetricsCalculatorTest()
    tester.runTest()

#
# qPythonMetricsCalculatorWidget
#

class PythonMetricsCalculatorWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    # Comment these out when not debugging
    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "PythonMetricsCalculator Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)


  def cleanup(self):
    pass

  def onReload(self,moduleName="PythonMetricsCalculator"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

  def onReloadAndTest(self,moduleName="PythonMetricsCalculator"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# PythonMetricsCalculatorLogic
#

class PythonMetricsCalculatorLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__( self ):
    self.metrics = []
    # By default, grab the instantiated module's logic (though other logics are possible)
    self.SetPerkEvaluatorLogic( slicer.modules.perkevaluator.logic() )
    
  
  # We need this in order to determine the tissue model node, etc.  
  def SetPerkEvaluatorLogic( self, newPELogic ):
    self.peLogic = newPELogic  
      
      
  def AddAllUserMetrics( self ): 
    # Read the metric scripts 
    metricPath = self.peLogic.GetMetricsDirectory()    
    if ( metricPath == "" ):
      return
    
    allScripts = glob.glob( metricPath + "/*.py" )
  
    for j in range( len( allScripts ) ):
      currentMetricModule = imp.load_source( "PerkEvaluatorUserMetric" + str( j ), allScripts[j] )
      self.metrics.append( currentMetricModule.PerkEvaluatorMetric() )
      
      
  def FilterTissueMetrics( self, inMetrics, currentTransform ):
    if ( self.peLogic.GetBodyModelNode() != None ):
      return inMetrics
      
    # Only output metrics not requiring tissue
    outMetrics = []
    for i in range( len( inMetrics ) ):
      if ( inMetrics[i].RequiresTissueNode() == False ):
        outMetrics.append( inMetrics[i] )
        
    return outMetrics
        
        
  def FilterNeedleMetrics( self, inMetrics, currentTransform ):
    if ( self.peLogic.GetNeedleTransformNode() != None and currentTransform.GetName() == self.peLogic.GetNeedleTransformNode().GetName() ):
      return inMetrics
      
    # Only output metrics not requiring needle
    outMetrics = []
    for i in range( len( inMetrics ) ):
      if ( inMetrics[i].RequiresNeedle() == False ):
        outMetrics.append( inMetrics[i] )
        
    return outMetrics


  def CalculateAllMetrics( self ):  
    # Initialize all the metrics    
    import PythonMetrics
    self.metrics = PythonMetrics.PerkTutorCoreMetrics
    self.AddAllUserMetrics()
    
    # Initialize the metrics output
    metricStringList = []
      
    # Exit if there are no metrics (e.g. no metrics directory was specified)
    if ( len( self.metrics ) == 0 ):
      return metricStringList

    # Now iterate over all of the trajectories
    toolTransforms = vtk.vtkCollection()
    self.peLogic.GetAnalyzeTransforms( toolTransforms )
  
    for i in range( toolTransforms.GetNumberOfItems() ):

      currentTransform = toolTransforms.GetItemAsObject( i )
    
      #Drop if based on tissue and needle as appropriate
      transformMetrics = self.FilterTissueMetrics( self.metrics, currentTransform )
      transformMetrics = self.FilterNeedleMetrics( transformMetrics, currentTransform )
  
      # Initialization
      for j in range( len( transformMetrics ) ):
        transformMetrics[j].Initialize( self.peLogic.GetBodyModelNode() )
      
      # Calculation
      self.CalculateTransformMetric( currentTransform, transformMetrics )
    
      # Get the metrics
      for j in range( len( transformMetrics ) ):
        transformMetrics[j].Finalize()
        metricStringList.append( currentTransform.GetName() + " " + transformMetrics[j].GetMetricName() + " (" + str( transformMetrics[j].GetMetricUnit() ) + ")" )
        metricStringList.append( str( transformMetrics[j].GetMetric() ) )  
  
    return metricStringList
  
  

  def CalculateTransformMetric( self, currentTransform, transformMetrics ):
    # Initialize the origin, previous point, current point
    origin = [ 0, 0, 0, 1 ]
    point = [ 0, 0, 0, 1 ]
    # We will calculate the point here, since it is important, otherwise, the metrics are on their own
    
    # Start at the beginning (but remember where we were)
    originalPlaybackTime = self.peLogic.GetPlaybackTime()
    self.peLogic.SetPlaybackTime( self.peLogic.GetMinTime() )
    
    # Get the node associated with the trajectory we are interested in
    transformName = currentTransform.GetName()
    node = self.peLogic.GetMRMLScene().GetFirstNodeByName( transformName )
    
    # Get the self and parent transform buffer
    selfAndParentBuffer = self.peLogic.GetSelfAndParentTransformBuffer( node )
    
    # Initialize the matrices
    matrix = vtk.vtkMatrix4x4()
    
    # Now iterate
    for i in range( selfAndParentBuffer.GetNumTransforms() ):
      
      time = selfAndParentBuffer.GetTransformAt(i).GetTime()
      
      self.peLogic.SetPlaybackTime( time )
      
      matrix.Identity()
      currentTransform.GetMatrixTransformToWorld( matrix )
      
      if ( time < self.peLogic.GetMarkBegin() or time > self.peLogic.GetMarkEnd() ):
        continue
      
      matrix.MultiplyPoint( origin, point )
      
      for j in range( len( transformMetrics ) ):
        transformMetrics[j].AddTimestamp( time, matrix, point )
    
    self.peLogic.SetPlaybackTime( originalPlaybackTime )    




    


class PythonMetricsCalculatorTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear( 0 )

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    
    try:
      self.test_PythonMetricsCalculatorLumbar()
    
    except Exception, e:
      self.delayDisplay( "Test caused exception!\n" + str(e) )

  def test_PythonMetricsCalculatorLumbar(self):
    
    # These are the IDs of the relevant nodes
    transformBufferID = "vtkMRMLTransformBufferNode1"
    tissueModelID = "vtkMRMLModelNode4"
    needleTransformID = "vtkMRMLLinearTransformNode4"
    
    # TODO: Does this work for all OS?
    sceneFile = os.path.dirname( os.path.abspath( __file__ ) ) + "/Data/Scenes/Lumbar/TransformBuffer_Lumbar_Scene.mrml"
    resultsFile = os.path.dirname( os.path.abspath( __file__ ) ) + "/Data/Results/Lumbar.xml"
    
    #print sceneFile
    #print resultsFile
    
    # Load the scene
    activeScene = slicer.mrmlScene
    activeScene.Clear( 0 )
    activeScene.SetURL( sceneFile )
    if ( activeScene.Import() != 1 ):
      raise Exception( "Scene import failed. Scene file:" + sceneFile )   
    
    
    transformBufferNode = activeScene.GetNodeByID( transformBufferID )
    if ( transformBufferNode == None ):
      raise Exception( "Bad transform buffer." )
      
    tissueModelNode = activeScene.GetNodeByID( tissueModelID )
    if ( tissueModelNode == None ):
      raise Exception( "Bad tissue model." )
      
    needleTransformNode = activeScene.GetNodeByID( needleTransformID )
    if ( needleTransformNode == None ):
      raise Exception( "Bad needle transform." )
    
    # Parse the results xml file
    resultsParser = vtk.vtkXMLDataParser()
    resultsParser.SetFileName( resultsFile )
    resultsParser.Parse()
    rootElement = resultsParser.GetRootElement()
    if ( rootElement == None or rootElement.GetName() != "PythonMetricsResults" ):
      raise Exception( "Reading results failed. Results file:" + resultsFile )   
    
    # Create a dictionary to store results
    metricsDict = dict()
    
    for i in range( rootElement.GetNumberOfNestedElements() ):
      element = rootElement.GetNestedElement( i )
      if ( element == None or element.GetName() != "Metric" ):
        continue
      metricsDict[ element.GetAttribute( "Name" ) ] = float( element.GetAttribute( "Value" ) )
    
    # Setup the analysis
    peLogic = slicer.modules.perkevaluator.logic()
    
    peLogic.UpdateToolTrajectories( transformBufferNode )
    peLogic.SetPlaybackTime( peLogic.GetMinTime() )
    peLogic.AddAnalyzeTransform( needleTransformNode )
    
    peLogic.SetBodyModelNode( tissueModelNode )
    peLogic.SetNeedleTransformNode( needleTransformNode )
    
    peLogic.SetMarkBegin( peLogic.GetMinTime() )
    peLogic.SetMarkEnd( peLogic.GetMaxTime() )
    
    # Calculate the metrics
    pmcLogic = PythonMetricsCalculatorLogic()
    metricStringList = pmcLogic.CalculateAllMetrics()
    if ( len( metricStringList ) == 0 ):
      raise Exception( "No metrics were calculated." )
    if ( len( metricStringList ) % 2 != 0 ):
      raise Exception( "Metric calculation produced an unexpected result." ) 
    
    # Compare the metrics to the expected results
    metricIndex = 0
    metricsFail = False
    precision = 2
    
    while ( metricIndex < len( metricStringList ) ):
      metricName = metricStringList[ metricIndex ]
      metricValue = float( metricStringList[ metricIndex + 1 ] )
      
      if ( metricName not in metricsDict ):
        print "Could not find expected result for metric:", metricName, ". Value:", metricValue, "."
      else:
        if ( round( metricValue, precision ) != round( metricsDict[ metricName ], precision ) ):
          print "Incorrect metric:", metricName, ". Expected:", metricsDict[ metricName ], "but got", metricValue, "!"
          metricsFail = True
        else:
          print "Correct! Metric:", metricName, ". Expected:", metricsDict[ metricName ], "and got", metricValue, "!"
        
      metricIndex = metricIndex + 2
        
    if ( metricsFail == True ):
      self.delayDisplay( "Test failed! Calculated metrics were not consistent with results." )
    else:
      self.delayDisplay( "Test passed! Calculated metrics match results!" )