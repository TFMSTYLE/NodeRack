# SPDX-FileCopyrightText: 2025-2026 The French Monkey
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "NodeRack",
    "author": "The French Monkey",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "Node Editor > N-Panel > NodeRack",
    "description": "Advanced node browser with live search, colored categories, and custom node storage",
    "category": "Node",
    "license": "GPL-3.0-or-later",
}

import bpy
import json
import os
from bpy.types import Operator, Panel, PropertyGroup, Menu
from bpy.props import StringProperty, BoolProperty, CollectionProperty, PointerProperty, IntProperty

# --------------------------------------------------------------------------
# CATEGORY COLORS
# --------------------------------------------------------------------------

_node_color_cache = {}

def get_node_category_color(node_tree_type, category_name):
    cache_key = (node_tree_type, category_name)
    if cache_key in _node_color_cache:
        return _node_color_cache[cache_key]

    color = get_manual_color(node_tree_type, category_name)
    _node_color_cache[cache_key] = color
    return color

def get_manual_color(node_tree_type, category_name):
    name = category_name.lower()

    # Shader node colors
    if node_tree_type == "ShaderNodeTree":
        shader_colors = {
            "input": (0.608, 0.153, 0.231, 1.0),
            "output": (0.780, 0.290, 0.505, 1.0),
            "shader": (0.204, 0.459, 0.216, 1.0),
            "texture": (0.502, 0.243, 0.071, 1.0),
            "color": (0.502, 0.502, 0.161, 1.0),
            "vector": (0.188, 0.188, 0.447, 1.0),
            "converter": (0.200, 0.365, 0.592, 1.0),
            "script": (0.200, 0.400, 0.400, 1.0),
            "group": (0.200, 0.200, 0.200, 1.0),
            "layout": (0.400, 0.400, 0.400, 1.0),
        }
        for key, color in shader_colors.items():
            if key in name:
                return color

    # Geometry node colors
    if node_tree_type == "GeometryNodeTree":
        geo_colors = {
            "input": (0.608, 0.153, 0.231, 1.0),
            "output": (0.129, 0.129, 0.129, 1.0),
            "geometry": (0.204, 0.459, 0.216, 1.0),
            "topology": (0.608, 0.153, 0.231, 1.0),
            "mesh": (0.204, 0.459, 0.216, 1.0),
            "mesh topology": (0.608, 0.153, 0.231, 1.0),
            "mesh primitives": (0.243, 0.376, 0.659, 1.0),
            "curve": (0.204, 0.459, 0.216, 1.0),
            "curve topology": (0.608, 0.153, 0.231, 1.0),
            "curve primitives": (0.439, 0.169, 0.341, 1.0),
            "point": (0.204, 0.459, 0.216, 1.0),
            "instances": (0.204, 0.459, 0.216, 1.0),
            "material": (0.204, 0.459, 0.216, 1.0),
            "texture": (0.502, 0.243, 0.071, 1.0),
            "attribute": (0.200, 0.365, 0.592, 1.0),
            "utilities": (0.200, 0.365, 0.592, 1.0),
            "simulation": (0.200, 0.200, 0.200, 1.0),
            "volume": (0.204, 0.459, 0.216, 1.0),
            "group": (0.200, 0.200, 0.200, 1.0),
            "layout": (0.400, 0.400, 0.400, 1.0),
            "color": (0.200, 0.365, 0.592, 1.0),
        }
        for key, color in geo_colors.items():
            if key in name:
                return color

    # Compositor node colors
    if node_tree_type == "CompositorNodeTree":
        comp_colors = {
            "input": (0.608, 0.153, 0.231, 1.0),
            "output": (0.356, 0.243, 0.486, 1.0),
            "color": (0.502, 0.502, 0.161, 1.0),
            "converter": (0.200, 0.365, 0.592, 1.0),
            "filter": (0.290, 0.300, 0.580, 1.0),
            "matte": (0.353, 0.262, 0.262, 1.0),
            "vector": (0.188, 0.188, 0.447, 1.0),
            "distort": (0.168, 0.333, 0.329, 1.0),
            "group": (0.200, 0.200, 0.200, 1.0),
            "layout": (0.400, 0.400, 0.400, 1.0),
        }
        for key, color in comp_colors.items():
            if key in name:
                return color

    # default if nothing matched
    return (0.5, 0.5, 0.5, 1.0)

# --------------------------------------------------------------------------
# NODE CATALOG
# --------------------------------------------------------------------------

