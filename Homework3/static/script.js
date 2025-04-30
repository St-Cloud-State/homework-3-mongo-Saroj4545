const submitApplication = () => {
    const name = document.getElementById('name').value;
    const address = document.getElementById('address').value;
    const zipcode = document.getElementById('zipcode').value;

    fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, address, zipcode })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Application Submitted:", data);
        document.getElementById('applicationResponse').innerText = data.application_id 
            ? `Application Submitted. ID: ${data.application_id}` 
            : 'Failed to submit application.';
    });
}

const checkStatus = () => {
    const appId = document.getElementById('statusAppId').value;
    fetch(`/api/status/${appId}`)
    .then(response => response.json())
    .then(data => {
        viewApplication(appId);
        document.getElementById('statusResponse').innerText = data.status 
            ? `Status: ${data.status}` 
            : 'Application not found.';
    });
}

const addNote = () => {
    const appId = document.getElementById('noteAppId').value;
    const note = document.getElementById('noteText').value;

    fetch(`/api/note/${appId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note })
    })
    .then(response => response.json())
    .then(data => {
        viewApplication(appId);
        document.getElementById('noteResponse').innerText = data.message 
            ? data.message 
            : 'Failed to add note.';
    });
}

const viewNotes = () => {
    const appId = document.getElementById('viewNotesAppId').value;
    fetch(`/api/notes/${appId}`)
    .then(response => response.json())
    .then(data => {
        viewApplication(appId);
        const notesDiv = document.getElementById('notesList');
        notesDiv.innerHTML = '';

        if (data.notes && data.notes.length > 0) {
            data.notes.forEach(note => {
                const p = document.createElement('p');
                p.innerText = note;
                notesDiv.appendChild(p);
            });
        } else {
            notesDiv.innerHTML = '<p>No notes found for this application.</p>';
        }
    });
}

function toggleStatusFields() {
    const status = document.getElementById('newStatus').value;
    document.getElementById('subphaseFields').style.display = (status === 'processing') ? 'block' : 'none';
    document.getElementById('loanTermField').style.display = (status === 'accepted') ? 'block' : 'none';
    document.getElementById('rejectionReasonField').style.display = (status === 'rejected') ? 'block' : 'none';
}

function handleStatusUpdate() {
    const appId = document.getElementById('updateAppId').value;
    const status = document.getElementById('newStatus').value;
    const subphase = document.getElementById('subphaseName').value;
    const subMsg = document.getElementById('subphaseMessage').value;
    const loanTerm = document.getElementById('loanTermText').value;
    const rejectionReason = document.getElementById('rejectionReason').value;

    fetch(`/api/status/${appId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('updateResponse').innerText = data.message || data.error;

        if (status === 'processing' && subphase && subMsg) {
            return fetch(`/api/subphase/${appId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subphase, message: subMsg })
            });
        } else if (status === 'accepted' && loanTerm) {
            return fetch(`/api/loan_terms/${appId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ term: loanTerm })
            });
        } else if (status === 'rejected' && rejectionReason) {
            return fetch(`/api/reject/${appId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: rejectionReason })
            });
        }
    })
    .then(response => response?.json?.())
    .then(data => {
        if (data?.message || data?.error) {
            document.getElementById('updateResponse').innerText += ` \u2192 ${data.message || data.error}`;
        }
        viewApplication(appId);
    })
    .catch(err => console.error("Status update error:", err));
}

const viewApplication = (appId = null) => {
    if (!appId) {
        appId = document.getElementById('statusAppId')?.value;
    }
    if (!appId) {
        console.warn("No application ID provided.");
        return;
    }

    fetch(`/api/application/${appId}`)
    .then(response => response.json())
    .then(data => {
        console.log("\ud83d\udcc4 Full Application Document:", data);
    })
    .catch(err => {
        console.error("Error viewing application:", err);
    });
}
