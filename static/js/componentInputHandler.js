// Index is set in Carousal card (data-index) 
// and as position in the card (data-carousal-card-position)

let _formPlaceholderId = 'inputFormPlaceHolder';
let formPlaceholder = document.getElementById(_formPlaceholderId);

// Copy form, for the selected component in "add section", and copy it to the form placeholder
// @component: string (ex: "cylinder")
function showForm(component){
    // Get the form from hidden components
    let form = document.getElementById(component.toLowerCase() + "Form").cloneNode(true);
    // Set the id of the form
    form.id = generateRandomId();
    // Set data component attribute
    form.dataset.component = component;
    // Reset the form
    form.reset();
    // prevent the form from submitting
    form.addEventListener('submit', function(e){
        e.preventDefault();
    });
    // delete the previous form
    formPlaceholder.innerHTML = "";
    // Append the new form
    formPlaceholder.appendChild(form);
}
// Show the form for the first component
showForm(document.getElementById('newComponentSelector').options[0].value.toLowerCase());


// Convert inputs from form to numbers
function sanitizeData(componentShapeName, formData){
    let sanitizedData = {};
    for(let key in formData){
        sanitizedData[key] = parseFloat(formData[key]) || 0;
        if (isNaN(sanitizedData[key])){
            sanitizedData[key] = 0;
        }
    }
    return sanitizedData;
}

// Minimum length of a cone to get a valid signal
function calculateConeMinLength(r1,r2,rp){
    let min_length = Math.abs(r1-r2)/Math.sqrt(((rp/Math.max(r1,r2))**2)-1);
    let precision = 10**3;
    return Math.ceil(min_length*precision)/precision;
}

// ToDo: Combine both validtion functions to build 2 new validation functions: validateWithSelf, ValidateWithRp
function validateComponentBeforeAddingToList(componentShapeName, formData){
    /**
     * Validates the form data before adding the component to the molecule list
     * @componentShapeName: string (ex: "cylinder")
     * @formData: object (ex: {radius: 1, height: 2})
     * @returns: [boolean, object] - [validation status, validated data or error messages]
     */
    // Check if the pore is valid
    if (!poreDetailsValid){
        return [false, ["Please enter valid nanopore details."]];
    }
    let validation = true;
    formData = sanitizeData(componentShapeName, formData);
    componentShapeName = componentShapeName.toLowerCase();
    console.log(componentShapeName,formData);
    let validationErrors = [];
    let nanoporeRadius = widthInNanoporeForThingsToPass;
    console.log(`Validating ${componentShapeName} with data:`, formData);
    // Validate the form data
    switch(componentShapeName){
        case "cylinder":
            if(formData.cylinderRadius <= 0){
                validation = false;
                validationErrors.push("Cylinder radius should be greater than 0.");
            }
            if(formData.cylinderLength <= 0){
                validation = false;
                validationErrors.push("Cylinder height should be greater than 0.");
            }
            if(formData.cylinderRadius >= nanoporeRadius){
                validation = false;
                validationErrors.push("Cylinder radius should be less than nanopore radius.");
            }
            break;
        case "cone":
            if(formData.coneRadius1 <= 0 || formData.coneRadius2 <= 0){
                validation = false;
                validationErrors.push("Cone radius should be greater than 0.");
            }
            if(formData.coneLength <= 0){
                validation = false;
                validationErrors.push("Cone length should be greater than 0.");
            }
            if(formData.coneRadius1 >= nanoporeRadius || formData.coneRadius2 >= nanoporeRadius){
                validation = false;
                validationErrors.push("Cone radius should be less than nanopore radius.");
            }
            if(formData.coneRadius1 === formData.coneRadius2){
                validation = false;
                validationErrors.push("Cone Radius 1 and Radius 2 cannot be the same.");
            }
            let coneMinLengthValue = calculateConeMinLength(formData.coneRadius1, formData.coneRadius2, nanoporeRadius);
            if(formData.coneLength < coneMinLengthValue && validation == true){
                validation = false;
                validationErrors.push(`For closed form solution, cone length should be greater than ${coneMinLengthValue} given the input radii.`)
            }
            break;
        case "sphere":
            if(formData.sphereRadius <= 0){
                validation = false;
                validationErrors.push("Sphere radius should be greater than 0.");
            }
            if(formData.sphereRadius >= nanoporeRadius){
                validation = false;
                validationErrors.push("Sphere radius should be less than nanopore radius.");
            }
            break;
        case "wedge":
            if(formData.wedgeAngle > 2*Math.PI || formData.wedgeAngle <= 0){
                validation = false;
                validationErrors.push("Wedge angle should be between 0 and 2π.");
            }
            if(formData.wedgeRadius1 <= 0 || formData.wedgeRadius2 <= 0){
                validation = false;
                validationErrors.push("Wedge radius should be greater than 0.");
            }
            if(formData.wedgeLength <= 0){
                validation = false;
                validationErrors.push("Wedge length should be greater than 0.");
            }
            if(formData.wedgeRadius1 >= nanoporeRadius){
                validation = false;
                validationErrors.push("Wedge Radius 1 should be smaller that nanopore radius.")
            }
            if(formData.wedgeRadius2 >= nanoporeRadius){
                validation = false;
                validationErrors.push("Wedge Radius 2 should be smaller that nanopore radius.")
            }
            break;
        case "ellipsoid":
            if(formData.ellipsoidAxisA <= 0 || formData.ellipsoidAxisB <= 0){
                validation = false;
                validationErrors.push("Ellipsoid axis should be greater than 0.");
            }
            if(formData.ellipsoidAxisB <= formData.ellipsoidAxisA){
                validation = false;
                validationErrors.push("Ellipsoid axis B should be greater than axis A.");
            }
            if(formData.ellipsoidAxisA >= nanoporeRadius){
                validation = false;
                validationErrors.push("Ellipsoid axis A should be less than nanopore radius.");
            }
            break;
        default:
            validation = false;
            validationErrors.push("Invalid component shape.");
    }


    // If validation failed, return the errors
    if(!validation){
        return [false, validationErrors];
    }
    // If validation passed, return the validated data
    return [true, formData];
}