NODE_CATALOG = {
    "ShaderNodeTree": {
        "Input": [
            ("Ambient Occlusion", "ShaderNodeAmbientOcclusion", "Ambient occlusion factor at shading point"),
            ("Attribute", "ShaderNodeAttribute", "Read attributes from geometry"),
            ("Bevel", "ShaderNodeBevel", "Rounded edge information for shading"),
            ("Camera Data", "ShaderNodeCameraData", "View vector and distance from camera"),
            ("Color Attribute", "ShaderNodeVertexColor", "Access vertex color attributes"),
            ("Fresnel", "ShaderNodeFresnel", "Fresnel reflection factor based on IOR"),
            ("Geometry", "ShaderNodeNewGeometry", "Geometric properties of surface"),
            ("Hair Info", "ShaderNodeHairInfo", "Hair strand information for hair rendering"),
            ("Layer Weight", "ShaderNodeLayerWeight", "Blend weights for layers based on angle"),
            ("Light Path", "ShaderNodeLightPath", "Light ray type information"),
            ("Object Info", "ShaderNodeObjectInfo", "Object data like location and index"),
            ("Particle Info", "ShaderNodeParticleInfo", "Particle system properties"),
            ("Point Info", "ShaderNodePointInfo", "Point cloud point information"),
            ("RGB", "ShaderNodeRGB", "RGB color constant"),
            ("Tangent", "ShaderNodeTangent", "Tangent direction for anisotropic shading"),
            ("Texture Coordinate", "ShaderNodeTexCoord", "Texture coordinate systems"),
            ("Uvmap", "ShaderNodeUVMap", "Named UV map coordinates"),
            ("Value", "ShaderNodeValue", "Scalar value constant"),
            ("Volume Info", "ShaderNodeVolumeInfo", "Volume grid information"),
            ("Wireframe", "ShaderNodeWireframe", "Wireframe rendering factor"),
        ],
        "Output": [
            ("AOV Output", "ShaderNodeOutputAOV", "Custom render pass output"),
            ("Light Output", "ShaderNodeOutputLight", "Light shader output"),
            ("Material Output", "ShaderNodeOutputMaterial", "Surface shader output"),
            ("World Output", "ShaderNodeOutputWorld", "World shader output"),
        ],
        "Shader": [
            ("Add Shader", "ShaderNodeAddShader", "Add two shader closures"),
            ("Anisotropic BSDF", "ShaderNodeBsdfAnisotropic", "Anisotropic reflection shader"),
            ("Background", "ShaderNodeBackground", "Background shader for world"),
            ("Diffuse BSDF", "ShaderNodeBsdfDiffuse", "Lambertian diffuse reflection"),
            ("Emission", "ShaderNodeEmission", "Light emitting surface shader"),
            ("Glass BSDF", "ShaderNodeBsdfGlass", "Glass-like refraction and reflection"),
            ("Glossy BSDF", "ShaderNodeBsdfGlossy", "Glossy specular reflection"),
            ("Hair BSDF", "ShaderNodeBsdfHair", "Hair shading model"),
            ("Holdout", "ShaderNodeHoldout", "Render transparent placeholder"),
            ("Metallic BSDF", "ShaderNodeBsdfMetallic", "Metallic reflection shader"),
            ("Mix Shader", "ShaderNodeMixShader", "Mix two shader closures"),
            ("Principled BSDF", "ShaderNodeBsdfPrincipled", "Physically based uber shader"),
            ("Principled Hair BSDF", "ShaderNodeBsdfHairPrincipled", "Principled hair shading model"),
            ("Principled Volume", "ShaderNodeVolumePrincipled", "Principled volume shader"),
            ("Ray Portal BSDF", "ShaderNodeBsdfRayPortal", "Portal for ray tracing optimization"),
            ("Refraction BSDF", "ShaderNodeBsdfRefraction", "Refraction without reflection"),
            ("Sheen BSDF", "ShaderNodeBsdfSheen", "Fabric-like sheen reflection"),
            ("Specular BSDF", "ShaderNodeEeveeSpecular", "EEVEE specular shader"),
            ("Subsurface Scattering", "ShaderNodeSubsurfaceScattering", "Subsurface light transport"),
            ("Toon BSDF", "ShaderNodeBsdfToon", "Non-photorealistic toon shading"),
            ("Translucent BSDF", "ShaderNodeBsdfTranslucent", "Diffuse transmission"),
            ("Transparent BSDF", "ShaderNodeBsdfTransparent", "Fully transparent shader"),
            ("Volume Absorption", "ShaderNodeVolumeAbsorption", "Light absorption in volumes"),
            ("Volume Scatter", "ShaderNodeVolumeScatter", "Light scattering in volumes"),
        ],
        "Texture": [
            ("Brick Texture", "ShaderNodeTexBrick", "Procedural brick pattern"),
            ("Checker Texture", "ShaderNodeTexChecker", "Checkerboard pattern"),
            ("Environment Texture", "ShaderNodeTexEnvironment", "Environment map for lighting"),
            ("Gabor Texture", "ShaderNodeTexGabor", "Procedural Gabor noise pattern"),
            ("Gradient Texture", "ShaderNodeTexGradient", "Gradient ramp pattern"),
            ("IES Texture", "ShaderNodeTexIES", "IES light profile texture"),
            ("Image Texture", "ShaderNodeTexImage", "Sample image as texture"),
            ("Magic Texture", "ShaderNodeTexMagic", "Psychedelic noise pattern"),
            ("Noise Texture", "ShaderNodeTexNoise", "Perlin-style noise texture"),
            ("Point Density", "ShaderNodeTexPointDensity", "Particle or vertex density texture"),
            ("Sky Texture", "ShaderNodeTexSky", "Physically-based sky texture"),
            ("Voronoi Texture", "ShaderNodeTexVoronoi", "Voronoi cell noise texture"),
            ("Wave Texture", "ShaderNodeTexWave", "Wave-based procedural texture"),
            ("White Noise Texture", "ShaderNodeTexWhiteNoise", "Random white noise"),
        ],
        "Color": [
            ("Bright/Contrast", "ShaderNodeBrightContrast", "Adjust brightness and contrast"),
            ("Gamma", "ShaderNodeGamma", "Apply gamma correction"),
            ("Hue/Saturation/Value", "ShaderNodeHueSaturation", "Adjust HSV color values"),
            ("Invert Color", "ShaderNodeInvert", "Invert color channels"),
            ("Light Falloff", "ShaderNodeLightFalloff", "Light intensity falloff curves"),
            ("Mix Color", "ShaderNodeMixRGB", "Mix two colors with blend modes"),
            ("RGB Curves", "ShaderNodeRGBCurve", "Color curves adjustment"),
        ],
        "Vector": [
            ("Bump", "ShaderNodeBump", "Generate normals from height"),
            ("Displacement", "ShaderNodeDisplacement", "Displace surface geometry"),
            ("Mapping", "ShaderNodeMapping", "Transform texture coordinates"),
            ("Normal", "ShaderNodeNormal", "Set surface normal direction"),
            ("Normal Map", "ShaderNodeNormalMap", "Apply tangent-space normal map"),
            ("Vector Curves", "ShaderNodeVectorCurve", "Vector component curves"),
            ("Vector Displacement", "ShaderNodeVectorDisplacement", "Vector-based displacement"),
            ("Vector Rotate", "ShaderNodeVectorRotate", "Rotate vector around axis"),
            ("Vector Transform", "ShaderNodeVectorTransform", "Transform vector between spaces"),
        ],
        "Converter": [
            ("Blackbody", "ShaderNodeBlackbody", "Blackbody emission color"),
            ("Clamp", "ShaderNodeClamp", "Clamp value to range"),
            ("Color Ramp", "ShaderNodeValToRGB", "Map value to color gradient"),
            ("Combine Color", "ShaderNodeCombineColor", "Combine color channels"),
            ("Combine XYZ", "ShaderNodeCombineXYZ", "Combine vector components"),
            ("Float Curve", "ShaderNodeFloatCurve", "Curve mapping for float values"),
            ("Map Range", "ShaderNodeMapRange", "Remap value range"),
            ("Math", "ShaderNodeMath", "Mathematical operations"),
            ("Mix", "ShaderNodeMix", "Mix values with factor"),
            ("RGB to BW", "ShaderNodeRGBToBW", "Convert color to grayscale"),
            ("Separate Color", "ShaderNodeSeparateColor", "Separate color channels"),
            ("Separate XYZ", "ShaderNodeSeparateXYZ", "Separate vector components"),
            ("Shader to RGB", "ShaderNodeShaderToRGB", "Convert shader to RGB color"),
            ("Vector Math", "ShaderNodeVectorMath", "Vector mathematical operations"),
            ("Wavelength", "ShaderNodeWavelength", "Convert wavelength to RGB"),
        ],
        "Script": [
            ("Script", "ShaderNodeScript", "OSL shader script node"),
        ],
        "Group": [
            ("Group Input", "NodeGroupInput", "Node group input sockets"),
            ("Group Output", "NodeGroupOutput", "Node group output sockets"),
        ],
        "Layout": [
            ("Frame", "NodeFrame", "Group nodes visually with frame"),
            ("Reroute", "NodeReroute", "Redirect node connections"),
        ],
    },
    
    "GeometryNodeTree": {
        "Input": [
            ("Active Camera", "GeometryNodeInputActiveCamera", "Active camera object"),
            ("Collection Info", "GeometryNodeCollectionInfo", "Collection geometry data"),
            ("Curve Handle Positions", "GeometryNodeInputCurveHandlePositions", "Bezier handle positions"),
            ("Curve Length", "GeometryNodeCurveLength", "Total curve spline length"),
            ("Curve Tilt", "GeometryNodeInputCurveTilt", "Curve point tilt angle"),
            ("Edge Angle", "GeometryNodeInputMeshEdgeAngle", "Angle between faces"),
            ("Edge Neighbors", "GeometryNodeInputMeshEdgeNeighbors", "Connected face count"),
            ("Edge Vertices", "GeometryNodeInputMeshEdgeVertices", "Vertex indices of edge"),
            ("Face Area", "GeometryNodeInputMeshFaceArea", "Face surface area"),
            ("Face Neighbors", "GeometryNodeInputMeshFaceNeighbors", "Adjacent face/vertex/edge count"),
            ("ID", "GeometryNodeInputID", "Stable unique element ID"),
            ("Image", "GeometryNodeInputImage", "Image datablock input"),
            ("Image Info", "GeometryNodeImageInfo", "Image properties like size"),
            ("Index", "GeometryNodeInputIndex", "Element index in list"),
            ("Instance Rotation", "GeometryNodeInputInstanceRotation", "Instance rotation value"),
            ("Instance Scale", "GeometryNodeInputInstanceScale", "Instance scale value"),
            ("Is Viewport", "GeometryNodeIsViewport", "Check if rendering viewport"),
            ("Island", "GeometryNodeInputMeshIsland", "Connected mesh component ID"),
            ("Material", "GeometryNodeInputMaterial", "Material datablock input"),
            ("Mesh Island", "GeometryNodeInputMeshIsland", "Mesh island index"),
            ("Named Attribute", "GeometryNodeInputNamedAttribute", "Get attribute by name"),
            ("Named Layer Selection", "GeometryNodeInputNamedLayerSelection", "Layer selection by name"),
            ("Normal", "GeometryNodeInputNormal", "Surface normal vector"),
            ("Object Info", "GeometryNodeObjectInfo", "Object transformation data"),
            ("Position", "GeometryNodeInputPosition", "Element position vector"),
            ("Radius", "GeometryNodeInputRadius", "Point/curve radius value"),
            ("Scene Time", "GeometryNodeInputSceneTime", "Current scene frame/time"),
            ("Self Object", "GeometryNodeSelfObject", "Current evaluated object"),
            ("Shortest Edge Paths", "GeometryNodeInputShortestEdgePaths", "Shortest path between vertices"),
            ("Spline Cyclic", "GeometryNodeInputSplineCyclic", "Spline closed loop status"),
            ("Spline Length", "GeometryNodeSplineLength", "Individual spline length"),
            ("Spline Parameter", "GeometryNodeSplineParameter", "Normalized position on spline"),
            ("Spline Resolution", "GeometryNodeInputSplineResolution", "Curve evaluation resolution"),
            ("String", "FunctionNodeInputString", "String value input"),
            ("Value", "ShaderNodeValue", "Float value input"),
            ("Vertex Neighbors", "GeometryNodeInputMeshVertexNeighbors", "Connected edge/face count"),
        ],
        "Output": [
            ("Group Output", "NodeGroupOutput", "Node group output sockets"),
            ("Viewer", "GeometryNodeViewer", "Preview geometry in viewer"),
        ],
        "Geometry": [
            ("Bake", "GeometryNodeBake", "Store simulation results"),
            ("Bounding Box", "GeometryNodeBoundBox", "Geometry bounding box"),
            ("Convex Hull", "GeometryNodeConvexHull", "Convex hull of geometry"),
            ("Delete Geometry", "GeometryNodeDeleteGeometry", "Remove geometry elements"),
            ("Duplicate Elements", "GeometryNodeDuplicateElements", "Duplicate selected elements"),
            ("Geometry Proximity", "GeometryNodeProximity", "Closest point on geometry"),
            ("Geometry to Instance", "GeometryNodeGeometryToInstance", "Convert geometry to instance"),
            ("Join Geometry", "GeometryNodeJoinGeometry", "Combine multiple geometries"),
            ("Merge by Distance", "GeometryNodeMergeByDistance", "Merge nearby vertices"),
            ("Raycast", "GeometryNodeRaycast", "Cast ray onto geometry"),
            ("Sample Index", "GeometryNodeSampleIndex", "Sample attribute at index"),
            ("Sample Nearest", "GeometryNodeSampleNearest", "Sample nearest element"),
            ("Separate Components", "GeometryNodeSeparateComponents", "Split geometry by type"),
            ("Separate Geometry", "GeometryNodeSeparateGeometry", "Split by selection"),
            ("Set ID", "GeometryNodeSetID", "Assign element IDs"),
            ("Set Position", "GeometryNodeSetPosition", "Move element positions"),
            ("Transform Geometry", "GeometryNodeTransform", "Transform entire geometry"),
        ],
        "Curve": [
            ("Curve Length", "GeometryNodeCurveLength", "Total length of curves"),
            ("Curve to Mesh", "GeometryNodeCurveToMesh", "Convert curve to mesh"),
            ("Curve to Points", "GeometryNodeCurveToPoints", "Sample points on curves"),
            ("Deform Curves on Surface", "GeometryNodeDeformCurvesOnSurface", "Deform curves along surface"),
            ("Fill Curve", "GeometryNodeFillCurve", "Fill closed curves with faces"),
            ("Fillet Curve", "GeometryNodeFilletCurve", "Round curve corners"),
            ("Interpolate Curves", "GeometryNodeInterpolateCurves", "Blend between curve shapes"),
            ("Resample Curve", "GeometryNodeResampleCurve", "Resample curve points"),
            ("Reverse Curve", "GeometryNodeReverseCurve", "Reverse curve direction"),
            ("Sample Curve", "GeometryNodeSampleCurve", "Sample curve at parameter"),
            ("Set Curve Normal", "GeometryNodeSetCurveNormal", "Set curve normal direction"),
            ("Set Curve Radius", "GeometryNodeSetCurveRadius", "Set curve point radius"),
            ("Set Curve Tilt", "GeometryNodeSetCurveTilt", "Set curve tilt angle"),
            ("Set Handle Positions", "GeometryNodeSetCurveHandlePositions", "Set bezier handle positions"),
            ("Set Handle Type", "GeometryNodeCurveSetHandles", "Set bezier handle types"),
            ("Set Spline Cyclic", "GeometryNodeSetSplineCyclic", "Make spline cyclic"),
            ("Set Spline Resolution", "GeometryNodeSetSplineResolution", "Set spline resolution"),
            ("Set Spline Type", "GeometryNodeCurveSplineType", "Convert spline type"),
            ("Subdivide Curve", "GeometryNodeSubdivideCurve", "Add points to curves"),
            ("Trim Curve", "GeometryNodeTrimCurve", "Cut curve at positions"),
        ],
        "Curve Primitives": [
            ("Arc", "GeometryNodeCurveArc", "Circular arc curve primitive"),
            ("Bezier Segment", "GeometryNodeCurvePrimitiveBezierSegment", "Single bezier curve segment"),
            ("Curve Circle", "GeometryNodeCurvePrimitiveCircle", "Circle curve primitive"),
            ("Curve Line", "GeometryNodeCurvePrimitiveLine", "Straight line curve"),
            ("Quadratic Bezier", "GeometryNodeCurveQuadraticBezier", "Quadratic bezier curve"),
            ("Quadrilateral", "GeometryNodeCurvePrimitiveQuadrilateral", "Four-point polygon curve"),
            ("Spiral", "GeometryNodeCurveSpiral", "Spiral curve primitive"),
            ("Star", "GeometryNodeCurveStar", "Star-shaped curve"),
        ],
        "Curve Topology": [
            ("Curve of Point", "GeometryNodeCurveOfPoint", "Curve containing point"),
            ("Offset Point in Curve", "GeometryNodeOffsetPointInCurve", "Offset point along curve"),
            ("Points of Curve", "GeometryNodePointsOfCurve", "Points in curve range"),
        ],
        "Instances": [
            ("Instance on Points", "GeometryNodeInstanceOnPoints", "Create instances at points"),
            ("Instances to Points", "GeometryNodeInstancesToPoints", "Convert instances to points"),
            ("Realize Instances", "GeometryNodeRealizeInstances", "Make instances real geometry"),
            ("Rotate Instances", "GeometryNodeRotateInstances", "Rotate instance transforms"),
            ("Scale Instances", "GeometryNodeScaleInstances", "Scale instance transforms"),
            ("Translate Instances", "GeometryNodeTranslateInstances", "Translate instance transforms"),
        ],
        "Mesh": [
            ("Dual Mesh", "GeometryNodeDualMesh", "Face-vertex dual mesh"),
            ("Edge Paths to Curves", "GeometryNodeEdgePathsToCurves", "Convert edge paths to curves"),
            ("Edge Paths to Selection", "GeometryNodeEdgePathsToSelection", "Select edge paths"),
            ("Extrude Mesh", "GeometryNodeExtrudeMesh", "Extrude mesh elements"),
            ("Flip Faces", "GeometryNodeFlipFaces", "Reverse face normals"),
            ("Mesh Boolean", "GeometryNodeMeshBoolean", "Boolean operations on meshes"),
            ("Mesh to Curve", "GeometryNodeMeshToCurve", "Convert mesh edges to curves"),
            ("Mesh to Density Grid", "GeometryNodeMeshToDensityGrid", "Convert mesh to volume density"),
            ("Mesh to Points", "GeometryNodeMeshToPoints", "Convert mesh to points"),
            ("Mesh to SDF Grid", "GeometryNodeMeshToSDFGrid", "Convert mesh to SDF volume"),
            ("Mesh to Volume", "GeometryNodeMeshToVolume", "Convert mesh to volume"),
            ("Points to SDF Grid", "GeometryNodePointsToSDFGrid", "Convert points to SDF grid"),
            ("Points to Vertices", "GeometryNodePointsToVertices", "Convert points to mesh vertices"),
            ("Scale Elements", "GeometryNodeScaleElements", "Scale mesh faces or edges"),
            ("Set Shade Smooth", "GeometryNodeSetShadeSmooth", "Set smooth/flat shading"),
            ("SDF Grid to Mesh", "GeometryNodeSDFVolumeTomesh", "Convert SDF volume to mesh"),
            ("Split Edges", "GeometryNodeSplitEdges", "Split edges into disconnected"),
            ("Subdivide Mesh", "GeometryNodeSubdivideMesh", "Subdivide mesh faces"),
            ("Subdivision Surface", "GeometryNodeSubdivisionSurface", "Catmull-Clark subdivision"),
            ("Triangulate", "GeometryNodeTriangulate", "Convert faces to triangles"),
        ],
        "Mesh Primitives": [
            ("Cone", "GeometryNodeMeshCone", "Cone mesh primitive"),
            ("Cube", "GeometryNodeMeshCube", "Cube mesh primitive"),
            ("Cylinder", "GeometryNodeMeshCylinder", "Cylinder mesh primitive"),
            ("Grid", "GeometryNodeMeshGrid", "Grid mesh primitive"),
            ("Ico Sphere", "GeometryNodeMeshIcoSphere", "Icosphere mesh primitive"),
            ("Mesh Circle", "GeometryNodeMeshCircle", "Circle mesh primitive"),
            ("Mesh Line", "GeometryNodeMeshLine", "Line mesh primitive"),
            ("UV Sphere", "GeometryNodeMeshUVSphere", "UV sphere mesh primitive"),
        ],
        "Mesh Topology": [
            ("Corners of Edge", "GeometryNodeCornersOfEdge", "Face corners of edge"),
            ("Corners of Face", "GeometryNodeCornersOfFace", "Face corner indices"),
            ("Corners of Vertex", "GeometryNodeCornersOfVertex", "Corners connected to vertex"),
            ("Edges of Corner", "GeometryNodeEdgesOfCorner", "Edges adjacent to corner"),
            ("Edges of Vertex", "GeometryNodeEdgesOfVertex", "Edges connected to vertex"),
            ("Face of Corner", "GeometryNodeFaceOfCorner", "Face containing corner"),
            ("Offset Corner in Face", "GeometryNodeOffsetCornerInFace", "Offset corner in face"),
            ("Vertex of Corner", "GeometryNodeVertexOfCorner", "Vertex at corner"),
        ],
        "Point": [
            ("Distribute Points in Grid", "GeometryNodeDistributePointsInGrid", "Regular grid of points"),
            ("Distribute Points in Volume", "GeometryNodeDistributePointsInVolume", "Scatter points in volume"),
            ("Distribute Points on Faces", "GeometryNodeDistributePointsOnFaces", "Scatter points on surfaces"),
            ("Points", "GeometryNodePoints", "Create point cloud"),
            ("Points to Volume", "GeometryNodePointsToVolume", "Convert points to volume"),
            ("Set Point Radius", "GeometryNodeSetPointRadius", "Set point cloud radius"),
        ],
        "Volume": [
            ("SDF Volume Sphere", "GeometryNodeVolumeCube", "SDF sphere volume primitive"),
            ("Volume Cube", "GeometryNodeVolumeCube", "Cube volume primitive"),
            ("Volume to Mesh", "GeometryNodeVolumeToMesh", "Convert volume to mesh"),
        ],
        "Material": [
            ("Replace Material", "GeometryNodeReplaceMaterial", "Replace material assignment"),
            ("Set Material", "GeometryNodeSetMaterial", "Assign material to geometry"),
            ("Set Material Index", "GeometryNodeSetMaterialIndex", "Set material slot index"),
        ],
        "Texture": [
            ("Brick Texture", "ShaderNodeTexBrick", "Procedural brick texture"),
            ("Checker Texture", "ShaderNodeTexChecker", "Checkerboard texture"),
            ("Gradient Texture", "ShaderNodeTexGradient", "Gradient texture"),
            ("Image Texture", "GeometryNodeImageTexture", "Sample image texture"),
            ("Magic Texture", "ShaderNodeTexMagic", "Magic noise texture"),
            ("Noise Texture", "ShaderNodeTexNoise", "Perlin noise texture"),
            ("Voronoi Texture", "ShaderNodeTexVoronoi", "Voronoi texture"),
            ("Wave Texture", "ShaderNodeTexWave", "Wave texture"),
            ("White Noise Texture", "ShaderNodeTexWhiteNoise", "White noise texture"),
        ],
        "Utilities": [
            ("Accumulate Field", "GeometryNodeAccumulateField", "Running total of field values"),
            ("Align Euler to Vector", "FunctionNodeAlignEulerToVector", "Align rotation to vector"),
            ("Axes to Rotation", "FunctionNodeAxesToRotation", "Rotation from axis vectors"),
            ("Blur Attribute", "GeometryNodeBlurAttribute", "Blur attribute values"),
            ("Boolean Math", "FunctionNodeBooleanMath", "Boolean logic operations"),
            ("Capture Attribute", "GeometryNodeCaptureAttribute", "Store field as attribute"),
            ("Clamp", "ShaderNodeClamp", "Clamp value to range"),
            ("Color Ramp", "ShaderNodeValToRGB", "Map value to color"),
            ("Compare", "FunctionNodeCompare", "Compare two values"),
            ("Evaluate at Index", "GeometryNodeFieldAtIndex", "Get field value at index"),
            ("Evaluate on Domain", "GeometryNodeFieldOnDomain", "Evaluate field on domain"),
            ("Float to Integer", "FunctionNodeFloatToInt", "Convert float to integer"),
            ("Hash Value", "FunctionNodeHashValue", "Generate hash from value"),
            ("Index Switch", "GeometryNodeIndexSwitch", "Switch value by index"),
            ("Integer", "FunctionNodeInputInt", "Integer value input"),
            ("Map Range", "ShaderNodeMapRange", "Remap value range"),
            ("Math", "ShaderNodeMath", "Math operations"),
            ("Matrix Determinant", "FunctionNodeMatrixDeterminant", "Matrix determinant value"),
            ("Matrix Invert", "FunctionNodeMatrixInvert", "Invert matrix"),
            ("Matrix Multiply", "FunctionNodeMatrixMultiply", "Multiply matrices"),
            ("Matrix Transpose", "FunctionNodeMatrixTranspose", "Transpose matrix"),
            ("Menu Switch", "GeometryNodeMenuSwitch", "Switch between menu options"),
            ("Mix", "ShaderNodeMix", "Mix values with factor"),
            ("Quaternion to Rotation", "FunctionNodeQuaternionToRotation", "Convert quaternion to rotation"),
            ("Random Value", "FunctionNodeRandomValue", "Generate random values"),
            ("Remove Named Attribute", "GeometryNodeRemoveAttribute", "Delete named attribute"),
            ("Repeat Zone", "ZONE:GeometryNodeRepeatInput", "Repeat operations N times (adds input and output)"),
            ("Rotation to Axis Angle", "FunctionNodeRotationToAxisAngle", "Convert rotation to axis-angle"),
            ("Rotation to Euler", "FunctionNodeRotationToEuler", "Convert rotation to euler"),
            ("Rotation to Quaternion", "FunctionNodeRotationToQuaternion", "Convert rotation to quaternion"),
            ("Rotate Euler", "FunctionNodeRotateEuler", "Rotate euler angles"),
            ("Rotate Vector", "ShaderNodeVectorRotate", "Rotate vector around axis"),
            ("Sample Grid", "GeometryNodeSampleGrid", "Sample volume grid"),
            ("Sample Grid Index", "GeometryNodeSampleGridIndex", "Sample volume at index"),
            ("Sample Image", "GeometryNodeSampleImage", "Sample image at coordinates"),
            ("Sample Nearest Surface", "GeometryNodeSampleNearestSurface", "Sample nearest point on surface"),
            ("Sample UV Surface", "GeometryNodeSampleUVSurface", "Sample surface at UV"),
            ("Separate Matrix", "FunctionNodeSeparateMatrix", "Separate matrix components"),
            ("Simulation Zone", "ZONE:GeometryNodeSimulationInput", "Simulation feedback loop (adds input and output)"),
            ("Sort Elements", "GeometryNodeSortElements", "Sort elements by attribute"),
            ("Store Named Attribute", "GeometryNodeStoreNamedAttribute", "Store field as named attribute"),
            ("Store Named Grid", "GeometryNodeStoreNamedGrid", "Store grid in volume"),
            ("String", "FunctionNodeInputString", "String value input"),
            ("String to Curves", "GeometryNodeStringToCurves", "Convert text to curves"),
            ("Switch", "GeometryNodeSwitch", "Switch between two inputs"),
            ("Tool Face Set", "GeometryNodeToolFaceSet", "Sculpt face set operations"),
            ("Tool Selection", "GeometryNodeToolSelection", "Tool selection state"),
            ("Tool Set Face Set", "GeometryNodeToolSetFaceSet", "Set sculpt face set"),
            ("Tool Set Selection", "GeometryNodeToolSetSelection", "Set tool selection"),
            ("Vector Math", "ShaderNodeVectorMath", "Vector math operations"),
        ],
        "Color": [
            ("Combine Color", "FunctionNodeCombineColor", "Combine color channels"),
            ("RGB Curves", "ShaderNodeRGBCurve", "RGB curve adjustment"),
            ("Separate Color", "FunctionNodeSeparateColor", "Separate color channels"),
        ],
        "Vector": [
            ("Combine XYZ", "ShaderNodeCombineXYZ", "Combine XYZ components"),
            ("Separate XYZ", "ShaderNodeSeparateXYZ", "Separate XYZ components"),
            ("Vector Curves", "ShaderNodeVectorCurve", "Vector curve adjustment"),
        ],
        "Group": [
            ("Group Input", "NodeGroupInput", "Group input sockets"),
            ("Group Output", "NodeGroupOutput", "Group output sockets"),
        ],
        "Layout": [
            ("Frame", "NodeFrame", "Visual grouping frame"),
            ("Reroute", "NodeReroute", "Connection reroute"),
        ],
        "Simulation": [
            ("Simulation Input", "GeometryNodeSimulationInput", "Simulation state input"),
            ("Simulation Output", "GeometryNodeSimulationOutput", "Simulation state output"),
        ],
    },
    
    "CompositorNodeTree": {
        "Input": [
            ("Bokeh Image", "CompositorNodeBokehImage", "Bokeh shape for blur"),
            ("Image", "CompositorNodeImage", "Image input from file"),
            ("Mask", "CompositorNodeMask", "Mask datablock input"),
            ("Movie Clip", "CompositorNodeMovieClip", "Movie clip input"),
            ("Render Layers", "CompositorNodeRLayers", "Scene render layer input"),
            ("RGB", "CompositorNodeRGB", "RGB color input"),
            ("Scene Time", "CompositorNodeTime", "Scene time/frame input"),
            ("Texture", "CompositorNodeTexture", "Texture datablock input"),
            ("Time", "CompositorNodeTime", "Time curve input"),
            ("Track Position", "CompositorNodeTrackPos", "Motion tracking position"),
            ("Value", "CompositorNodeValue", "Numeric value input"),
        ],
        "Output": [
            ("Composite", "CompositorNodeComposite", "Final composite output"),
            ("File Output", "CompositorNodeOutputFile", "Write image to file"),
        ],
        "Color": [
            ("Alpha Over", "CompositorNodeAlphaOver", "Layer image over another"),
            ("Bright/Contrast", "CompositorNodeBrightContrast", "Brightness and contrast"),
            ("Color Balance", "CompositorNodeColorBalance", "Color temperature/tint"),
            ("Color Correction", "CompositorNodeColorCorrection", "Advanced color correction"),
            ("Exposure", "CompositorNodeExposure", "Exposure adjustment"),
            ("Gamma", "CompositorNodeGamma", "Gamma correction"),
            ("Hue Correct", "CompositorNodeHueCorrect", "Hue correction curves"),
            ("Hue/Saturation/Value", "CompositorNodeHueSat", "Adjust HSV values"),
            ("Invert Color", "CompositorNodeInvert", "Invert color channels"),
            ("Mix Color", "CompositorNodeMixRGB", "Mix two colors"),
            ("RGB Curves", "CompositorNodeCurveRGB", "RGB curve adjustment"),
            ("Tonemap", "CompositorNodeTonemap", "HDR tone mapping"),
            ("Z Combine", "CompositorNodeZcombine", "Combine images by depth"),
        ],
        "Converter": [
            ("Color Ramp", "CompositorNodeValToRGB", "Map value to color"),
            ("Combine Color", "CompositorNodeCombineColor", "Combine color channels"),
            ("ID Mask", "CompositorNodeIDMask", "Extract object index mask"),
            ("Math", "CompositorNodeMath", "Math operations"),
            ("RGB to BW", "CompositorNodeRGBToBW", "Convert to grayscale"),
            ("Separate Color", "CompositorNodeSeparateColor", "Separate color channels"),
            ("Set Alpha", "CompositorNodeSetAlpha", "Replace alpha channel"),
            ("Switch View", "CompositorNodeSwitchView", "Switch stereo views"),
        ],
        "Filter": [
            ("Antialiasing", "CompositorNodeAntiAliasing", "SMAA antialiasing"),
            ("Bilateral Blur", "CompositorNodeBilateralblur", "Edge-preserving blur"),
            ("Blur", "CompositorNodeBlur", "Gaussian blur filter"),
            ("Bokeh Blur", "CompositorNodeBokehBlur", "Bokeh-style blur"),
            ("Defocus", "CompositorNodeDefocus", "Depth-based defocus"),
            ("Denoise", "CompositorNodeDenoise", "AI-based denoising"),
            ("Despeckle", "CompositorNodeDespeckle", "Remove noise specks"),
            ("Dilate/Erode", "CompositorNodeDilateErode", "Expand or shrink mask"),
            ("Directional Blur", "CompositorNodeDBlur", "Motion-style blur"),
            ("Filter", "CompositorNodeFilter", "Edge detection filter"),
            ("Glare", "CompositorNodeGlare", "Bloom and glare effects"),
            ("Inpaint", "CompositorNodeInpaint", "Fill missing areas"),
            ("Kuwahara", "CompositorNodeKuwahara", "Kuwahara filter"),
            ("Pixelate", "CompositorNodePixelate", "Pixelate image"),
            ("Posterize", "CompositorNodePosterize", "Reduce color depth"),
            ("Sun Beams", "CompositorNodeSunBeams", "God rays effect"),
            ("Vector Blur", "CompositorNodeVecBlur", "Motion vector blur"),
        ],
        "Vector": [
            ("Map UV", "CompositorNodeMapUV", "Map image to UV"),
            ("Map Value", "CompositorNodeMapValue", "Remap value range"),
            ("Normal", "CompositorNodeNormal", "Normal direction"),
            ("Normalize", "CompositorNodeNormalize", "Normalize value range"),
        ],
        "Matte": [
            ("Box Mask", "CompositorNodeBoxMask", "Rectangular mask"),
            ("Channel Key", "CompositorNodeChannelMatte", "Key by color channel"),
            ("Chroma Key", "CompositorNodeChromaMatte", "Chroma key (green screen)"),
            ("Color Key", "CompositorNodeColorMatte", "Key by color similarity"),
            ("Color Spill", "CompositorNodeColorSpill", "Remove color spill"),
            ("Cryptomatte", "CompositorNodeCryptomatte", "Cryptomatte ID keying"),
            ("Cryptomatte V2", "CompositorNodeCryptomatteV2", "Cryptomatte V2 keying"),
            ("Difference Key", "CompositorNodeDiffMatte", "Key by difference"),
            ("Distance Key", "CompositorNodeDistanceMatte", "Key by color distance"),
            ("Double Edge Mask", "CompositorNodeDoubleEdgeMask", "Refine edge mask"),
            ("Ellipse Mask", "CompositorNodeEllipseMask", "Elliptical mask"),
            ("Keying", "CompositorNodeKeying", "Advanced keying"),
            ("Keying Screen", "CompositorNodeKeyingScreen", "Keying screen builder"),
            ("Luminance Key", "CompositorNodeLumaMatte", "Key by luminance"),
        ],
        "Distort": [
            ("Corner Pin", "CompositorNodeCornerPin", "Four-point distortion"),
            ("Crop", "CompositorNodeCrop", "Crop image area"),
            ("Displace", "CompositorNodeDisplace", "Vector displacement"),
            ("Flip", "CompositorNodeFlip", "Flip image horizontally/vertically"),
            ("Lens Distortion", "CompositorNodeLensdist", "Lens distortion correction"),
            ("Map UV", "CompositorNodeMapUV", "UV coordinate mapping"),
            ("Movie Distortion", "CompositorNodeMovieDistortion", "Movie clip distortion"),
            ("Plane Track Deform", "CompositorNodePlaneTrackDeform", "Plane tracking warp"),
            ("Rotate", "CompositorNodeRotate", "Rotate image"),
            ("Scale", "CompositorNodeScale", "Scale image size"),
            ("Stabilize 2D", "CompositorNodeStabilize", "Motion stabilization"),
            ("Transform", "CompositorNodeTransform", "Transform image"),
            ("Translate", "CompositorNodeTranslate", "Translate position"),
        ],
        "Group": [
            ("Group Input", "NodeGroupInput", "Group input sockets"),
            ("Group Output", "NodeGroupOutput", "Group output sockets"),
        ],
        "Layout": [
            ("Frame", "NodeFrame", "Visual grouping frame"),
            ("Reroute", "NodeReroute", "Connection reroute"),
            ("Switch", "CompositorNodeSwitch", "Switch between inputs"),
        ],
    },
}

