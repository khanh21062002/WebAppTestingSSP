// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        }, 4000);
    });
});
