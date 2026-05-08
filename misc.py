from math import pi
from typing import Union, Type
###Complex Molecules - Test Code Including every type of building block 
#0 - Cylinder;          block = [0,lc,rc] Fix Length stuff  (lc = half length of cylender)
#1 - Sphere;            block = [1,rs] 
#2 - Ellipsoid;         block = [2,b,a]
#3 - Wedge;             block = [3,lw,r1,r2,phi] (lw = half length of cylender) (phi = radians)
#4 - Truncated Cone;    block = [4,lco,r1,r2] (loc = half length of cylender)

MAX_SIGNAL_RESOLUTION = 1_000_000

def Blockmaker(components):
    # Converts the components into a block
    block = []
    # All values are present and are valid.
    # Pore radius to compontent parameter comparison is done at *front end*

    # Check of all values are present and are valid
    for i, component in enumerate(components):
        componentShape = component.get("shape", None)
        if componentShape is None:
            return False, f"Shape of component {i+1} is missing"
        
        componentData = component.get("data", None)
        if componentData is None:
            return False, f"Data of component {i+1} is missing"

        if componentShape == "cylinder":
            try:
                cylinderLength = float(componentData['cylinderLength'])
                cylinderRadius = float(componentData['cylinderRadius'])
                if cylinderLength <= 0:
                    return False, f"Error in component {i+1}: Cylinder Length must be greater than 0"
                if cylinderRadius <= 0:
                    return False, f"Error in component {i+1}: Cylinder Radius must be greater than 0"
                cylinder = [0, cylinderLength/2, cylinderRadius]
                block.append(cylinder)
            except Exception as e:
                return False, f"Error in component {i+1}: {e}"
        elif componentShape == "wedge":
            try:
                wedgeLength = float(componentData['wedgeLength'])
                wedgeRadius1 = float(componentData['wedgeRadius1'])
                wedgeRadius2 = float(componentData['wedgeRadius2'])
                # ToDo: Check if angle is in radians | and restrict it to numpy range
                wedgeAngle = float(componentData['wedgeAngle'])
                if wedgeLength <= 0:
                    return False, f"Error in component {i+1}: Wedge Length must be greater than 0"
                if wedgeRadius1 <= 0 or wedgeRadius2 <= 0:
                    return False, f"Error in component {i+1}: Wedge radii must be greater than 0"
                wedge = [3, wedgeLength/2, wedgeRadius1, wedgeRadius2, wedgeAngle]
                block.append(wedge)
            except Exception as e:
                return False, f"Error in component {i+1}: {e}"
        elif componentShape == "sphere":
            try:
                sphereRadius = float(componentData['sphereRadius'])
                if sphereRadius <= 0:
                    return False, f"Error in component {i+1}: Sphere Radius must be greater than 0"
                sphere = [1, sphereRadius]
                block.append(sphere)
            except Exception as e:
                return False, f"Error in component {i+1}: {e}"
        elif componentShape == "cone":
            try:
                coneLength = float(componentData['coneLength'])
                coneRadius1 = float(componentData['coneRadius1'])
                coneRadius2 = float(componentData['coneRadius2'])
                if coneLength <= 0:
                    return False, f"Error in component {i+1}: Cone Length must be greater than 0"
                if coneRadius1 <= 0 or coneRadius2 <= 0:
                    return False, f"Error in component {i+1}: Cone radii must be greater than 0"
                if coneRadius1 == coneRadius2:
                    return False, f"Error in component {i+1}: Cone Radius 1 and Radius 2 cannot be the same"
                cone = [4, coneLength/2, coneRadius1, coneRadius2]
                block.append(cone)
            except Exception as e:
                return False, f"Error in component {i+1}: {e}"
        elif componentShape == "ellipsoid":
            try:
                ellipsoidAxisA = float(componentData['ellipsoidAxisA'])
                ellipsoidAxisB = float(componentData['ellipsoidAxisB'])
                if ellipsoidAxisA <= 0 or ellipsoidAxisB <= 0:
                    return False, f"Error in component {i+1}: Ellipsoid axes must be greater than 0"
                if ellipsoidAxisB <= ellipsoidAxisA:
                    return False, f"Error in component {i+1}: Ellipsoid Axis B must be greater than Axis A"
                ellipsoid = [2, ellipsoidAxisB, ellipsoidAxisA]
                block.append(ellipsoid)
            except Exception as e:
                return False, f"Error in component {i+1}: {e}"
        else:
            return False, f"Invalid shape in component {i+1}"
    return True, block

def BlockNormalizer(block, rp):
    # Normalize the dimensions of all shapes
    # rp is the pore radius

    n_block = []
    for component in block:
        shape = component[0]
        if shape == 0:
            # Cylinder
            n_block.append([shape, component[1]/rp, component[2]/rp])
        elif shape == 1:
            # Sphere
            n_block.append([shape, component[1]/rp])
        elif shape == 2:
            # Ellipsoid
            n_block.append([shape, component[1]/rp, component[2]/rp])
        elif shape == 3:
            # Wedge
            # ToDo: Check if angle is in radians | and restrict it to numpy range | and normalize angle by 2pi if needed
            n_block.append([shape, component[1]/rp, component[2]/rp, component[3]/rp, component[4]/(2*pi)])
        elif shape == 4:
            # Truncated Cone
            n_block.append([shape, component[1]/rp, component[2]/rp, component[3]/rp])
        else:
            raise ValueError(f"Invalid shape number: {shape}")
    return n_block

