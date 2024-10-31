function initKcForm() {
    var submitButtons = document.getElementsByClassName('btn-form-submit');
    for (var i = 0; i < submitButtons.length; i++) {
        submitButtons[i].addEventListener('click', function validateForm(e) {
            var form = e.target.closest('form');
            if (form != undefined && form != null) {
                form.classList.add('form-kc-submit');
            }
        });
    }
}
initKcForm();
