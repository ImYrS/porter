// Function - Stop All Interval
function stopAllInterval() {
    let intervalEndID = setInterval(() => {
    }, 1000);
    for (let i = 1; i <= intervalEndID; i++) {
        clearInterval(i);
    }
}

// Function - Auto Redirect
function autoRedirect(path, time = PAGE_REDIRECT_DELAY_TIME) {
    window.setTimeout(() => {
        location.href = path;
    }, time);
}

// Function - Back To Previous Page
function toPreviousPage() {
    if (history.length > 1) history.go(-1); else location.href = '/';
}

// Function - Is Empty Object
function isEmptyObject(variable) {
    for (let i in variable) {
        return false;
    }
    return true;
}

// Function - Sleep
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Function - Formatted Time
function formattedTime(time) {
    if (time) return dayjs(time).format('YYYY-MM-DD HH:mm:ss'); else return '-';
}

// Function - null or undefined or blank to '-':
function null2dash(variable, replace = '-') {
    if (variable === null || variable === undefined) return replace; else {
        if (typeof variable === 'string') if (variable.replaceAll('\n', '').replaceAll('\t', '').replaceAll(' ', '') === '') return replace;
        return variable;
    }
}

function XHRError(e) {
    if (e.responseJSON) {
        if (e.status === 401) {
            localStorage.clear();
            location.href = '/';
        }

        alert(e.responseJSON.message_human_readable);
    } else alert('连接后端失败');
}

function logOut() {
    localStorage.clear();
    location.href = '/';
}