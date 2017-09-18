
// When the user clicks on the button, open the modal 
openDialog = function(id) {
    var modal = document.getElementById(id);
    modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
closeDialog = function(id) {
    var modal = document.getElementById(id);
    modal.style.display = "none";
}