// Add the component to the molecule list
function addComponentToList(componentShapeName, validatedData, componentId){
    let component = {
        id: componentId,
        shape: componentShapeName,
        data: validatedData
    };
    _ComponentList.push(component);
    console.log(_ComponentList);
}

// Add the component to the output carousal (at the end) based on the index in _ComponentList
// @index: int (ex: 0)
function addComponentToOutputCarousal(index){
    console.log(`Adding component to output carousal at index: ${index}`)
    // Note: Use it after calling addComponentToList
    let component = _ComponentList[index];
    console.log(component);
    let componentShapeName = component.shape;
    let componentData = component.data;
    let componentId = component.id;
    // Clone the carousal card
    let componentCard = document.getElementById("carousalCard").cloneNode(true);
    componentCard.removeAttribute("data-DONOT-DELETE");
    // Set the card id // Cannot use id attribute as it is being used by splide
    componentCard.dataset.id = `carousalCard_${componentId}`; // <<<<<<<< IMPORTANT >>>>>>>>
    componentCard.dataset.index = index;
    // Set the component image
    let imageLocation = `${import_listCard}${componentShapeName.toLowerCase()}.png`;
    componentCard.querySelector("[data-carousal-card-image]").src = imageLocation;
    // Set Card Title
    componentCard.querySelector("[data-carousal-card-title]").innerText = componentShapeName;
    // Set Card Position
    componentCard.querySelector("[data-carousal-card-position]").innerText = parseInt(index) + 1;
    // Set Card ID
    for(let key in componentData){
        let carousalCardBadge = document.querySelector("[data-carousal-card-badge]").cloneNode(true);
        carousalCardBadge.removeAttribute("data-carousal-card-badge");
        carousalCardBadge.removeAttribute("hidden");
        carousalCardBadge.innerText = `${key.replace(componentShapeName.toLowerCase(),"")}: ${componentData[key]}`;
        componentCard.querySelector("[data-carousal-card-badge-container]").appendChild(carousalCardBadge);
        componentCard.querySelector("[data-carousal-card-badge-container]").appendChild(document.createTextNode(" "));
    }
    // Show the card
    document.getElementById("carousal_list").appendChild(componentCard);
    initSplide();
}

// When Add button is clicked, get the form data and add the component to the molecule list
function addComponent(obj){
    loader.show();
    try{
        // Select the form on which the add button was clicked
        let component = formPlaceholder.querySelector("form");
        let formData = Object.fromEntries(new FormData(component));
        let componentShapeName = component.dataset.component;
        let componentId = component.id;
        // Validate the form data
        let [validation, validatedData] = validateComponentBeforeAddingToList(componentShapeName, formData);
        if(!validation){
            let errorText = "Unable to add component! Please fix the following errors:";
            for(let error of validatedData){
                errorText += `\n- ${error}`;
            }
            showToast(errorText, "danger");
        } else {
            // Add the component to the molecule list
            addComponentToList(componentShapeName, validatedData, componentId);
            // Add the component to the output carousal
            addComponentToOutputCarousal(index=_ComponentList.length-1);
            // Update the output figure
            addShapePlotly(index=_ComponentList.length-1);
            // Show toast
            showToast(`Component ${component.dataset.component} added!`);
            // Reset the form
            showForm(component.dataset.component);
        }
    } catch(e){
        console.log("Unable to add component!")
        console.error(e);
        console.trace();
        showToast("Error adding component!", "danger");
    } finally{
        loader.hide();
    }
}