def _fieldValidator(field:str, fieldName:str, dt:Type=float, defaults:bool=True)->tuple[bool,float|str]:
    if field is None:
        return False, f"{fieldName} is missing"
    try:
        field = dt(field)
        if defaults:
            if field <= 0:
                return False, f"{fieldName} must be greater than 0"
    except:
        return False, f"{fieldName} is invalid"
    return True, field

def validate_and_sanitize_generate_signal_data(data: dict) -> tuple[bool, dict|str]:
    # Validate molecule components are present
    if data.get('components') is None:
        return False, "Molecule shapes are unavailable"
    
    # Validate poreDetails are present
    poreDetails = data.get('poreDetails',None)
    if poreDetails is None:
        return False, 'Pore details are missing'
    
    # pore type
    poreType = poreDetails.get('selectedPoreType',None)
    if poreType is None:
        return False, 'Pore Type is Missing'
    if poreType not in ['2dPore','CylindricalPore','ConicalPore','HyperbolicPore']:
        return False, f"{poreType} is invalid."

    # Resolution validation
    status, signalResolution = _fieldValidator(poreDetails.get("signalResolution"), "Signal Resolution", int)
    if not status:
        return False, "Signal Resolution is invalid or missing"
    if signalResolution > MAX_SIGNAL_RESOLUTION:
        return False, f"Signal Resolution must be <= {MAX_SIGNAL_RESOLUTION}"
    
    validatedData = {
        'poreType': poreType,
        'signalResolution': signalResolution
    }
    # components validation
    if data.get("components", None) is None:
        return False, "Components is missing"
    components = data["components"]
    if not isinstance(components, list):
        return False, "Components must be a list"
    if len(components) == 0:
        return False, "Components must have atleast one element"

    print(f"Debugging: {poreType}, {poreDetails}", flush=True)
    # Pore specific validation
    if poreType == '2dPore':
        # Nanopore radius validation
        status, nanoporeRadius = _fieldValidator(poreDetails.get("nanoporeRadius_2D"),"Nanopore Radius")
        if status is False:
            return False, "Nanopore Radius of 2D Pore is invalid or missing"
        validatedData["nanoporeRadius"] = nanoporeRadius
    elif poreType == 'CylindricalPore':
        status, nanoporeRadius_cylindrical = _fieldValidator(poreDetails.get('nanoporeRadius_cylindrical'),"Nanopore Radius")
        if status is False:
            return False, "Nanopore Radius of Cylindrical Pore is invalid or missing"
        status, nanoporeLength_cylindrical = _fieldValidator(poreDetails.get("nanoporeLength_cylindrical"),"Nanopore Length")
        if status is False:
            return False, "Nanopore Length of Cylindrical Pore is invalid or missing"
        validatedData['pore'] = [1,nanoporeLength_cylindrical,nanoporeRadius_cylindrical]
    elif poreType == 'ConicalPore':
        status, nanoporeRadius1_conical = _fieldValidator(poreDetails.get('nanoporeRadius1_conical'),"Nanopore Radius 1")
        if status is False:
            return False, "Nanopore Radius 1 of Conical Pore is invalid or missing"
        status, nanoporeRadius2_conical = _fieldValidator(poreDetails.get('nanoporeRadius2_conical'),"Nanopore Radius 2")
        if status is False:
            return False, "Nanopore Radius 2 of Conical Pore is invalid or missing"
        if nanoporeRadius1_conical == nanoporeRadius2_conical:
            return False, "Nanopore Radius 1 and 2 cannot be the same for a conical pore"
        status, nanoporeLength_conical = _fieldValidator(poreDetails.get("nanoporeLength_conical"),"Nanopore Length")
        if status is False:
            return False, "Nanopore Length of Conical Pore is invalid or missing"
        validatedData['pore'] = [2,nanoporeLength_conical,nanoporeRadius1_conical,nanoporeRadius2_conical]
    elif poreType == 'HyperbolicPore':
        status, nanoporeRadiusIn_hyperbolic = _fieldValidator(poreDetails.get('nanoporeRadiusIn_hyperbolic'),"Nanopore Radius In")
        if status is False:
            return False, "Nanopore Radius In of Hyperbolic Pore is invalid or missing"
        status, nanoporeRadiusOut_hyperbolic = _fieldValidator(poreDetails.get('nanoporeRadiusOut_hyperbolic'),"Nanopore Radius Out")
        if status is False:
            return False, "Nanopore Radius Out of Hyperbolic Pore is invalid or missing"
        if nanoporeRadiusOut_hyperbolic <= nanoporeRadiusIn_hyperbolic:
            return False, "Nanopore Radius Out must be greater than Radius In for a hyperbolic pore"
        status, nanoporeLength_hyperbolic = _fieldValidator(poreDetails.get("nanoporeLength_hyperbolic"),"Nanopore Length")
        if status is False:
            return False, "Nanopore Length of Hyperbolic Pore is invalid or missing"
        validatedData['pore'] = [3,nanoporeLength_hyperbolic,nanoporeRadiusIn_hyperbolic,nanoporeRadiusOut_hyperbolic]
    else:
        return False, f"{poreType} not made yet!"

    status, result = Blockmaker(components)
    if status is False:
        return False, f"Error in components: {result}"
    validatedData["components"] = result
    return True, validatedData