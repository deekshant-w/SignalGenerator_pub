// Carousel settings
var _splide;
function initSplide(){
    _splide = new Splide('.splide',{
        perMove: 2,
        gap: '1rem',
        omitEnd: true,
        autoWidth: true,
        padding: '4rem',
        pagination: false,
        cover: true,
        drag:false
    }).mount();
}

// Initialize tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

// Dark Mode Toggle
document.querySelector('#advanced').addEventListener('click', function() {
    document.body.dataset.bsTheme = document.body.dataset.bsTheme === 'dark' ? 'light' : 'dark';
});

// onfocusout -> validate input | negative numbers are not allowed
function positiveDecimalInputValidate(e){
    if(e.value==""){
        e.value = "";
        return
    } 
    const newVal = Math.abs(e.value);
    if(newVal != e.value){
        alert("Please enter a positive number. Updating value to " + newVal + ".");
        e.value = newVal;
    }
}

// onkeypress -> validate input | remove bad characters for non negative numbers validation
function badCharForNumberInputValidate(event){
    const badKeys = ['-', '+', 'e', 'E', ',']
    if(badKeys.includes(event.key)){
        event.preventDefault();
    }
}

// Show Component Image on Selector Panel
function showComponentImage(component) {
    // component: string (ex: "cylinder")
    let image = document.getElementById('componentShapeImage');
    image.src = `${import_newCard}${component}.png`;
}
showComponentImage(document.getElementById('newComponentSelector').options[0].value.toLowerCase());

// Add new component selector -> onChange (Triggered when a new component is selected in the dropdown | Changes image and form)
document.getElementById('newComponentSelector').addEventListener('change', function(event) {
    let component = event.target.value.toLowerCase();
    console.log(component);
    showComponentImage(component);
    showForm(component);
});

// Random ID Generator
function generateRandomId(size=10){
    let chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let randomId = '';
    for (let i = 0; i < size; i++){
        randomId += chars[Math.floor(Math.random() * chars.length)];
    }
    return randomId;
}

// Toast
const toastBootstrap = bootstrap.Toast.getOrCreateInstance(document.getElementById('ReusableToast'))
function showToast(message, type='success'){
    let messageBox = document.getElementById('ReusableToastMessage');
    let toastBox = document.getElementById('ReusableToast');
    // remove all classes that start with 'text-bg-' and add the new class 'text-bg-<type>'
    toastBox.className = toastBox.className.replace(/(^|\b)text-bg-\S+/g, '');
    toastBox.classList.add(`text-bg-${type}`);
    messageBox.innerText = message;
    toastBootstrap.show();
}

// Resize shape image div based on row height and refresh on window resize
// NOT IN USE
function resizeOutputDiv(){
    try{
        document.getElementById('drawBoxDiv').style.height = "0px";
        let rowHeight = document.getElementById('leftPanel').offsetHeight;
        document.getElementById('drawBoxDiv').style.height = `${rowHeight}px`;
    } catch (e) {
        console.debug("Error resizing output div.");
        console.debug(e);
    }
}
// resizeOutputDiv();
// window.addEventListener('resize', resizeOutputDiv);
// new ResizeObserver(resizeOutputDiv).observe(document.getElementById('leftPanel'));

function resizeShapesPlotlyDiv(){
    try{
        Plotly.Plots.resize(document.getElementById(SHAPES_DIV_ID));
    } catch (e) {
        console.debug("Error reploting shapes plotly div.");
        console.error(e);
    }
}
window.addEventListener('resize', resizeShapesPlotlyDiv);
new ResizeObserver(resizeShapesPlotlyDiv).observe(document.getElementById('leftPanel'));

function downloadMolecule(){
    let copiedData = structuredClone(_ComponentList);
    // remove the id field
    for(let i=0; i<copiedData.length; i++){
        delete copiedData[i].id;
    }
    let data = jsyaml.dump(copiedData);
    let blob = new Blob([data], {type: 'text/yaml'});
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    let nanoporeRadius = "";
    let signalResolution = ""; 
    try{
        nanoporeRadius = document.getElementById("nanoporeRadius").value.replace(".","-");
        signalResolution = document.getElementById("signalResolution").value.replace(".","-");
    } catch (e) {
        console.error(e);
    }
    // a.download = `molecule_${generateRandomId()}.yaml`;
    a.download = `molecule_${generateRandomId()}_${nanoporeRadius}_${signalResolution}_${Date.now()}.yaml`;
    a.click();
    window.URL.revokeObjectURL(url);
}

function uploadMolecule(){
    document.getElementById("uploadFileDummy").click();
}

function parseFileName(fileName){}

function displayUploadedMolecule(data, fileName){
    // Clear the existing data
    _ComponentList = [];
    // Clear the carousal
    document.getElementById("carousal_list").innerHTML = "";
    // Add the uploaded data to the component list
    for(let component of data){
        addComponentToList(component.shape, component.data, generateRandomId());
        addComponentToOutputCarousal(index=_ComponentList.length-1);
    }
    // Update output figure
    remakeShapesPlotly(false);
    // Use the file name to set pore size and resolution (optionally)
    parseFileName(fileName);
}

document.getElementById('uploadFileDummy').addEventListener('change', function(event) {
    // print current time stamp
    console.log(Date.now());
    const file = event.target.files[0];
    console.log(file);
    console.log(file.name);
    if (!file) {
        // No file selected, toast error
        showToast("No file selected!", "warning");
        return;
    }
    const reader = new FileReader();
    reader.onload = function(event) {
        const contents = event.target.result;
        loader.show();
        try {
            let data = jsyaml.load(contents);
            displayUploadedMolecule(data, file.name);
            console.log(data);
            showToast("File read successfully.");
            // Hide bottom navbar
            // let offcanvas = new bootstrap.Offcanvas(document.getElementById("offcanvasRight1"))
            // console.log(offcanvas);
            // offcanvas.hide();
        } catch (e) {
            console.error(e);
            showToast("Unable to read file.", "danger");
        } finally {
            // clear file input
            document.getElementById('uploadFileDummy').value = '';
            loader.hide();
        }
    };
    reader.readAsText(file);
});