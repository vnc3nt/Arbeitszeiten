

document.addEventListener('DOMContentLoaded', loadButtons);
document.addEventListener('DOMContentLoaded', buttonSwipeUp);


document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    const saveBtn = document.getElementById('saveCategoryBtn');
    const cancelBtn = document.getElementById('cancelCategoryBtn');
    //const addModal = document.getElementById('addCategoryModal');

    const cancelEditBtn = document.getElementById('cancelEditCategoryBtn');
    const saveEditedBtn = document.getElementById('saveEditCategoryBtn');
    const deleteBtn = document.getElementById('deleteCategoryBtn');
    //const editModal = document.getElementById('addEditCategoryModal');
    
    if (saveBtn) {
        console.log('Save button found');
        saveBtn.addEventListener('click', saveCategory);
    } else {
        console.log('Save button not found');
    }
    
    if (cancelBtn) {
        console.log('Cancel button found');
        cancelBtn.addEventListener('click', hideAddCategoryModal);
    } else {
        console.log('Cancel button not found');
    }

    /*if (addModal) {
        console.log('addModal found');
        addModal.addEventListener('click', hideAddCategoryModal);
    } else {
        console.log('addModal not found');
    }
*/

    if (cancelEditBtn) {
        console.log('Cancel button found');
        cancelEditBtn.addEventListener('click', hideAddEditCategoryModal);
    } else {
        console.log('Save button not found');
    }

    /*if (editModal) {
        console.log('editModal found');
        editModal.addEventListener('click', hideAddEditCategoryModal);
    } else {
        console.log('editModal not found');
    }*/

    if (saveEditedBtn) {
        console.log('Save button found');
        saveEditedBtn.addEventListener('click', saveEditedCategory);
    } else {
        console.log('Save button not found');
    }
    
    if (deleteBtn) {
        console.log('Delete button found');
        deleteBtn.addEventListener('click', deleteCategory);
    } else {
        console.log('Cancel button not found');
    }

    for (let modal of document.getElementsByClassName("modal")) {
        let content = modal.querySelector(".modal-content");
        modal.addEventListener("click", (e) => {
            if (!e.target.classList.contains("modal")) return;

            if (content.offsetTop > e.y || content.offsetTop + content.offsetHeight < e.y || content.offsetLeft > e.x || content.offsetLeft + content.offsetWidth / 2 < e.x) {
                modal.style.display = "none";
            }
        }, true);
    }

    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            for (let modal of document.getElementsByClassName("modal")) {
                modal.style.display = "none";
            }
        }
    }, true);
});



let touchStartTime = null;
let touchStartX = null;
let touchStartY = null;
let touchX = 0;
let touchY = 0;
let moveDistance = 0;
let globalDatatransfer;
let lastTarget = null;
let allowDrop = false;
let draggedTouchNode = undefined;

const TOUCH_DRAG = "drag";
const TOUCH_NORMAL = "normal";
let touchSimulation = TOUCH_NORMAL;
let firstTarget = undefined;

const RIGHT_CLICK_TOUCH = 500;  // ms 
const DRAG_DISTANCE = 250;  // px²

let categories = [];

async function loadButtons() {
    let mainButtons = document.getElementById('main-buttons');
    mainButtons.innerHTML = ''; // Leeren des Inhalts

    try {
        let response = await fetch('/api/categories');
        categories = await response.json();

        // Sortieren der Kategorien nach ID
        categories.sort((a, b) => a.id - b.id);

        categories.forEach(category => {
            let button = document.createElement('button');
            button.classList.add('category-button'); // Allgemeine CSS-Klasse für Kategorie-Buttons
            button.classList.add(category.name.toLowerCase()); // CSS-Klasse basierend auf dem Kategorienamen
            button.innerText = category.name;

            // Stil für Hintergrundfarbe aus der Datenbank
            button.style.backgroundColor = lightenColor(category.color, -40);
            button.style.borderColor = lightenColor(category.color, 0);

            button.id = `btn-${category.name.toLowerCase()}`; // ID basierend auf dem Kategorienamen
            button.addEventListener('click', left);
            button.addEventListener('contextmenu', right);
            mainButtons.appendChild(button);
        });
        
        console.debug('Dynamisch generierte Buttons:', categories);
    } catch (error) {
        console.error('Fehler beim Laden der Kategorien:', error);
    }

    // Hinzufügen des '+' Buttons am Ende
    let addButton = document.createElement('button');
    addButton.classList.add('category-button', 'add');
    addButton.innerHTML = '<img src="static/img/icons/96x96-add.png" alt="+">';

    const rootStyles = getComputedStyle(document.documentElement);
    const buttonColor = rootStyles.getPropertyValue('--selected-color').trim();


    addButton.style.backgroundColor = lightenColor(buttonColor, -40);
    addButton.style.borderColor = lightenColor(buttonColor, 0);

    addButton.id = 'btn-add';
    addButton.addEventListener('click', showAddCategoryModal);
    mainButtons.appendChild(addButton);
}

