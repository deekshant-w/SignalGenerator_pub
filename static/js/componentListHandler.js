var _ComponentList = [];
let editModalId = "editModal";
let editModalComponent = document.getElementById(editModalId);
var editModal = new bootstrap.Modal(editModalComponent);

function findParentCard(element){
    return element.closest("[data-parent-stop-search]");
}

function editButtonHandler(e){
    let loc = import_listCard;
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    let componentData = _ComponentList[index];
    document.getElementById("editModalTitle").innerHTML = componentData.shape;
    document.getElementById("editModalPosition").innerHTML = index+1;
    document.getElementById("editModalImage").src = `${loc}${componentData.shape.toLowerCase()}.png`;
    document.getElementById("editModalFormContainer").innerHTML = "";
    // Clone the form
    let newForm = document.getElementById(`${componentData.shape}Form`).cloneNode(true);
    // Clean the form
    newForm.reset();
    // Set the values
    for(let key in componentData.data){
        let input = newForm.querySelector(`[name=${key}]`);
        input.value = componentData.data[key];
    }
    // Append the form
    document.getElementById("editModalFormContainer").appendChild(newForm);
    // Set the index
    editModalComponent.dataset.index = index;
    // Show the modal
    editModal.show();
}

// Save the changes made in the edit modal
function editModalSubmitHandler(){
    // Get the index of the component in _ComponentList
    let index = editModalComponent.dataset.index;
    index = parseInt(index);
    // Get the form data
    let form = editModalComponent.querySelector("form");
    // Convert the form data to dictionary
    let formData = Object.fromEntries(new FormData(form).entries());
    // Validate the form data
    let componentShapeName = _ComponentList[index].shape.toLowerCase();
    let [validation, validatedData] = validateComponentBeforeAddingToList(componentShapeName, formData);
    if(!validation){
        // Show error message toast
        let errorText = "Unable to edit component! Please fix the following errors:";
        for(let error of validatedData){
            errorText += `\n- ${error}`;
        }
        showToast(errorText, "danger");
        return;
    }
    formData = validatedData;
    // Update the component data
    _ComponentList[index].data = formData;
    // Update the carousal card
    let id = `carousalCard_${_ComponentList[index].id}`;
    let carousalCard = document.querySelector(`[data-id=${id}]`);
    let badgeContainer = carousalCard.querySelector("[data-carousal-card-badge-container]");
    // Clear the badge container
    badgeContainer.innerHTML = "";
    for(let key in formData){
        // Create a new badge
        let carousalCardBadge = document.querySelector("[data-carousal-card-badge]").cloneNode(true);
        // Remove attributes of the cloned badge
        carousalCardBadge.removeAttribute("data-carousal-card-badge");
        carousalCardBadge.removeAttribute("hidden");
        // Set the text of the badge
        carousalCardBadge.innerText = `${key.replace(componentShapeName,"")}: ${formData[key]}`;
        // Append the badge to the badge container
        badgeContainer.appendChild(carousalCardBadge);
        // Add a space
        badgeContainer.appendChild(document.createTextNode(" "));
    }
    // Remake plotly shapes
    remakeShapesPlotly();

    console.log(_ComponentList);
    editModal.hide();
    // Show success message toast
    showToast("Component edited successfully");
}

// Update position and index of the carousal cards
function updateIndexAndPosition(){
    for(let i=0; i<_ComponentList.length; i++){
        let id = `carousalCard_${_ComponentList[i].id}`;
        let carousalCard = document.querySelector(`[data-id=${id}]`);
        carousalCard.dataset.index = i;
        carousalCard.querySelector("[data-carousal-card-position]").innerText = i+1;
    }
}

// Handle the left arrow click
function leftArrowHandler(e){
    // Get the parent card
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Swap the components
    if(index>0){
        // Get the current card and the previous card
        let currentCard = parent;
        let previousCard = currentCard.previousElementSibling;
        // Swap the cards
        previousCard.before(currentCard);
        // Get the list elements
        let currentComponent = structuredClone(_ComponentList[index]);
        let previousComponent = structuredClone(_ComponentList[index-1]);
        // Swap the components
        _ComponentList[index] = previousComponent;
        _ComponentList[index-1] = currentComponent;
        // Update the index and position of the carousal cards
        updateIndexAndPosition();
        console.log(_ComponentList);
        // Show success message toast
        showToast("Component moved LEFT successfully");
        // Remake plotly shapes
        remakeShapesPlotly();
    } else {
        // Show error message toast
        showToast("Unable to move component to LEFT", "warning");
    }
}

// Handle the right arrow click
function rightArrowHandler(e){
    // Get the parent card
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Swap the components
    if(index<_ComponentList.length-1){
        // Get the current card and the next card
        let currentCard = parent;
        let nextCard = currentCard.nextElementSibling;
        // Swap the cards
        nextCard.after(currentCard);
        // Get the list elements
        let currentComponent = structuredClone(_ComponentList[index]);
        let nextComponent = structuredClone(_ComponentList[index+1]);
        // Swap the components
        _ComponentList[index] = nextComponent;
        _ComponentList[index+1] = currentComponent;
        // Update the index and position of the carousal cards
        updateIndexAndPosition();
        console.log(_ComponentList);
        // Show success message toast
        showToast("Component moved RIGHT successfully");
        // Remake plotly shapes
        remakeShapesPlotly();
    } else {
        // Show error message toast
        showToast("Unable to move component to RIGHT", "warning");
    }
}