TOOLTIPS = {bl: tip for tree in NODE_CATALOG.values() for cats in tree.values() for _, bl, tip in cats}

# --------------------------------------------------------------------------
# CUSTOM NODE STORAGE
# --------------------------------------------------------------------------

def get_custom_nodes_path():
    config_dir = bpy.utils.user_resource('CONFIG', path="noderack")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "custom_nodes.json")

def load_custom_nodes():
    path = get_custom_nodes_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                if 'favorites' not in data:
                    data['favorites'] = {}
                return data
        except:
            return {'favorites': {}}
    return {'favorites': {}}

def save_custom_nodes(custom_nodes):
    path = get_custom_nodes_path()
    with open(path, 'w') as f:
        json.dump(custom_nodes, f, indent=2)

# --------------------------------------------------------------------------
# Property Groups
# --------------------------------------------------------------------------

class NR_Node(PropertyGroup):
    name: StringProperty()
    bl_idname: StringProperty()

class NR_Category(PropertyGroup):
    name: StringProperty()
    expanded: BoolProperty(default=True)
    nodes: CollectionProperty(type=NR_Node)

class NR_CustomNode(PropertyGroup):
    name: StringProperty()
    node_data: StringProperty()

def update_search(self, context):
    if context.area:
        context.area.tag_redraw()