window.addEventListener("touchstart", (e) => {
    touchX = e.touches[0].clientX;
    touchY = e.touches[0].clientY;
    touchStartTime = Date.now();
    firstTarget = document.elementFromPoint(touchX, touchY);

    if (e.target.className.split(' ')[0] === "category-button") {
        // Setze einen Timer, um die right() Funktion nach RIGHT_CLICK_TOUCH Millisekunden auszuführen
        longPressTimeout = setTimeout(() => {
            let actualTarget = document.elementFromPoint(touchX, touchY);
            if (actualTarget === firstTarget) { // block clicks when it has been swiped
                console.debug("yesyesyes");
                e.preventDefault();
                right(e);
            }
        }, RIGHT_CLICK_TOUCH);
    }

    // Funktion zum Animieren des Profilmenüs
    checkToHideProfile(e);

    buttonSwipeUp(e);
});


window.addEventListener("touchmove", (e) => {
    touchX = e.touches[0].clientX;
    touchY = e.touches[0].clientY;
    if (e.target != null) {
        if (e.target.className.split(' ')[0] === "category-button"){
            if (e.touches.length >= 2) { 
                touchSimulation = TOUCH_NORMAL;
                return;
            }
            if (touchSimulation === TOUCH_NORMAL) {
                let moveX = touchStartX - e.touches[0].clientX;
                let moveY = touchStartY - e.touches[0].clientY;
                moveDistance = moveX * moveX + moveY * moveY;
                if (moveDistance >= DRAG_DISTANCE) {
                    clearTimeout(longPressTimeout);
                    let draggedTouchNode = findNextDraggable(e.target);
                    if (draggedTouchNode) {
                        globalDatatransfer = new DataTransfer();
                        globalDatatransfer.dropEffect = "move";
                        globalDatatransfer.effectAllowed = "move";

                        console.log(globalDatatransfer);
                        draggedTouchNode.dispatchEvent(new DragEvent("dragstart", {bubble: true, dataTransfer: globalDatatransfer}));
                        touchSimulation = TOUCH_DRAG;
                        lastTarget = actualTarget;
                        lastTarget.dispatchEvent(new DragEvent("dragenter", {bubbles: true, dataTransfer: globalDatatransfer}));
                    }
                }
            }
            else if (touchSimulation === TOUCH_DRAG) {
                // TODO dragenter/-leave
                let prevDOver = actualTarget.dispatchEvent(new DragEvent("dragover", {bubbles: true, dataTransfer: globalDatatransfer, cancelable: true}));
                allowDrop = !prevDOver;
                if (actualTarget != lastTarget) {
                    lastTarget.dispatchEvent(new DragEvent("dragleave", {bubbles: true, dataTransfer: globalDatatransfer, cancelable: true}));
                    lastTarget = actualTarget;
                    actualTarget.dispatchEvent(new DragEvent("dragenter", {bubbles: true, dataTransfer: globalDatatransfer, cancelable: true}));
                }
            }
        }
    }
});