// Handle the delete button click
// @e : delete element on which the click event was triggered
function deleteButtonHandler(e){
    // Get the parent card
    let parent = findParentCard(e);
    // if parent has data-DONOT-DELETE attribute, do not delete
    if(parent.hasAttribute("data-DONOT-DELETE")){
        return;
    }
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Remove the component from the list
    let deletedComponent = _ComponentList.splice(index, 1);
    // Deleted Card
    let deletedCard = parent.cloneNode(true);
    // Update stack with both the component and the card
    _UndoStack.push([index, deletedComponent[0], deletedCard]);
    // Remove the card from the carousal
    parent.remove();
    // Update the index and position of the carousal cards
    updateIndexAndPosition();
    // Remake plotly shapes
    remakeShapesPlotly();
    // Show success message toast
    showToast("Component deleted successfully. Press Ctrl+Shift+Z to undo.");
}

var _UndoStack = [];
// Undo the last delete operation
function undoHandler(){
    if(_UndoStack.length==0){
        showToast("Nothing to undo!", "warning");
        return;
    }
    let [index, component, card] = _UndoStack.pop();
    // Add the component back to the list
    _ComponentList.splice(index, 0, component);
    // Add the card back to the carousal
    let parent = document.getElementById("carousal_list");
    // Add the card to the index in parent
    parent.insertBefore(card, parent.children[index]);
    // Update the index and position of the carousal cards
    updateIndexAndPosition();
    // Remake plotly shapes
    remakeShapesPlotly();
    // Show success message toast
    showToast("Undo successful");
}

// Set the event listener for the ctrl+shift+z key press
document.addEventListener("keydown", function(e){
    // if(e.ctrlKey && e.key=="z"){
    if(e.ctrlKey && e.shiftKey && (e.key=="z" || e.key=="Z")){
        undoHandler();
    }
});

// Clear Molecule Manually
function _clearMolecule(){
    _ComponentList = [];
    document.getElementById("carousal_list").innerHTML = "";
    _UndoStack = [];
    console.log(_ComponentList);
    // Show success message toast
    showToast("Molecule cleared successfully");
}

// Clear Molecule by page reload
function _clearMolecule(){
    location.reload();
}


// Clearn Molecule by pressing all delete buttons
function clearMolecule(){
    let deleteButtons = document.querySelectorAll(".deleteCardBigButtonBox");
    for(let button of deleteButtons){
        button.click();
    }
    // Show success message toast
    showToast("Molecule cleared successfully. Press Ctrl+Shift+Z to undo individual deletions.");
}

// Copy Handler
function copyHandler(e){
    // Get the parent card
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Get the component data
    let componentData = _ComponentList[index];
    // Copy list element
    let copiedElement = structuredClone(componentData);
    // Give new ID to the copied element
    copiedElement.id = generateRandomId();
    // Copy Carousal Card
    let copiedCard = parent.cloneNode(true);
    // Update the ID
    copiedCard.dataset.id = `carousalCard_${copiedElement.id}`;
    return [copiedElement, copiedCard];
}

// Handle copy here button click
function copyHereButtonHandler(e){
    let [copiedElement, copiedCard] = copyHandler(e);
    // Get the parent card
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Update index of copied card
    copiedCard.dataset.index = index+1;
    // Update position of copied card
    copiedCard.querySelector("[data-carousal-card-position]").innerText = index+2;
    // Add the component to the list
    _ComponentList.splice(index+1, 0, copiedElement);
    // Add the card to the carousal
    parent.after(copiedCard);
    // Update the index and position of the carousal cards
    updateIndexAndPosition();
    // Re-initialize the carousal
    initSplide();
    // Remake plotly shapes
    remakeShapesPlotly();
    // Show success message toast
    showToast("Component copied INPLACE successfully");
}

// Handle copy to end button click
function copyToEndButtonHandler(e){
    let [copiedElement, copiedCard] = copyHandler(e);
    // Get the parent card
    let parent = findParentCard(e);
    // Index of the component in the list
    let index = parseInt(parent.dataset.index);
    // Update index of copied card
    copiedCard.dataset.index = _ComponentList.length;
    // Update position of copied card
    copiedCard.querySelector("[data-carousal-card-position]").innerText = _ComponentList.length+1;
    // Add the component to the list
    _ComponentList.push(copiedElement);
    // Add the card to the end of the carousal
    parent.parentElement.appendChild(copiedCard);
    // No need to update the index and position of the carousal cards as the card is added at the end
    // Re-initialize the carousal
    initSplide();
    // Remake plotly shapes
    remakeShapesPlotly();
    // Show success message toast
    showToast("Component copied to END successfully");
}

// Remake the carousal and update the output figure based on _ComponentList
function remakeCarousal(){
    // show loader
    loader.show();
    try{
        // Clear the carousal
        document.getElementById("carousal_list").innerHTML = "";
        // Add the uploaded data to the component list
        for(let i=0; i<_ComponentList.length; i++){
            addComponentToOutputCarousal(index=i);
        }
        // Update output figure
        // updateOutputFigure();
    } catch(e){
        console.error(e);
        showToast("Unable to remake carousal", "danger");
    } finally{
        // hide loader
        loader.hide();
    }
}

function remakeMoleculeEverywhere(){
    remakeCarousal();
    remakeShapesPlotly();
    showToast("Molecule remade successfully");
}