class NR_Props(PropertyGroup):
    search: StringProperty(
        name="Search",
        description="Search nodes (live filtering)",
        default="",
        update=update_search,
        options={'TEXTEDIT_UPDATE'}
    )
    categories: CollectionProperty(type=NR_Category)
    custom_nodes: CollectionProperty(type=NR_CustomNode)
    custom_expanded: BoolProperty(name="Custom Nodes", default=True)
    favorites_expanded: BoolProperty(name="Favorite Nodes", default=True)
    last_tree_type: StringProperty(default="")

# --------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------

class NR_OT_add_node(Operator):
    bl_idname = "noderack.add_node"
    bl_label = "Add Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    bl_idname_str: StringProperty()
    tooltip: StringProperty(default="Add node to editor")
    
    @classmethod
    def description(cls, context, properties):
        return getattr(properties, "tooltip", "Add node to editor")
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'NODE_EDITOR' and space.edit_tree
    
    def invoke(self, context, event):
        override_context = context.copy()
        override_context['window'] = context.window
        override_context['screen'] = context.screen
        override_context['area'] = context.area
        override_context['region'] = context.region
        override_context['space_data'] = context.space_data
        
        try:
            with context.temp_override(**override_context):
                bpy.ops.node.add_node('INVOKE_DEFAULT', type=self.bl_idname_str, use_transform=True)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add node: {str(e)}")
            return {'CANCELLED'}
    
    def execute(self, context):
        return self.invoke(context, None)