window.addEventListener("touchend", (e) => {
    touchX = e.changedTouches[0].clientX;
    touchY = e.changedTouches[0].clientY;
    let actualTarget = document.elementFromPoint(touchX, touchY);
    //console.debug(actualTarget.className);

    clearTimeout(longPressTimeout);

    if (e.target != null) {
        if (e.target.className.split(' ')[0] === "category-button"){
            console.log("touch end diff:", Date.now() - touchStartTime);
            if (!touchStartTime || e.touches.length >= 2) {
                touchStartTime = null;
                return;
            }

            let diff = Date.now() - touchStartTime;  // ms 
            //console.debug("end touch target", e.target);
            
            touchSimulation = TOUCH_NORMAL;
            if (actualTarget === firstTarget) { // block clicks when it has been swiped
                if (diff >= RIGHT_CLICK_TOUCH && touchSimulation === TOUCH_NORMAL) {
                    console.debug("yesyesyes");
                    e.preventDefault(); 
                    right(e);
                }
            }
            touchStartTime = null;
        }
    }
});

window.addEventListener("touchcancel", (e) => {
    clearTimeout(longPressTimeout);
    console.debug("touch cancel");
    if (touchSimulation == 0) {}
    touchStartTime = null;
    touchSimulation = TOUCH_NORMAL;
    moveDistance = 0;
    globalDatatransfer = null;
    draggedTouchNode = undefined;
});

