document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const propInput = document.getElementById('propInput');
    const statDropdownItems = document.querySelectorAll('#statDropdownButton + .dropdown-menu .dropdown-item');
    const overUnderDropdownItems = document.querySelectorAll('#overUnderDropdownButton + .dropdown-menu .dropdown-item');
    const submitButton = document.getElementById('submitButton');

    // Function to check if all fields are filled
    function checkFormValidity() {
        const searchValue = searchInput.value.trim();
        const propValue = propInput.value.trim();
        const isStatSelected = Array.from(statDropdownItems).some(item => item.classList.contains('active'));
        const isOverUnderSelected = Array.from(overUnderDropdownItems).some(item => item.classList.contains('active'));

        // Enable the submit button if all conditions are met
        if (searchValue !== '' && propValue !== '' && isStatSelected && isOverUnderSelected) {
            submitButton.disabled = false;
        } else {
            submitButton.disabled = true;
        }
    }

    // Add event listeners to the necessary elements
    searchInput.addEventListener('input', checkFormValidity);
    propInput.addEventListener('input', checkFormValidity);
    statDropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            // Toggle the active class when the item is clicked
            statDropdownItems.forEach(item => item.classList.remove('active'));
            this.classList.add('active');
            checkFormValidity();
        });
    });
    overUnderDropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            // Toggle the active class when the item is clicked
            overUnderDropdownItems.forEach(item => item.classList.remove('active'));
            this.classList.add('active');
            checkFormValidity();
        });
    });

    // Initial check on page load
    checkFormValidity();
});