class NR_OT_add_simulation_zone(Operator):
    bl_idname = "noderack.add_simulation_zone"
    bl_label = "Add Simulation Zone"
    bl_description = "Add Simulation Input and Output nodes as a pair"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'NODE_EDITOR' and space.edit_tree
    
    def invoke(self, context, event):
        space = context.space_data
        tree = space.edit_tree
        
        for node in tree.nodes:
            node.select = False
        
        try:
            bpy.ops.node.add_simulation_zone('EXEC_DEFAULT')
            
            override_context = context.copy()
            override_context['window'] = context.window
            override_context['screen'] = context.screen
            override_context['area'] = context.area
            override_context['region'] = context.region
            override_context['space_data'] = context.space_data
            
            try:
                with context.temp_override(**override_context):
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
            except:
                pass
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add simulation zone: {str(e)}")
            return {'CANCELLED'}

class NR_OT_add_repeat_zone(Operator):
    bl_idname = "noderack.add_repeat_zone"
    bl_label = "Add Repeat Zone"
    bl_description = "Add Repeat Input and Output nodes as a pair"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space and space.type == 'NODE_EDITOR' and space.edit_tree
    
    def invoke(self, context, event):
        space = context.space_data
        tree = space.edit_tree
        
        for node in tree.nodes:
            node.select = False
        
        try:
            bpy.ops.node.add_repeat_zone('EXEC_DEFAULT')
        
            override_context = context.copy()
            override_context['window'] = context.window
            override_context['screen'] = context.screen
            override_context['area'] = context.area
            override_context['region'] = context.region
            override_context['space_data'] = context.space_data
            
            try:
                with context.temp_override(**override_context):
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
            except:
                pass
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add repeat zone: {str(e)}")
            return {'CANCELLED'}