async function left(e) {
    let buttonName = e.target.innerHTML;  // Name des Buttons/der Kategorie, z.B. "Gewicht"
    console.debug("BBB: " + buttonName);
    console.debug(categories);
    let category = categories.find(categ => categ.name === buttonName);
    if (!category) {
        console.error('Kategorie nicht gefunden für Button:', buttonName);
        return;
    }

    let unit = category.unit;
    let userInput = parseFloat(window.prompt(`${buttonName} in ${unit}:`).replace(',', '.'));
    if (!userInput) {
        console.debug("Keine Benutzereingabe");
        return;
    }

    if (userInput < 0) {
        console.debug("negative Eingabe");
        return;
    }

    let data = await fetch("/api/data",  {
        method: "POST",
        body: JSON.stringify({
            category: buttonName,  // buttonName wird als Kategorie verwendet
            data: userInput,
            user: getUserId()
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
    .then((response) => response.json())
    .catch((error) => console.error('Fehler beim Speichern der Daten:', error));
    
    await drawChart();
}

async function right(e) { //TODO edit old data ->
    //alert("right clicked!");
    e.preventDefault(); //kein kontextmenü
    let buttonName = e.target.innerHTML;  // Name des Buttons/der Kategorie, z.B. "Gewicht"
    console.debug("BBB: " + buttonName);
    console.debug(categories);
    category = categories.find(categ => categ.name === buttonName);
    if (!category) {
        console.error('Kategorie nicht gefunden für Button:', buttonName);
        return;
    }
    
    editCategory(category);
    

}

function checkToHideProfile(e) {
    const profileMenu = document.querySelector("#profile-menu");
    const profileMenuButton = document.querySelector("details#profile-menu-btn");
    let startY = e.touches[0].clientY;
    let originalY = 0;

    profileMenu.addEventListener("touchstart", (event) => {
        startY = event.touches[0].clientY;
        originalY = profileMenu.getBoundingClientRect().top;
    });

    profileMenu.addEventListener("touchmove", (event) => {
        const deltaY = event.touches[0].clientY - startY;
        if(deltaY > 0){
            profileMenu.style.transform = `translateY(${deltaY}px)`;
        }
        else {
            profileMenu.style.transform = `translateY(${deltaY/10}px)`;
        }
    });

    profileMenu.addEventListener("touchend", () => {
        // Prüfe, ob der Bereich überschritten wurde
        const threshold = 100;
        if (profileMenu.getBoundingClientRect().top - originalY > threshold) {

            profileMenu.style.transform = "translateY(100%)"; //nach unten fliegen

            if (profileMenuButton.open) {
                profileMenuButton.open = false;
            }
            profileMenu.style.transform = "translateY(0%)";
        } else {
            // Springe zurück zur Ausgangsposition
            profileMenu.style.transition = "transform 0.1s ease";
            profileMenu.style.transform = `translateY(${originalY}px)`;
        }
    });
}

function buttonSwipeUp() {
    const buttonMenu = document.querySelector(".button-menu");
    let startY, startHeight, isSwipeValid = false;
    const minHeight = 20; // Minimale Höhe in vh
    const maxHeight = 60; // Maximale Höhe in vh

    function vh(v) {
        return (v * window.innerHeight) / 100;
    }

    function setHeight(height) {
        buttonMenu.style.height = `${height}vh`;
    }

    function elasticEffect(height) {
        const factor = 0.5;
        
        if (height > maxHeight) {
            const overshoot = height - maxHeight;
            return maxHeight + Math.log1p(overshoot * factor) / factor;
        } else if (height < minHeight) {
            const undershoot = minHeight - height;
            return minHeight - Math.log1p(undershoot * factor) / factor;
        }
        
        return height;
    }

    function animateToHeight(from, to, duration = 300) {
        const startTime = performance.now();
        
        function animate(currentTime) {
            const elapsedTime = currentTime - startTime;
            if (elapsedTime > duration) {
                setHeight(to);
                return;
            }

            const progress = elapsedTime / duration;
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            const currentHeight = from + (to - from) * easeProgress;
            
            const elasticHeight = elasticEffect(currentHeight);
            setHeight(elasticHeight);

            requestAnimationFrame(animate);
        }

        requestAnimationFrame(animate);
    }

    function isMenuFullyExpanded() {
        return (buttonMenu.offsetHeight / window.innerHeight) * 100 >= maxHeight;
    }

    function isMenuAtTop() {
        return buttonMenu.scrollTop === 0;
    }

    buttonMenu.addEventListener("touchstart", (e) => {
        startY = e.touches[0].clientY;
        const currentHeight = (buttonMenu.offsetHeight / window.innerHeight) * 100;
        startHeight = currentHeight > (minHeight + maxHeight) / 2 ? maxHeight : minHeight;
        isSwipeValid = !isMenuFullyExpanded();
    });

    buttonMenu.addEventListener("touchmove", (e) => {


        

        const currentY = e.touches[0].clientY;
        const deltaY = startY - currentY;
        let newHeight = startHeight + (deltaY / window.innerHeight) * 100;


        if (!isSwipeValid) {
            console.debug(isMenuAtTop());
            isSwipeValid= (isMenuFullyExpanded() && isMenuAtTop() && newHeight <= startHeight);
        }

        if (!isSwipeValid) return;
        e.preventDefault();

        newHeight = elasticEffect(newHeight);
        setHeight(newHeight);
    });

    buttonMenu.addEventListener("touchend", () => {
        if (!isSwipeValid) return;

        const currentHeight = (buttonMenu.offsetHeight / window.innerHeight) * 100;
        const targetHeight = currentHeight > (minHeight + maxHeight) / 2 ? maxHeight : minHeight;

        animateToHeight(currentHeight, targetHeight);
    });
}


function expandButtonsDesktop(e) {
    const buttonMenu = document.getElementsByClassName("button-menu")[0];
    let startY =  buttonMenu.getBoundingClientRect().top;

    console.debug("algoo: " + startY);

    if (startY > 500) {
        buttonMenu.style.height = '80vh';
        e.target.style.transform = 'rotate(-180deg)';
    }
    else {
        buttonMenu.style.height = '20vh';
        e.target.style.transform = 'rotate(0deg)';
    }
}


function lightenColor(color, percent) {
    // Farbe in RGB-Werte aufteilen
    let r = parseInt(color.substring(1, 3), 16);
    let g = parseInt(color.substring(3, 5), 16);
    let b = parseInt(color.substring(5, 7), 16);

    // Helligkeit erhöhen
    r = Math.floor(r * (1 + percent / 100));
    g = Math.floor(g * (1 + percent / 100));
    b = Math.floor(b * (1 + percent / 100));

    // Grenzwerte sicherstellen (0 bis 255)
    r = Math.min(r, 255);
    g = Math.min(g, 255);
    b = Math.min(b, 255);

    // RGB-Werte zu HEX umwandeln
    let hex = `#${(r).toString(16).padStart(2, '0')}${(g).toString(16).padStart(2, '0')}${(b).toString(16).padStart(2, '0')}`;
    return hex;
}




function showAddCategoryModal() {
    console.log('showAddCategoryModal was called');
    // Clear input fields
    document.getElementById('categoryName').value = '';
    document.getElementById('categoryUnit').value = '';
    document.getElementById('categoryColor').value = '#991199';
    document.getElementById('addCategoryModal').style.display = 'block';
}

function hideAddCategoryModal() {
    console.log('hideAddCategoryModal was called');
    const modal = document.getElementById('addCategoryModal');
    if (modal) {
        console.log('Modal found, hiding it');
        modal.style.display = 'none';
    } else {
        console.log('Modal not found');
    }
}

async function saveCategory() {
    const name = document.getElementById('categoryName').value;
    const unit = document.getElementById('categoryUnit').value;
    const color = document.getElementById('categoryColor').value;

    if (!name || !unit || !color) {
        alert('Bitte füllen Sie alle Felder aus.');
        return;
    }

    else if (name.includes(" ")) {
        alert('Bitte nutzen Sie keine Leerzeichen im Namen.');
        return;
    }

    else if (unit.includes(" ")) {
        alert('Bitte nutzen Sie keine Leerzeichen in der Einheit.');
        return;
    }

    try {
        const response = await fetch('/api/categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, color, unit }),
        });
        console.debug(response);
        if (response.ok) {
            let result = await response.json();
            hideAddCategoryModal();
            await loadButtons(); // Reload buttons after adding a new category
        } 
        else if (response.status === 403) {
            alert("Kategorie existiert bereits!");
        }
        else {
            throw new Error('Fehler beim Hinzufügen der Kategorie');
        }
    } catch (error) {
        console.error('Fehler:', error);
        alert('Es gab einen Fehler beim Hinzufügen der Kategorie.');
    }
}


function editCategory(category) {
    console.debug("adfdss",category);
    document.getElementById("addEditCategoryModalTitle").innerHTML = category.name + " bearbeiten";
    document.getElementById("editCategoryName").value = category.name;
    document.getElementById("editCategoryUnit").value = category.unit;
    document.getElementById("editCategoryColor").value = category.color;
    showAddEditCategoryModal();
}

function showAddEditCategoryModal() {
    console.log('showAddEditCategoryModal was called');
    document.getElementById('addEditCategoryModal').style.display = 'block';
}

function hideAddEditCategoryModal() {

    console.log('hideAddEditCategoryModal was called');
    const modal = document.getElementById('addEditCategoryModal');
    if (modal) {
        console.log('Modal found, hiding it');
        modal.style.display = 'none';
    } else {
        console.log('Modal not found');
    }
    
}

async function saveEditedCategory() {
    const name = document.getElementById('editCategoryName').value;
    const unit = document.getElementById('editCategoryUnit').value;
    const color = document.getElementById('editCategoryColor').value;
    const originalCategory = categories.find(categ => categ.name === document.getElementById("addEditCategoryModalTitle").innerHTML.replace(" bearbeiten", "").trim());
    const id = originalCategory.id;

    if (!name || !unit || !color) {
        alert('Bitte füllen Sie alle Felder aus.');
        return;
    }

    else if (name.includes(" ")) {
        alert('Bitte nutzen Sie keine Leerzeichen im Namen.');
        return;
    }

    else if (unit.includes(" ")) {
        alert('Bitte nutzen Sie keine Leerzeichen in der Einheit.');
        return;
    }

    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, color, unit }),
        });

        console.debug(response);

        if (response.ok) {
            const result = await response.json();
            hideAddEditCategoryModal();
            await loadButtons(); // Reload buttons after editing a category
            await drawChart();
        } else {
            throw new Error('Fehler beim Aktualisieren der Kategorie');
        }
    } catch (error) {
        console.error('Fehler:', error);
        alert('Es gab einen Fehler beim Bearbeiten der Kategorie.');
    }   
}

async function deleteCategory() {
    const originalCategory = categories.find(categ => categ.name === document.getElementById("addEditCategoryModalTitle").innerHTML.replace(" bearbeiten", "").trim());
    const id = originalCategory.id;

    if (!confirm('Sind Sie sicher, dass Sie die Kategorie samt aller Datenpunkte unwiderruflich löschen möchten?')) {
        return;
    }

    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            await loadButtons(); // Reload buttons after deleting a category
            await drawChart(); // Reload chart after deleting all categorydata
            console.log('Kategorie und alle Daten erfolgreich gelöscht.');
            hideAddEditCategoryModal();
            
        } else {
            throw new Error('Fehler beim Löschen der Kategorie');
        }
    } catch (error) {
        console.error('Fehler:', error);
        alert('Es gab einen Fehler beim Löschen der Kategorie.');
    }
}
