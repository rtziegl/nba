// resetForm.js
document.addEventListener('DOMContentLoaded', function() {
    const resetButton = document.getElementById('resetButton');
    const statDropdownItems = document.querySelectorAll('.stat-dropdown-item');
    const overUnderDropdownItems = document.querySelectorAll('.over-under-dropdown-item');
    resetButton.addEventListener('click', function () {
        // Reset the form fields
        document.getElementById('myForm').reset();
        document.getElementById('statDropdownButton').textContent = 'Select a Stat';
        document.getElementById('overUnderDropdownButton').textContent = 'Over/Under';
        statDropdownItems.forEach(item => item.classList.remove('active'));
        overUnderDropdownItems.forEach(item => item.classList.remove('active'));
        submitButton.disabled = true;
    });
});