class NR_OT_clear_search(Operator):
    bl_idname = "noderack.clear_search"
    bl_label = "Clear Search"
    bl_description = "Clear search field"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        context.window_manager.nr_props.search = ""
        return {'FINISHED'}

class NR_OT_collapse_all(Operator):
    bl_idname = "noderack.collapse_all"
    bl_label = "Collapse All Categories"
    bl_description = "Collapse all node categories"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        props = context.window_manager.nr_props
        for cat in props.categories:
            cat.expanded = False
        return {'FINISHED'}

class NR_OT_expand_all(Operator):
    bl_idname = "noderack.expand_all"
    bl_label = "Expand All Categories"
    bl_description = "Expand all node categories"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        props = context.window_manager.nr_props
        for cat in props.categories:
            cat.expanded = True
        return {'FINISHED'}

class NR_OT_toggle_favorite(Operator):
    bl_idname = "noderack.toggle_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Add or remove this node from favorites"
    bl_options = {'INTERNAL'}
    
    node_bl_idname: StringProperty()
    node_name: StringProperty()
    
    def execute(self, context):
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR':
            return {'CANCELLED'}
        
        tree_type = space.tree_type
        
        data = load_custom_nodes()
        favorites = data.get('favorites', {})
        tree_favorites = favorites.get(tree_type, [])
        
        favorite_entry = {
            'bl_idname': self.node_bl_idname,
            'name': self.node_name
        }
        
        is_favorited = False
        for fav in tree_favorites:
            if fav['bl_idname'] == self.node_bl_idname:
                is_favorited = True
                break
        
        if is_favorited:
            tree_favorites = [f for f in tree_favorites if f['bl_idname'] != self.node_bl_idname]
        else:
            tree_favorites.append(favorite_entry)
        
        favorites[tree_type] = tree_favorites
        data['favorites'] = favorites
        save_custom_nodes(data)
        
        return {'FINISHED'}

