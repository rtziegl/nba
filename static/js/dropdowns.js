document.addEventListener('DOMContentLoaded', function () {
    const statDropdownItems = document.querySelectorAll('#statDropdownButton + .dropdown-menu .dropdown-item');
    statDropdownItems.forEach(item => {
        item.addEventListener('click', function () {
            const selectedValue = item.dataset.value;
            document.getElementById('statDropdownButton').textContent = selectedValue;
        });
    });

    const overUnderDropdownItems = document.querySelectorAll('#overUnderDropdownButton + .dropdown-menu .dropdown-item');
    overUnderDropdownItems.forEach(item => {
        item.addEventListener('click', function () {
            const selectedValue = item.dataset.value;
            document.getElementById('overUnderDropdownButton').textContent = selectedValue;
        });
    });
});