// list all class, id
const allElements = document.querySelectorAll("*"), uniqueClasses = new Set(), uniqueIds = new Set(); allElements.forEach(element => { element.classList.forEach(cls => uniqueClasses.add(cls)); if (element.id) uniqueIds.add(element.id); }); console.log("Unique Classes:", Array.from(uniqueClasses).sort()); console.log("Unique IDs:", Array.from(uniqueIds).sort());


// download all class
const allElements = document.querySelectorAll("*"), uniqueClasses = new Set(); allElements.forEach(element => { element.classList.forEach(cls => uniqueClasses.add(cls)); }); const blob = new Blob([Array.from(uniqueClasses).sort().join("\n")], {type: "text/plain"}); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "unique-classes.txt"; document.body.appendChild(link); link.click(); document.body.removeChild(link);


// download all class all download
const allElements = document.querySelectorAll("*"),uniqueClasses = new Set(),uniqueIds = new Set();allElements.forEach(element => { element.classList.forEach(cls=>uniqueClasses.add(cls)); if (element.id) uniqueIds.add(element.id); });allElements.forEach(element => { element.classList.forEach(cls => uniqueClasses.add(cls)); });
download = (array, name)=>{const blob=new Blob([Array.from(array).sort().join("\n")], { type: "text/plain" });const link = document.createElement("a");link.href = URL.createObjectURL(blob);link.download = `${name}.txt`;document.body.appendChild(link);link.click();document.body.removeChild(link);}
download(uniqueClasses, 'all-class');download(uniqueIds, 'all-id'); 

// cloest 
const findClosest = (el, selector) => { while (el && el !== document) { if (el.matches(selector)) return el; el = el.parentElement; } return null; };

// cloest or sibling
function findClosestInParent(el, selector) {
    while (el) {
        const found = el.parentElement ? el.parentElement.querySelectorAll(selector) : [];
        if (found.length > 0) {
            return found[0];
        }
        el = el.parentElement;
    }
    return null;
}



const allElements = document.querySelectorAll("*");
const uniqueClasses = new Set();
const uniqueIds = new Set();
allElements.forEach(element => {
    element.classList.forEach(cls => {
        uniqueClasses.add(cls);
    });

    if (element.id) {
        uniqueIds.add(element.id);
    }
});
const uniqueClassesArray = Array.from(uniqueClasses);
const uniqueIdsArray = Array.from(uniqueIds);

search_key = "result";
uniqueClassesArray.forEach((css_class)=>{
	if(css_class.includes(search_key)){
		console.log(css_class)
	}
})