class NR_OT_save_nodes(Operator):
    bl_idname = "noderack.save_nodes"
    bl_label = "Save Selected Nodes"
    bl_description = "Save selected nodes as custom preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name for this node preset",
        default="My Preset"
    )
    
    preset_description: StringProperty(
        name="Description",
        description="Optional description for this preset (shows on hover)",
        default=""
    )
    
    preset_color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Optional color for this preset",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.608, 0.608, 0.608)
    )
    
    use_color: BoolProperty(
        name="Use Custom Color",
        description="Enable custom color for this preset",
        default=False
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")
        layout.prop(self, "preset_description")
        layout.separator()
        layout.prop(self, "use_color")
        if self.use_color:
            layout.prop(self, "preset_color")
    
    def execute(self, context):
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR' or not space.edit_tree:
            self.report({'ERROR'}, "No active node tree")
            return {'CANCELLED'}
        
        tree = space.edit_tree
        selected_nodes = [n for n in tree.nodes if n.select]
        
        if not selected_nodes:
            self.report({'ERROR'}, "No nodes selected")
            return {'CANCELLED'}
        
        node_data = {
            'tree_type': space.tree_type,
            'nodes': [],
            'links': [],
            'description': self.preset_description,
        }
        
        if self.use_color:
            node_data['color'] = list(self.preset_color)
        
        min_x = min(n.location.x for n in selected_nodes)
        max_x = max(n.location.x for n in selected_nodes)
        min_y = min(n.location.y for n in selected_nodes)
        max_y = max(n.location.y for n in selected_nodes)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        node_index_map = {node: idx for idx, node in enumerate(selected_nodes)}
        
        for node in selected_nodes:
            node_info = {
                'type': node.bl_idname,
                'location': (node.location.x - center_x, node.location.y - center_y),
                'width': node.width,
                'height': node.height,
                'label': node.label,
                'name': node.name,
            }
            node_data['nodes'].append(node_info)
        
        for link in tree.links:
            if link.from_node in selected_nodes and link.to_node in selected_nodes:
                link_info = {
                    'from_node': node_index_map[link.from_node],
                    'from_socket': link.from_socket.name,
                    'to_node': node_index_map[link.to_node],
                    'to_socket': link.to_socket.name,
                }
                node_data['links'].append(link_info)
        
        custom_nodes = load_custom_nodes()
        tree_customs = custom_nodes.get(space.tree_type, {})
        tree_customs[self.preset_name] = node_data
        custom_nodes[space.tree_type] = tree_customs
        save_custom_nodes(custom_nodes)
        
        self.report({'INFO'}, f"Saved preset: {self.preset_name}")
        return {'FINISHED'}

class NR_OT_load_preset(Operator):
    bl_idname = "noderack.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: StringProperty()
    preset_description: StringProperty(default="Load custom node preset")

    @classmethod
    def description(cls, context, properties):
        desc = getattr(properties, "preset_description", "")
        return desc if desc else "Load custom node preset"

    def invoke(self, context, event):
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR' or not space.edit_tree:
            self.report({'ERROR'}, "No active node tree")
            return {'CANCELLED'}

        tree = space.edit_tree
        custom_nodes = load_custom_nodes()
        tree_customs = custom_nodes.get(space.tree_type, {})

        if self.preset_name not in tree_customs:
            self.report({'ERROR'}, "Preset not found")
            return {'CANCELLED'}

        preset = tree_customs[self.preset_name]

        node_region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
        if not node_region:
            self.report({'ERROR'}, "Could not find node editor region")
            return {'CANCELLED'}

        cursor_x, cursor_y = space.cursor_location
        for node in tree.nodes:
            node.select = False

        created_nodes = []
        for node_info in preset.get('nodes', []):
            try:
                node = tree.nodes.new(type=node_info['type'])
                node.location = (
                    cursor_x + node_info['location'][0],
                    cursor_y + node_info['location'][1]
                )
                node.width = node_info.get('width', 140)
                if node_info.get('label'):
                    node.label = node_info['label']
                node.select = True
                created_nodes.append(node)
            except Exception as e:
                self.report({'WARNING'}, f"Could not create {node_info['type']}: {str(e)}")

        if 'links' in preset:
            for link_info in preset['links']:
                try:
                    from_node = created_nodes[link_info['from_node']]
                    to_node = created_nodes[link_info['to_node']]

                    from_socket = next((s for s in from_node.outputs if s.name == link_info['from_socket']), None)
                    to_socket = next((s for s in to_node.inputs if s.name == link_info['to_socket']), None)

                    if from_socket and to_socket:
                        tree.links.new(from_socket, to_socket)
                except Exception as e:
                    self.report({'WARNING'}, f"Could not restore link: {str(e)}")

        if created_nodes:
            tree.nodes.active = created_nodes[0]

            try:
                with bpy.context.temp_override(
                    window=context.window,
                    screen=context.screen,
                    area=context.area,
                    region=node_region,
                    space_data=context.space_data,
                ):
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
            except Exception:
                pass

            self.report({'INFO'}, f"Loaded preset: {self.preset_name}")

        return {'FINISHED'}

class NR_OT_delete_preset(Operator):
    bl_idname = "noderack.delete_preset"
    bl_label = "Delete Preset"
    bl_description = "Delete custom node preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty()
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR':
            return {'CANCELLED'}
        
        custom_nodes = load_custom_nodes()
        tree_customs = custom_nodes.get(space.tree_type, {})
        
        if self.preset_name in tree_customs:
            del tree_customs[self.preset_name]
            custom_nodes[space.tree_type] = tree_customs
            save_custom_nodes(custom_nodes)
            self.report({'INFO'}, f"Deleted preset: {self.preset_name}")
        
        return {'FINISHED'}

# --------------------------------------------------------------------------
# Category Builder
# --------------------------------------------------------------------------

def build_categories(context):
    props = context.window_manager.nr_props
    _node_color_cache.clear()
    props.categories.clear()
    
    space = context.space_data
    if not space or space.type != 'NODE_EDITOR':
        return
    
    tree_id = space.tree_type
    catalog = NODE_CATALOG.get(tree_id, {})
    
    for cname, items in catalog.items():
        cat = props.categories.add()
        cat.name = cname
        for label, blid, _tip in items:
            n = cat.nodes.add()
            n.name = label
            n.bl_idname = blid

def get_category_color(tree_type, category_name):
    return get_node_category_color(tree_type, category_name)

def is_node_favorited(tree_type, node_bl_idname):
    data = load_custom_nodes()
    favorites = data.get('favorites', {})
    tree_favorites = favorites.get(tree_type, [])
    
    for fav in tree_favorites:
        if fav['bl_idname'] == node_bl_idname:
            return True
    return False

def get_node_category(tree_type, node_bl_idname):
    catalog = NODE_CATALOG.get(tree_type, {})
    for category_name, nodes in catalog.items():
        for node_name, bl_idname, desc in nodes:
            if bl_idname == node_bl_idname:
                return category_name
    return None

# --------------------------------------------------------------------------
# Panel
# --------------------------------------------------------------------------

class NR_PT_browser(Panel):
    bl_label = "NodeRack"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "NodeRack"
    
    def draw(self, context):
        layout = self.layout
        props = context.window_manager.nr_props
        
        row = layout.row(align=True)
        row.prop(props, "search", text="", icon='VIEWZOOM')
        row.operator("noderack.collapse_all", text="", icon='TRIA_RIGHT')
        row.operator("noderack.expand_all", text="", icon='TRIA_DOWN')
        
        row = layout.row()
        row.operator("noderack.save_nodes", text="Save Selected Nodes", icon='FILE_TICK')
        
        layout.separator()
        
        space = context.space_data
        if not space or space.type != 'NODE_EDITOR':
            layout.label(text="No node editor active")
            return
        
        tree_id = space.tree_type
        if tree_id != props.last_tree_type:
            build_categories(context)
            props.last_tree_type = tree_id
        
        search = props.search.strip().lower()
        
        if not props.categories:
            layout.label(text="No nodes for this editor")
            return
        
        data = load_custom_nodes()
        favorites = data.get('favorites', {})
        tree_favorites = favorites.get(tree_id, [])
        
        if tree_favorites or not search:
            box = layout.box()
            row = box.row()
            row.prop(props, "favorites_expanded", text="", emboss=False,
                    icon='TRIA_DOWN' if props.favorites_expanded else 'TRIA_RIGHT')
            row.label(text="Favorites")
            header_color = (1.0, 0.8, 0.2, 1.0)
            row.template_node_socket(color=header_color)
            
            if props.favorites_expanded:
                if tree_favorites:
                    col = box.column(align=True)
                    for fav in sorted(tree_favorites, key=lambda x: x['name']):
                        if search and search not in fav['name'].lower():
                            continue
                        
                        node_bl_idname = fav['bl_idname']
                        node_name = fav['name']
                        
                        category = get_node_category(tree_id, node_bl_idname)
                        if category:
                            color = get_category_color(tree_id, category)
                        else:
                            color = (0.5, 0.5, 0.5, 1.0)
                        
                        is_zone = node_bl_idname.startswith("ZONE:")
                        if is_zone:
                            node_bl_idname = node_bl_idname[5:]
                        
                        row = col.row(align=True)
                        
                        indicator_col = row.column(align=True)
                        indicator_col.scale_x = 0.3
                        indicator_col.template_node_socket(color=color)
                        
                        if is_zone:
                            if "Simulation" in node_name:
                                op = row.operator("noderack.add_simulation_zone",
                                                text=node_name, icon='NODE')
                            elif "Repeat" in node_name:
                                op = row.operator("noderack.add_repeat_zone",
                                                text=node_name, icon='NODE')
                        else:
                            op = row.operator(NR_OT_add_node.bl_idname,
                                            text=node_name, icon='NODE')
                            op.bl_idname_str = fav['bl_idname']
                            op.tooltip = TOOLTIPS.get(fav['bl_idname'], "Add node to editor")
                        
                        op = row.operator("noderack.toggle_favorite", text="", icon='SOLO_ON')
                        op.node_bl_idname = fav['bl_idname']
                        op.node_name = fav['name']
                else:
                    box.label(text="No favorite nodes yet", icon='INFO')
        
        custom_nodes = load_custom_nodes()
        tree_customs = custom_nodes.get(tree_id, {})
        
        if tree_customs or not search:
            box = layout.box()
            row = box.row()
            row.prop(props, "custom_expanded", text="", emboss=False,
                    icon='TRIA_DOWN' if props.custom_expanded else 'TRIA_RIGHT')
            row.label(text="Custom Presets")
            color = (0.9, 0.6, 0.3, 1.0)
            row.template_node_socket(color=color)
            
            if props.custom_expanded:
                if tree_customs:
                    col = box.column(align=True)
                    for preset_name in sorted(tree_customs.keys()):
                        if search and search not in preset_name.lower():
                            continue
                        
                        preset_data = tree_customs[preset_name]
                        
                        if 'color' in preset_data:
                            preset_color = tuple(preset_data['color']) + (1.0,)
                        else:
                            preset_color = (0.6, 0.6, 0.6, 1.0)
                        
                        preset_desc = preset_data.get('description', '')
                        
                        row = col.row(align=True)
                        
                        indicator_col = row.column(align=True)
                        indicator_col.scale_x = 0.3
                        indicator_col.template_node_socket(color=preset_color)
                        
                        op = row.operator("noderack.load_preset", text=preset_name, 
                                       icon='PRESET')
                        op.preset_name = preset_name
                        op.preset_description = preset_desc
                        
                        row.operator("noderack.delete_preset", text="", 
                                   icon='X').preset_name = preset_name
                else:
                    box.label(text="No custom presets saved", icon='INFO')
            
            layout.separator()
        
        if search:
            found_any = False
            
            for cat in props.categories:
                color = get_category_color(tree_id, cat.name)
                
                for node in cat.nodes:
                    if search in node.name.lower():
                        found_any = True
                        
                        node_name = node.name
                        node_bl_idname = node.bl_idname
                        
                        is_zone = node_bl_idname.startswith("ZONE:")
                        if is_zone:
                            node_bl_idname = node_bl_idname[5:]
                        
                        row = layout.row(align=True)
                        
                        indicator_col = row.column(align=True)
                        indicator_col.scale_x = 0.3
                        indicator_col.template_node_socket(color=color)
                        
                        if is_zone:
                            if "Simulation" in node_name:
                                op = row.operator("noderack.add_simulation_zone",
                                                text=node_name, icon='NODE')
                            elif "Repeat" in node_name:
                                op = row.operator("noderack.add_repeat_zone",
                                                text=node_name, icon='NODE')
                        else:
                            op = row.operator(NR_OT_add_node.bl_idname,
                                            text=node_name, icon='NODE')
                            op.bl_idname_str = node_bl_idname
                            op.tooltip = TOOLTIPS.get(node_bl_idname, "Add node to editor")
                        
                        is_fav = is_node_favorited(tree_id, node.bl_idname)
                        op = row.operator("noderack.toggle_favorite", text="", 
                                        icon='SOLO_ON' if is_fav else 'SOLO_OFF')
                        op.node_bl_idname = node.bl_idname
                        op.node_name = node.name
            
            if not found_any:
                layout.label(text="No nodes found", icon='INFO')
        else:
            for cat in props.categories:
                color = get_category_color(tree_id, cat.name)
                
                head = layout.box()
                r = head.row()
                r.prop(cat, "expanded", text="", emboss=False,
                      icon='TRIA_DOWN' if cat.expanded else 'TRIA_RIGHT')
                r.label(text=cat.name)
                r.template_node_socket(color=color)
                
                if not cat.expanded:
                    continue
                
                for node in cat.nodes:
                    node_name = node.name
                    node_bl_idname = node.bl_idname
                    
                    is_zone = node_bl_idname.startswith("ZONE:")
                    if is_zone:
                        node_bl_idname = node_bl_idname[5:]
                    
                    row = layout.row(align=True)
                    
                    indicator_col = row.column(align=True)
                    indicator_col.scale_x = 0.3
                    indicator_col.template_node_socket(color=color)
                    
                    if is_zone:
                        if "Simulation" in node_name:
                            op = row.operator("noderack.add_simulation_zone",
                                            text=node_name, icon='NODE')
                        elif "Repeat" in node_name:
                            op = row.operator("noderack.add_repeat_zone",
                                            text=node_name, icon='NODE')
                    else:
                        op = row.operator(NR_OT_add_node.bl_idname,
                                        text=node_name, icon='NODE')
                        op.bl_idname_str = node_bl_idname
                        op.tooltip = TOOLTIPS.get(node_bl_idname, "Add node to editor")
                    
                    is_fav = is_node_favorited(tree_id, node.bl_idname)
                    op = row.operator("noderack.toggle_favorite", text="", 
                                    icon='SOLO_ON' if is_fav else 'SOLO_OFF')
                    op.node_bl_idname = node.bl_idname
                    op.node_name = node.name

# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------

classes = (
    NR_Node,
    NR_Category,
    NR_CustomNode,
    NR_Props,
    NR_OT_add_node,
    NR_OT_add_simulation_zone,
    NR_OT_add_repeat_zone,
    NR_OT_clear_search,
    NR_OT_collapse_all,
    NR_OT_expand_all,
    NR_OT_toggle_favorite,
    NR_OT_save_nodes,
    NR_OT_load_preset,
    NR_OT_delete_preset,
    NR_PT_browser,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.WindowManager.nr_props = PointerProperty(type=NR_Props)

def unregister():
    if hasattr(bpy.types.WindowManager, "nr_props"):
        del bpy.types.WindowManager.nr_props
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()